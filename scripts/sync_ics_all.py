#!/usr/bin/env python3
"""
Sync all aircraft from ICS calendars
Usage: python scripts/sync_ics_all.py
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from database_postgres import async_session_factory
from integrations.ics_importer import sync_aircraft_ics
from models_postgres import Aircraft
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def sync_all_aircraft():
    """Sync all aircraft that have calendar URLs configured."""
    
    logger.info("🔄 Starting ICS sync for all aircraft...")
    
    async with async_session_factory() as db:
        # Get all aircraft with calendar URLs
        result = await db.execute(
            select(Aircraft).where(Aircraft.calendar_url.isnot(None))
        )
        aircraft_list = result.scalars().all()
        
        if not aircraft_list:
            logger.info("📅 No aircraft with calendar URLs found")
            return
        
        logger.info(f"📅 Found {len(aircraft_list)} aircraft with calendar URLs")
        
        success_count = 0
        error_count = 0
        
        for aircraft in aircraft_list:
            try:
                logger.info(f"📅 Syncing {aircraft.id} ({aircraft.model})...")
                
                result = await sync_aircraft_ics(aircraft.id, db)
                
                logger.info(
                    f"✅ {aircraft.id}: {result['slots_created']} created, "
                    f"{result['slots_updated']} updated"
                )
                success_count += 1
                
            except Exception as e:
                logger.error(f"❌ Failed to sync {aircraft.id}: {e}")
                error_count += 1
        
        logger.info(f"🏁 ICS sync complete: {success_count} success, {error_count} errors")

async def sync_single_aircraft(aircraft_id: str):
    """Sync a single aircraft by ID."""
    
    logger.info(f"🔄 Syncing single aircraft: {aircraft_id}")
    
    async with async_session_factory() as db:
        try:
            result = await sync_aircraft_ics(aircraft_id, db)
            logger.info(f"✅ Sync complete: {result}")
        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
            raise

if __name__ == "__main__":
    # Check for aircraft ID argument
    if len(sys.argv) > 1:
        aircraft_id = sys.argv[1]
        asyncio.run(sync_single_aircraft(aircraft_id))
    else:
        asyncio.run(sync_all_aircraft())
