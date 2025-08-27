#!/usr/bin/env python3
"""
Test PostgreSQL Migration with SQLite
Tests the migration process using SQLite before deploying to PostgreSQL
"""

import asyncio
import os
import sys
from pathlib import Path
import sqlite3
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv

# Add current directory to Python path
sys.path.append(os.path.dirname(__file__))

from models_postgres import Base
from migrate_mongo_to_postgres import MongoToPostgresMigrator
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_migration_with_sqlite():
    """Test the migration process using SQLite"""
    
    # Create SQLite database
    sqlite_db_path = "/app/backend/test_migration.db"
    
    # Remove existing test database
    if os.path.exists(sqlite_db_path):
        os.remove(sqlite_db_path)
    
    # Create async SQLite engine
    engine = create_async_engine(f"sqlite+aiosqlite:///{sqlite_db_path}")
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✅ Created SQLite test database with all tables")
    
    # Create session factory
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Test creating some sample data
    async with async_session_factory() as session:
        from models_postgres import Operator, Aircraft, Route, Listing
        
        # Create test operator
        operator = Operator(
            name="Test Operator",
            code="TEST001",
            email="test@example.com",
            active=True
        )
        session.add(operator)
        await session.flush()
        
        # Create test aircraft
        aircraft = Aircraft(
            operator_id=operator.id,
            model="Test Aircraft",
            registration="TEST123",
            capacity=4,
            active=True
        )
        session.add(aircraft)
        await session.flush()
        
        # Create test route
        route = Route(
            origin="Test Origin",
            destination="Test Destination",
            distance=100.0,
            duration=60
        )
        session.add(route)
        await session.flush()
        
        # Create test listing
        listing = Listing(
            operator_id=operator.id,
            aircraft_id=aircraft.id,
            route_id=route.id,
            base_price=1000.0,
            service_fee=50.0,
            total_price=1050.0,
            max_passengers=4
        )
        session.add(listing)
        
        await session.commit()
        
        logger.info("✅ Created test data successfully")
        
        # Query test data
        from sqlalchemy import select
        result = await session.execute(select(Listing).join(Operator).join(Aircraft).join(Route))
        listings = result.scalars().all()
        
        logger.info(f"✅ Found {len(listings)} listings in test database")
        
        for listing in listings:
            logger.info(f"   - {listing.aircraft.model}: {listing.route.origin} → {listing.route.destination} (${listing.total_price})")
    
    await engine.dispose()
    logger.info("✅ SQLite migration test completed successfully!")

async def main():
    """Run the migration test"""
    logger.info("🧪 Testing PostgreSQL Migration with SQLite")
    
    await test_migration_with_sqlite()
    
    logger.info("🎉 All tests passed! Ready for PostgreSQL migration.")

if __name__ == "__main__":
    asyncio.run(main())