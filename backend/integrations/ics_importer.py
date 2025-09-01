"""
ICS Calendar Importer for SkyRide
Imports aircraft availability from ICS calendar feeds
Creates availability slots with source="ICS"
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import httpx
from icalendar import Calendar, Event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from models_postgres import Aircraft, AvailabilitySlot
import pytz

logger = logging.getLogger(__name__)

# Panama timezone
PANAMA_TZ = pytz.timezone('America/Panama')

class ICSImporter:
    """Import aircraft availability from ICS calendar feeds."""
    
    def __init__(self):
        self.user_agent = "SkyRide-ICS-Importer/2.0"
    
    async def fetch_ics(self, url: str) -> str:
        """Fetch ICS content from URL."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": self.user_agent},
                    timeout=30.0,
                    follow_redirects=True
                )
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"❌ Failed to fetch ICS from {url}: {e}")
            raise
    
    def parse_ics(self, ics_content: str) -> List[Dict[str, Any]]:
        """Parse ICS content and extract events."""
        try:
            calendar = Calendar.from_ical(ics_content)
            events = []
            
            for component in calendar.walk():
                if component.name == "VEVENT":
                    event = self._parse_event(component)
                    if event:
                        events.append(event)
            
            logger.info(f"📅 Parsed {len(events)} events from ICS")
            return events
            
        except Exception as e:
            logger.error(f"❌ Failed to parse ICS: {e}")
            raise
    
    def _parse_event(self, event: Event) -> Optional[Dict[str, Any]]:
        """Parse individual ICS event."""
        try:
            # Extract basic info
            summary = str(event.get('summary', ''))
            description = str(event.get('description', ''))
            
            # Extract dates
            dtstart = event.get('dtstart')
            dtend = event.get('dtend')
            
            if not dtstart or not dtend:
                return None
            
            # Convert to datetime objects
            start_dt = dtstart.dt
            end_dt = dtend.dt
            
            # Handle all-day events
            if isinstance(start_dt, datetime):
                # Already datetime
                pass
            else:
                # Date only - convert to datetime
                start_dt = datetime.combine(start_dt, datetime.min.time())
                end_dt = datetime.combine(end_dt, datetime.min.time())
            
            # Ensure timezone awareness
            if start_dt.tzinfo is None:
                start_dt = PANAMA_TZ.localize(start_dt)
            if end_dt.tzinfo is None:
                end_dt = PANAMA_TZ.localize(end_dt)
            
            # Convert to UTC
            start_utc = start_dt.astimezone(timezone.utc)
            end_utc = end_dt.astimezone(timezone.utc)
            
            return {
                'summary': summary,
                'description': description,
                'start_time': start_utc,
                'end_time': end_utc,
                'duration_hours': (end_utc - start_utc).total_seconds() / 3600,
                'raw_event': str(event)
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse event: {e}")
            return None
    
    async def sync_aircraft_ics(
        self, 
        aircraft_id: str, 
        db: AsyncSession,
        ics_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sync aircraft availability from ICS calendar.
        
        Args:
            aircraft_id: Aircraft ID to sync
            db: Database session
            ics_url: Override ICS URL (if not in aircraft.calendar_url)
        """
        
        # Get aircraft
        result = await db.execute(select(Aircraft).where(Aircraft.id == aircraft_id))
        aircraft = result.scalar_one_or_none()
        
        if not aircraft:
            raise ValueError(f"Aircraft {aircraft_id} not found")
        
        # Get ICS URL
        calendar_url = ics_url or aircraft.calendar_url
        if not calendar_url:
            raise ValueError(f"No calendar URL configured for aircraft {aircraft_id}")
        
        logger.info(f"📅 Syncing ICS for aircraft {aircraft_id} from {calendar_url}")
        
        # Fetch and parse ICS
        ics_content = await self.fetch_ics(calendar_url)
        events = self.parse_ics(ics_content)
        
        # Filter relevant events (next 6 months)
        now = datetime.now(timezone.utc)
        future_limit = now + timedelta(days=180)
        
        relevant_events = [
            event for event in events
            if event['start_time'] >= now and event['start_time'] <= future_limit
        ]
        
        logger.info(f"📅 Found {len(relevant_events)} relevant events for next 6 months")
        
        # Create/update availability slots
        slots_created = 0
        slots_updated = 0
        
        for event in relevant_events:
            # Check if slot already exists
            existing_result = await db.execute(
                select(AvailabilitySlot).where(
                    and_(
                        AvailabilitySlot.aircraft_id == aircraft_id,
                        AvailabilitySlot.start_time == event['start_time'],
                        AvailabilitySlot.source == "ICS"
                    )
                )
            )
            existing_slot = existing_result.scalar_one_or_none()
            
            if existing_slot:
                # Update existing
                existing_slot.end_time = event['end_time']
                existing_slot.duration_hours = event['duration_hours']
                existing_slot.metadata = {
                    'summary': event['summary'],
                    'description': event['description'],
                    'ics_sync_at': now.isoformat()
                }
                slots_updated += 1
            else:
                # Create new slot
                new_slot = AvailabilitySlot(
                    aircraft_id=aircraft_id,
                    start_time=event['start_time'],
                    end_time=event['end_time'],
                    duration_hours=event['duration_hours'],
                    source="ICS",
                    is_available=True,
                    metadata={
                        'summary': event['summary'],
                        'description': event['description'],
                        'ics_sync_at': now.isoformat(),
                        'raw_event': event['raw_event']
                    }
                )
                db.add(new_slot)
                slots_created += 1
        
        await db.commit()
        
        sync_result = {
            'aircraft_id': aircraft_id,
            'calendar_url': calendar_url,
            'total_events': len(events),
            'relevant_events': len(relevant_events),
            'slots_created': slots_created,
            'slots_updated': slots_updated,
            'sync_timestamp': now.isoformat()
        }
        
        logger.info(f"✅ ICS sync complete: {slots_created} created, {slots_updated} updated")
        return sync_result

# Convenience function
async def sync_aircraft_ics(aircraft_id: str, db: AsyncSession, ics_url: Optional[str] = None):
    """Sync single aircraft from ICS."""
    importer = ICSImporter()
    return await importer.sync_aircraft_ics(aircraft_id, db, ics_url)
