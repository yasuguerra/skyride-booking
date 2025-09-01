"""
Pricing Engine Service
Handles dynamic pricing calculation with breakdown transparency.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime, timezone
import logging

from ..models_postgres import PriceBook, Surcharge, PriceOverride, Route, Aircraft, Listing

logger = logging.getLogger(__name__)


class PricingService:
    """Service for calculating transparent pricing with breakdown."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def calculate_quote_pricing(
        self,
        route_id: str,
        aircraft_id: str,
        passengers: int = 1,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculate full pricing breakdown for a quote.
        
        Returns breakdown with:
        - Base Price (from PriceBook or listing)
        - Service Fee (5% default)
        - Surcharges (seasonal, weekend, etc.)
        - ITBMS (7% tax)
        - Total Price
        """
        try:
            # Get route and aircraft info
            route_result = await self.session.execute(select(Route).where(Route.id == route_id))
            route = route_result.scalar_one_or_none()
            
            aircraft_result = await self.session.execute(select(Aircraft).where(Aircraft.id == aircraft_id))
            aircraft = aircraft_result.scalar_one_or_none()
            
            if not route or not aircraft:
                raise ValueError("Route or aircraft not found")
            
            # Get base price from listing or calculate dynamically
            base_price = await self._get_base_price(route_id, aircraft_id, date)
            
            # Calculate service fee (5% default)
            service_fee_rate = 0.05
            service_fee = base_price * service_fee_rate
            
            # Calculate applicable surcharges
            surcharges = await self._calculate_surcharges(
                route=route,
                aircraft=aircraft,
                passengers=passengers,
                date=date,
                base_price=base_price
            )
            
            # Calculate subtotal
            subtotal = base_price + service_fee + sum(s['amount'] for s in surcharges)
            
            # Calculate ITBMS (7% tax on subtotal)
            itbms_rate = 0.07
            itbms = subtotal * itbms_rate
            
            # Calculate total
            total_price = subtotal + itbms
            
            return {
                'breakdown': {
                    'base_price': round(base_price, 2),
                    'service_fee': round(service_fee, 2),
                    'service_fee_rate': service_fee_rate,
                    'surcharges': surcharges,
                    'subtotal': round(subtotal, 2),
                    'itbms': round(itbms, 2),
                    'itbms_rate': itbms_rate,
                    'total_price': round(total_price, 2)
                },
                'currency': 'USD',
                'passengers': passengers,
                'calculation_date': datetime.now(timezone.utc).isoformat(),
                'route': {
                    'id': route.id,
                    'name': route.name,
                    'origin': route.origin,
                    'destination': route.destination
                },
                'aircraft': {
                    'id': aircraft.id,
                    'registration': aircraft.registration,
                    'type': aircraft.type
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating pricing: {e}")
            raise
    
    async def _get_base_price(
        self,
        route_id: str,
        aircraft_id: str,
        date: Optional[datetime] = None
    ) -> float:
        """Get base price from price overrides, PriceBook, or listing fallback."""
        
        # Check for price overrides first
        if date:
            override_result = await self.session.execute(
                select(PriceOverride).where(
                    and_(
                        or_(
                            PriceOverride.route_id == route_id,
                            PriceOverride.aircraft_id == aircraft_id
                        ),
                        PriceOverride.effective_from <= date,
                        or_(
                            PriceOverride.effective_to.is_(None),
                            PriceOverride.effective_to >= date
                        )
                    )
                )
            )
            override = override_result.scalar_one_or_none()
            
            if override:
                logger.info(f"Using price override: ${override.override_price}")
                return override.override_price
        
        # Get active PriceBook and calculate dynamic price
        current_date = date or datetime.now(timezone.utc)
        pricebook_result = await self.session.execute(
            select(PriceBook).where(
                and_(
                    PriceBook.active.is_(True),
                    PriceBook.effective_from <= current_date,
                    or_(
                        PriceBook.effective_to.is_(None),
                        PriceBook.effective_to >= current_date
                    )
                )
            ).order_by(PriceBook.effective_from.desc())
        )
        pricebook = pricebook_result.scalar_one_or_none()
        
        if pricebook:
            # Get route for distance calculation
            route_result = await self.session.execute(select(Route).where(Route.id == route_id))
            route = route_result.scalar_one_or_none()
            
            if route and route.distance_nm:
                # Dynamic pricing based on distance
                base_rate_per_nm = 15.0  # $15 per nautical mile base rate
                base_price = route.distance_nm * base_rate_per_nm
                logger.info(f"Using dynamic pricing: {route.distance_nm}nm × ${base_rate_per_nm} = ${base_price}")
                return base_price
        
        # Fallback to listing price
        listing_result = await self.session.execute(
            select(Listing).where(
                and_(
                    Listing.route_id == route_id,
                    Listing.aircraft_id == aircraft_id
                )
            )
        )
        listing = listing_result.scalar_one_or_none()
        
        if listing:
            logger.info(f"Using listing base price: ${listing.base_price}")
            return listing.base_price
        
        # Default fallback
        logger.warning(f"No pricing found for route {route_id} + aircraft {aircraft_id}, using default")
        return 5000.0  # Default $5000
    
    async def _calculate_surcharges(
        self,
        route: Any,
        aircraft: Any,
        passengers: int,
        date: Optional[datetime],
        base_price: float
    ) -> List[Dict[str, Any]]:
        """Calculate applicable surcharges."""
        
        surcharges = []
        current_date = date or datetime.now(timezone.utc)
        
        # Get active PriceBook
        pricebook_result = await self.session.execute(
            select(PriceBook).where(
                and_(
                    PriceBook.active.is_(True),
                    PriceBook.effective_from <= current_date,
                    or_(
                        PriceBook.effective_to.is_(None),
                        PriceBook.effective_to >= current_date
                    )
                )
            ).order_by(PriceBook.effective_from.desc())
        )
        pricebook = pricebook_result.scalar_one_or_none()
        
        if not pricebook:
            return surcharges
        
        # Get all surcharges for this PriceBook
        surcharge_result = await self.session.execute(
            select(Surcharge).where(Surcharge.price_book_id == pricebook.id)
        )
        all_surcharges = surcharge_result.scalars().all()
        
        for surcharge in all_surcharges:
            # Check if surcharge applies
            if not self._surcharge_applies(surcharge, route, aircraft, passengers, date):
                continue
            
            # Calculate surcharge amount
            if surcharge.type == 'PERCENTAGE':
                amount = base_price * (surcharge.amount / 100)
            else:  # FIXED
                amount = surcharge.amount
            
            surcharges.append({
                'name': surcharge.name,
                'code': surcharge.code,
                'type': surcharge.type,
                'rate': surcharge.amount,
                'amount': round(amount, 2)
            })
        
        return surcharges
    
    def _surcharge_applies(
        self,
        surcharge: Surcharge,
        route: Any,
        aircraft: Any,
        passengers: int,
        date: Optional[datetime]
    ) -> bool:
        """Check if a surcharge applies to the current conditions."""
        
        # Check aircraft type
        if surcharge.aircraft_type and surcharge.aircraft_type != aircraft.type:
            return False
        
        # Check passenger count
        if surcharge.min_passengers and passengers < surcharge.min_passengers:
            return False
        if surcharge.max_passengers and passengers > surcharge.max_passengers:
            return False
        
        # Check route pattern (regex match on route name)
        if surcharge.route_pattern:
            import re
            if not re.search(surcharge.route_pattern, route.name, re.IGNORECASE):
                return False
        
        # Add date-based checks (weekend, seasonal, etc.)
        if date:
            # Weekend surcharge example
            if surcharge.code == 'WEEKEND' and date.weekday() < 5:  # Mon-Fri
                return False
            
            # Holiday season surcharge example
            if surcharge.code == 'HOLIDAY' and not self._is_holiday_season(date):
                return False
        
        return True
    
    def _is_holiday_season(self, date: datetime) -> bool:
        """Check if date falls in holiday season (example: Dec 15 - Jan 15)."""
        month = date.month
        day = date.day
        
        return (month == 12 and day >= 15) or (month == 1 and day <= 15)


async def calculate_quote_pricing(
    session: AsyncSession,
    route_id: str,
    aircraft_id: str,
    passengers: int = 1,
    date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Convenience function for calculating quote pricing.
    
    This is the main entry point for pricing calculations.
    """
    pricing_service = PricingService(session)
    return await pricing_service.calculate_quote_pricing(
        route_id=route_id,
        aircraft_id=aircraft_id,
        passengers=passengers,
        date=date
    )
