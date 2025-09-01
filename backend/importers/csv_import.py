"""
CSV/XLSX Import Service for PostgreSQL
Handles bulk imports of operators, aircraft, routes, and listings with validation.
"""
import pandas as pd
import csv
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime, timezone
import logging
import uuid
from pathlib import Path

from ..models_postgres import Operator, Aircraft, Route, Listing, Airport
from ..database_postgres import get_session

logger = logging.getLogger(__name__)


class CSVImporter:
    """CSV/XLSX importer with validation and error reporting."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.errors: List[Dict[str, Any]] = []
    
    async def import_operators(self, file_path: str) -> Dict[str, Any]:
        """
        Import operators from CSV/XLSX.
        Required columns: code, name, email, phone, address
        """
        try:
            # Read file
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
            
            required_columns = ['code', 'name', 'email', 'phone', 'address']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            operators_created = 0
            operators_updated = 0
            
            for index, row in df.iterrows():
                try:
                    # Validate required fields
                    if pd.isna(row['code']) or pd.isna(row['name']):
                        self.errors.append({
                            'row': index + 2,  # Excel row number
                            'entity': 'operator',
                            'error': 'Missing required fields: code or name'
                        })
                        continue
                    
                    # Check if operator exists (upsert by code)
                    existing_result = await self.session.execute(
                        select(Operator).where(Operator.code == row['code'])
                    )
                    existing_operator = existing_result.scalar_one_or_none()
                    
                    if existing_operator:
                        # Update existing
                        existing_operator.name = row['name']
                        existing_operator.email = row['email'] if not pd.isna(row['email']) else None
                        existing_operator.phone = row['phone'] if not pd.isna(row['phone']) else None
                        existing_operator.address = row['address'] if not pd.isna(row['address']) else None
                        existing_operator.updated_at = datetime.now(timezone.utc)
                        operators_updated += 1
                    else:
                        # Create new
                        operator = Operator(
                            code=row['code'],
                            name=row['name'],
                            email=row['email'] if not pd.isna(row['email']) else None,
                            phone=row['phone'] if not pd.isna(row['phone']) else None,
                            address=row['address'] if not pd.isna(row['address']) else None
                        )
                        self.session.add(operator)
                        operators_created += 1
                
                except Exception as e:
                    self.errors.append({
                        'row': index + 2,
                        'entity': 'operator',
                        'error': str(e)
                    })
            
            await self.session.commit()
            
            return {
                'success': True,
                'created': operators_created,
                'updated': operators_updated,
                'errors': len(self.errors)
            }
            
        except Exception as e:
            logger.error(f"Error importing operators: {e}")
            return {
                'success': False,
                'error': str(e),
                'errors': len(self.errors)
            }
    
    async def import_aircraft(self, file_path: str) -> Dict[str, Any]:
        """
        Import aircraft from CSV/XLSX.
        Required columns: registration, type, operator_code, max_passengers
        """
        try:
            # Read file
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
            
            required_columns = ['registration', 'type', 'operator_code', 'max_passengers']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            aircraft_created = 0
            aircraft_updated = 0
            
            for index, row in df.iterrows():
                try:
                    # Validate required fields
                    if pd.isna(row['registration']) or pd.isna(row['operator_code']):
                        self.errors.append({
                            'row': index + 2,
                            'entity': 'aircraft',
                            'error': 'Missing required fields: registration or operator_code'
                        })
                        continue
                    
                    # Find operator
                    operator_result = await self.session.execute(
                        select(Operator).where(Operator.code == row['operator_code'])
                    )
                    operator = operator_result.scalar_one_or_none()
                    
                    if not operator:
                        self.errors.append({
                            'row': index + 2,
                            'entity': 'aircraft',
                            'error': f'Operator not found: {row["operator_code"]}'
                        })
                        continue
                    
                    # Check if aircraft exists (upsert by registration)
                    existing_result = await self.session.execute(
                        select(Aircraft).where(Aircraft.registration == row['registration'])
                    )
                    existing_aircraft = existing_result.scalar_one_or_none()
                    
                    if existing_aircraft:
                        # Update existing
                        existing_aircraft.type = row['type']
                        existing_aircraft.operator_id = operator.id
                        existing_aircraft.max_passengers = int(row['max_passengers']) if not pd.isna(row['max_passengers']) else None
                        existing_aircraft.updated_at = datetime.now(timezone.utc)
                        aircraft_updated += 1
                    else:
                        # Create new
                        aircraft = Aircraft(
                            registration=row['registration'],
                            type=row['type'],
                            operator_id=operator.id,
                            max_passengers=int(row['max_passengers']) if not pd.isna(row['max_passengers']) else None
                        )
                        self.session.add(aircraft)
                        aircraft_created += 1
                
                except Exception as e:
                    self.errors.append({
                        'row': index + 2,
                        'entity': 'aircraft',
                        'error': str(e)
                    })
            
            await self.session.commit()
            
            return {
                'success': True,
                'created': aircraft_created,
                'updated': aircraft_updated,
                'errors': len(self.errors)
            }
            
        except Exception as e:
            logger.error(f"Error importing aircraft: {e}")
            return {
                'success': False,
                'error': str(e),
                'errors': len(self.errors)
            }
    
    async def import_listings(self, file_path: str) -> Dict[str, Any]:
        """
        Import listings from CSV/XLSX.
        Required columns: route_code, aircraft_registration, base_price, service_fee
        """
        try:
            # Read file
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
            
            required_columns = ['route_code', 'aircraft_registration', 'base_price', 'service_fee']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            listings_created = 0
            listings_updated = 0
            
            for index, row in df.iterrows():
                try:
                    # Validate required fields
                    if pd.isna(row['route_code']) or pd.isna(row['aircraft_registration']):
                        self.errors.append({
                            'row': index + 2,
                            'entity': 'listing',
                            'error': 'Missing required fields'
                        })
                        continue
                    
                    # Find route
                    route_result = await self.session.execute(
                        select(Route).where(Route.code == row['route_code'])
                    )
                    route = route_result.scalar_one_or_none()
                    
                    if not route:
                        self.errors.append({
                            'row': index + 2,
                            'entity': 'listing',
                            'error': f'Route not found: {row["route_code"]}'
                        })
                        continue
                    
                    # Find aircraft
                    aircraft_result = await self.session.execute(
                        select(Aircraft).where(Aircraft.registration == row['aircraft_registration'])
                    )
                    aircraft = aircraft_result.scalar_one_or_none()
                    
                    if not aircraft:
                        self.errors.append({
                            'row': index + 2,
                            'entity': 'listing',
                            'error': f'Aircraft not found: {row["aircraft_registration"]}'
                        })
                        continue
                    
                    # Check if listing exists (upsert by route + aircraft)
                    existing_result = await self.session.execute(
                        select(Listing).where(
                            Listing.route_id == route.id,
                            Listing.aircraft_id == aircraft.id
                        )
                    )
                    existing_listing = existing_result.scalar_one_or_none()
                    
                    if existing_listing:
                        # Update existing
                        existing_listing.base_price = float(row['base_price'])
                        existing_listing.service_fee = float(row['service_fee'])
                        existing_listing.updated_at = datetime.now(timezone.utc)
                        listings_updated += 1
                    else:
                        # Create new
                        listing = Listing(
                            route_id=route.id,
                            aircraft_id=aircraft.id,
                            operator_id=aircraft.operator_id,
                            base_price=float(row['base_price']),
                            service_fee=float(row['service_fee']),
                            total_price=float(row['base_price']) + float(row['service_fee'])
                        )
                        self.session.add(listing)
                        listings_created += 1
                
                except Exception as e:
                    self.errors.append({
                        'row': index + 2,
                        'entity': 'listing',
                        'error': str(e)
                    })
            
            await self.session.commit()
            
            return {
                'success': True,
                'created': listings_created,
                'updated': listings_updated,
                'errors': len(self.errors)
            }
            
        except Exception as e:
            logger.error(f"Error importing listings: {e}")
            return {
                'success': False,
                'error': str(e),
                'errors': len(self.errors)
            }
    
    def export_errors_csv(self, output_path: str = "import_errors.csv"):
        """Export import errors to CSV file."""
        if not self.errors:
            logger.info("No errors to export")
            return
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['row', 'entity', 'error']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for error in self.errors:
                writer.writerow(error)
        
        logger.info(f"Exported {len(self.errors)} errors to {output_path}")


async def import_from_csv(entity_type: str, file_path: str) -> Dict[str, Any]:
    """
    Main import function for different entity types.
    
    Args:
        entity_type: 'operators', 'aircraft', or 'listings'
        file_path: Path to CSV or XLSX file
    
    Returns:
        Import result with statistics and errors
    """
    async with get_session() as session:
        importer = CSVImporter(session)
        
        if entity_type == 'operators':
            result = await importer.import_operators(file_path)
        elif entity_type == 'aircraft':
            result = await importer.import_aircraft(file_path)
        elif entity_type == 'listings':
            result = await importer.import_listings(file_path)
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        # Export errors if any
        if importer.errors:
            error_file = f"import_errors_{entity_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            importer.export_errors_csv(error_file)
            result['error_file'] = error_file
        
        return result
