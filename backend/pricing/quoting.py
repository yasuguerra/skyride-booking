"""
Quoting Engine for Charter Aviation System
Calculates pricing based on PriceBook, applies surcharges, overrides, taxes, and service fees
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import os
from database import database
import json
import logging

logger = logging.getLogger(__name__)

class PricingEngine:
    """Core pricing engine for charter quotes"""
    
    def __init__(self):
        self.service_fee_percentage = float(os.environ.get('SERVICE_FEE_PERCENTAGE', 5.0))
    
    async def calculate_quote(
        self, 
        listing_id: str,
        passengers: int = 1,
        departure_date: Optional[datetime] = None,
        return_date: Optional[datetime] = None,
        trip_type: str = 'ONE_WAY'
    ) -> Dict:
        """
        Calculate a complete quote with all pricing components
        
        Args:
            listing_id: ID of the listing to quote
            passengers: Number of passengers
            departure_date: Departure datetime
            return_date: Return datetime (for round trips)
            trip_type: 'ONE_WAY' or 'ROUND_TRIP'
            
        Returns:
            Dict with pricing breakdown
        """
        
        # Get listing details with route and aircraft info
        listing_query = """
        SELECT l.*, r.origin_id, r.destination_id, r.typical_duration_min,
               a.type as aircraft_type, a.operator_id,
               o.name as operator_name
        FROM listings l
        LEFT JOIN routes r ON l.route_id = r.id
        LEFT JOIN aircraft a ON l.aircraft_id = a.id
        LEFT JOIN operators o ON a.operator_id = o.id
        WHERE l.id = :listing_id AND l.status = 'ACTIVE'
        """
        
        listing = await database.fetch_one(listing_query, {"listing_id": listing_id})
        
        if not listing:
            raise ValueError(f"Active listing not found: {listing_id}")
        
        if not listing['origin_id'] or not listing['destination_id']:
            raise ValueError(f"Listing {listing_id} does not have a complete route")
        
        # Calculate base price from PriceBook
        base_price = await self._get_base_price(
            origin_id=listing['origin_id'],
            destination_id=listing['destination_id'],
            aircraft_type=listing['aircraft_type'],
            operator_id=listing['operator_id'],
            departure_date=departure_date
        )
        
        if base_price is None:
            raise ValueError(f"No pricing found for route {listing['origin_id']} -> {listing['destination_id']} with aircraft type {listing['aircraft_type']}")
        
        # Apply passenger multiplier if needed
        passenger_adjusted_price = base_price
        
        # Calculate surcharges
        surcharges = await self._calculate_surcharges(
            base_price=passenger_adjusted_price,
            aircraft_type=listing['aircraft_type'],
            operator_id=listing['operator_id'],
            passengers=passengers,
            departure_date=departure_date
        )
        
        # Apply any overrides
        override_amount = await self._check_overrides(
            listing_id=listing_id,
            operator_id=listing['operator_id'],
            departure_date=departure_date
        )
        
        # Calculate subtotal before taxes
        subtotal = passenger_adjusted_price + surcharges + override_amount
        
        # Calculate taxes (e.g., ITBMS in Panama)
        taxes = await self._calculate_taxes(
            subtotal=subtotal,
            country='PA',  # Panama
            applies_to_base=True,
            applies_to_surcharges=True
        )
        
        # Calculate total before service fee
        total_before_service_fee = subtotal + taxes
        
        # Calculate service fee
        service_fee = total_before_service_fee * (self.service_fee_percentage / 100)
        
        # Final total
        total_price = total_before_service_fee + service_fee
        
        # Handle round trip
        if trip_type == 'ROUND_TRIP':
            # For round trip, we typically apply a discount or use different pricing
            # For now, we'll simply double the one-way price with a small discount
            round_trip_discount = 0.1  # 10% discount for round trips
            total_price = total_price * 2 * (1 - round_trip_discount)
            service_fee = service_fee * 2 * (1 - round_trip_discount)
        
        return {
            'listing_id': listing_id,
            'base_price': round(passenger_adjusted_price, 2),
            'surcharges': round(surcharges, 2),
            'overrides': round(override_amount, 2),
            'taxes': round(taxes, 2),
            'service_fee': round(service_fee, 2),
            'total_price': round(total_price, 2),
            'currency': 'USD',
            'trip_type': trip_type,
            'passengers': passengers,
            'aircraft_type': listing['aircraft_type'],
            'operator_name': listing['operator_name'],
            'breakdown': {
                'base_price': round(passenger_adjusted_price, 2),
                'surcharges': round(surcharges, 2),
                'overrides': round(override_amount, 2),
                'subtotal': round(subtotal, 2),
                'taxes': round(taxes, 2),
                'total_before_service_fee': round(total_before_service_fee, 2),
                'service_fee': round(service_fee, 2),
                'final_total': round(total_price, 2)
            }
        }
    
    async def _get_base_price(
        self, 
        origin_id: str, 
        destination_id: str, 
        aircraft_type: str, 
        operator_id: str,
        departure_date: Optional[datetime] = None
    ) -> Optional[float]:
        """Get base price from PriceBook"""
        
        now = departure_date or datetime.now(timezone.utc)
        
        # Query PriceBook with priority:
        # 1. Specific operator + aircraft type + route
        # 2. Specific aircraft type + route (any operator)
        # 3. General route pricing
        
        price_queries = [
            # Operator + aircraft type specific
            """
            SELECT base_price, price_per_min FROM pricebook 
            WHERE origin_id = :origin_id AND destination_id = :destination_id 
            AND operator_id = :operator_id AND aircraft_type = :aircraft_type
            AND (effective_from IS NULL OR effective_from <= :now)
            AND (effective_to IS NULL OR effective_to >= :now)
            ORDER BY effective_from DESC LIMIT 1
            """,
            # Aircraft type specific
            """
            SELECT base_price, price_per_min FROM pricebook 
            WHERE origin_id = :origin_id AND destination_id = :destination_id 
            AND aircraft_type = :aircraft_type AND operator_id IS NULL
            AND (effective_from IS NULL OR effective_from <= :now)
            AND (effective_to IS NULL OR effective_to >= :now)
            ORDER BY effective_from DESC LIMIT 1
            """,
            # General route pricing
            """
            SELECT base_price, price_per_min FROM pricebook 
            WHERE origin_id = :origin_id AND destination_id = :destination_id 
            AND aircraft_type IS NULL AND operator_id IS NULL
            AND (effective_from IS NULL OR effective_from <= :now)
            AND (effective_to IS NULL OR effective_to >= :now)
            ORDER BY effective_from DESC LIMIT 1
            """
        ]
        
        for query in price_queries:
            result = await database.fetch_one(query, {
                "origin_id": origin_id,
                "destination_id": destination_id,
                "operator_id": operator_id,
                "aircraft_type": aircraft_type,
                "now": now
            })
            
            if result:
                base_price = result['base_price']
                
                # If there's a per-minute rate, we could apply it based on flight duration
                # For now, we'll just use the base price
                return float(base_price)
        
        return None
    
    async def _calculate_surcharges(
        self, 
        base_price: float,
        aircraft_type: str,
        operator_id: str,
        passengers: int,
        departure_date: Optional[datetime] = None
    ) -> float:
        """Calculate applicable surcharges"""
        
        surcharge_query = """
        SELECT name, amount_type, amount, conditions FROM surcharges 
        WHERE active = true
        """
        
        surcharges = await database.fetch_all(surcharge_query)
        total_surcharge = 0.0
        
        for surcharge in surcharges:
            # Check if surcharge applies
            conditions = json.loads(surcharge['conditions']) if surcharge['conditions'] else {}
            
            applies = True
            
            # Check aircraft type condition
            if 'aircraft_types' in conditions:
                if aircraft_type not in conditions['aircraft_types']:
                    applies = False
            
            # Check operator condition
            if 'operator_ids' in conditions:
                if operator_id not in conditions['operator_ids']:
                    applies = False
            
            # Check passenger count condition
            if 'min_passengers' in conditions:
                if passengers < conditions['min_passengers']:
                    applies = False
            
            if applies:
                if surcharge['amount_type'] == 'FIXED':
                    total_surcharge += surcharge['amount']
                elif surcharge['amount_type'] == 'PERCENTAGE':
                    total_surcharge += base_price * (surcharge['amount'] / 100)
        
        return total_surcharge
    
    async def _check_overrides(
        self, 
        listing_id: str,
        operator_id: str,
        departure_date: Optional[datetime] = None
    ) -> float:
        """Check for any pricing overrides"""
        
        # This could be implemented as a separate table or special surcharges
        # For now, return 0
        return 0.0
    
    async def _calculate_taxes(
        self, 
        subtotal: float,
        country: str = 'PA',
        applies_to_base: bool = True,
        applies_to_surcharges: bool = False
    ) -> float:
        """Calculate applicable taxes"""
        
        tax_query = """
        SELECT rate, applies_to_base, applies_to_surcharges FROM taxes 
        WHERE active = true AND (country IS NULL OR country = :country)
        """
        
        taxes = await database.fetch_all(tax_query, {"country": country})
        total_tax = 0.0
        
        for tax in taxes:
            if tax['applies_to_base'] and applies_to_base:
                total_tax += subtotal * (tax['rate'] / 100)
            # Additional logic for surcharge-specific taxes could go here
        
        return total_tax

# Global pricing engine instance
pricing_engine = PricingEngine()

# Convenience functions
async def calculate_quote(listing_id: str, **kwargs) -> Dict:
    """Calculate a quote for a given listing"""
    return await pricing_engine.calculate_quote(listing_id, **kwargs)

async def get_base_price(origin_id: str, destination_id: str, aircraft_type: str, operator_id: str = None) -> Optional[float]:
    """Get base price for a route and aircraft type"""
    return await pricing_engine._get_base_price(origin_id, destination_id, aircraft_type, operator_id or "")