"""
Availability management service for aircraft slots and scheduling.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.dialects.postgresql import insert
import logging

from ..models_postgres import AvailabilitySlot
from ..redis_service import get_hold_info, redis_client

logger = logging.getLogger(__name__)


class AvailabilityService:
    """Service for managing aircraft availability slots and holds integration."""
    
    @staticmethod
    async def create_or_update_slot(
        session: AsyncSession,
        aircraft_id: str,
        start: datetime,
        end: datetime,
        status: str = "AVAILABLE",
        source: str = "PORTAL", 
        notes: Optional[str] = None
    ) -> AvailabilitySlot:
        """
        Create or update availability slot with upsert logic.
        Validates overlaps and maintains data integrity.
        """
        # Validate overlap with existing slots for same aircraft
        overlap_query = select(AvailabilitySlot).where(
            and_(
                AvailabilitySlot.aircraft_id == aircraft_id,
                or_(
                    and_(AvailabilitySlot.start_time <= start, AvailabilitySlot.end_time > start),
                    and_(AvailabilitySlot.start_time < end, AvailabilitySlot.end_time >= end),
                    and_(AvailabilitySlot.start_time >= start, AvailabilitySlot.end_time <= end)
                )
            )
        )
        
        existing_overlaps = await session.execute(overlap_query)
        overlapping_slots = existing_overlaps.scalars().all()
        
        # For upsert, check if exact match exists
        exact_match_query = select(AvailabilitySlot).where(
            and_(
                AvailabilitySlot.aircraft_id == aircraft_id,
                AvailabilitySlot.start_time == start,
                AvailabilitySlot.end_time == end
            )
        )
        
        existing_exact = await session.execute(exact_match_query)
        existing_slot = existing_exact.scalar_one_or_none()
        
        if existing_slot:
            # Update existing slot
            existing_slot.status = status
            existing_slot.source = source
            existing_slot.notes = notes
            existing_slot.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(existing_slot)
            return existing_slot
        
        # Check for problematic overlaps (not exact matches)
        if overlapping_slots:
            overlap_details = [
                f"{slot.start_time} - {slot.end_time} ({slot.status})"
                for slot in overlapping_slots
            ]
            raise ValueError(
                f"Slot overlaps with existing slots: {', '.join(overlap_details)}"
            )
        
        # Create new slot
        new_slot = AvailabilitySlot(
            aircraft_id=aircraft_id,
            start_time=start,
            end_time=end,
            status=status,
            source=source,
            notes=notes
        )
        
        session.add(new_slot)
        await session.commit()
        await session.refresh(new_slot)
        
        logger.info(f"Created availability slot for aircraft {aircraft_id}: {start} - {end} ({status})")
        return new_slot
    
    @staticmethod
    async def get_availability(
        session: AsyncSession,
        aircraft_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get availability slots with hold information overlay.
        Returns enriched slot data including real-time hold status.
        """
        query = select(AvailabilitySlot)
        
        conditions = []
        if aircraft_id:
            conditions.append(AvailabilitySlot.aircraft_id == aircraft_id)
        if start_date:
            conditions.append(AvailabilitySlot.end_time >= start_date)
        if end_date:
            conditions.append(AvailabilitySlot.start_time <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(AvailabilitySlot.aircraft_id, AvailabilitySlot.start_time)
        
        result = await session.execute(query)
        slots = result.scalars().all()
        
        # Enrich with hold information from Redis
        enriched_slots = []
        for slot in slots:
            slot_data = {
                "id": slot.id,
                "aircraft_id": slot.aircraft_id,
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "status": slot.status,
                "source": slot.source,
                "notes": slot.notes,
                "created_at": slot.created_at.isoformat(),
                "updated_at": slot.updated_at.isoformat(),
                "hold_info": None
            }
            
            # Check for active holds affecting this slot
            if slot.status == "AVAILABLE":
                # Check Redis for holds affecting this aircraft and time range
                hold_info = await get_hold_info(slot.aircraft_id, slot.start_time, slot.end_time)
                if hold_info:
                    slot_data["hold_info"] = hold_info
                    slot_data["effective_status"] = "ON_HOLD"
                else:
                    slot_data["effective_status"] = "AVAILABLE"
            else:
                slot_data["effective_status"] = slot.status
            
            enriched_slots.append(slot_data)
        
        return enriched_slots
    
    @staticmethod
    async def check_slot_availability(
        session: AsyncSession,
        aircraft_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Check if a specific time slot is available for booking.
        Returns availability status and any conflicting information.
        """
        # Check database slots
        query = select(AvailabilitySlot).where(
            and_(
                AvailabilitySlot.aircraft_id == aircraft_id,
                or_(
                    and_(AvailabilitySlot.start_time <= start_time, AvailabilitySlot.end_time > start_time),
                    and_(AvailabilitySlot.start_time < end_time, AvailabilitySlot.end_time >= end_time),
                    and_(AvailabilitySlot.start_time >= start_time, AvailabilitySlot.end_time <= end_time)
                )
            )
        )
        
        result = await session.execute(query)
        conflicting_slots = result.scalars().all()
        
        # Check for BUSY or MAINTENANCE slots
        blocking_slots = [
            slot for slot in conflicting_slots 
            if slot.status in ["BUSY", "MAINTENANCE"]
        ]
        
        if blocking_slots:
            return {
                "available": False,
                "reason": "SLOT_CONFLICT",
                "conflicting_slots": [
                    {
                        "start": slot.start_time.isoformat(),
                        "end": slot.end_time.isoformat(),
                        "status": slot.status,
                        "notes": slot.notes
                    }
                    for slot in blocking_slots
                ]
            }
        
        # Check Redis for active holds
        hold_info = await get_hold_info(aircraft_id, start_time, end_time)
        if hold_info:
            return {
                "available": False,
                "reason": "ACTIVE_HOLD",
                "hold_info": hold_info
            }
        
        return {
            "available": True,
            "reason": None,
            "available_slots": [
                {
                    "start": slot.start_time.isoformat(),
                    "end": slot.end_time.isoformat(),
                    "status": slot.status
                }
                for slot in conflicting_slots
                if slot.status == "AVAILABLE"
            ]
        }
