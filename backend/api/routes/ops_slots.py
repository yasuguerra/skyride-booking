"""
Operations API for managing aircraft availability slots + ICS import.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional
import logging

from ...database_postgres import get_session
from ...services.availability import AvailabilityService
from ...integrations.ics_importer import sync_aircraft_ics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ops", tags=["Operations"])


class SlotCreate(BaseModel):
    """Request model for creating/updating availability slots."""
    aircraftId: str = Field(..., description="Aircraft identifier")
    start: datetime = Field(..., description="Slot start time (UTC)")
    end: datetime = Field(..., description="Slot end time (UTC)")
    status: Literal["AVAILABLE", "BUSY", "MAINTENANCE"] = Field(
        default="AVAILABLE", 
        description="Slot availability status"
    )
    source: Literal["PORTAL", "ICS", "GOOGLE"] = Field(
        default="PORTAL",
        description="Source of the slot data"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional notes about the slot"
    )


class SlotResponse(BaseModel):
    """Response model for availability slots."""
    id: str
    aircraft_id: str
    start_time: str
    end_time: str
    status: str
    source: str
    notes: Optional[str]
    created_at: str
    updated_at: str


@router.post("/slots", response_model=SlotResponse)
async def create_or_update_slot(
    slot_data: SlotCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Create or update an availability slot for an aircraft.
    
    This endpoint implements upsert logic based on (aircraftId, start, end).
    If a slot with identical coordinates exists, it will be updated.
    Otherwise, a new slot is created after validating for overlaps.
    
    - **aircraftId**: Aircraft identifier
    - **start**: Slot start time in UTC
    - **end**: Slot end time in UTC  
    - **status**: AVAILABLE, BUSY, or MAINTENANCE
    - **source**: PORTAL (manual), ICS (calendar), or GOOGLE (sync)
    - **notes**: Optional notes about the slot
    """
    try:
        # Validate time range
        if slot_data.end <= slot_data.start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time must be after start time"
            )
        
        # Create or update slot
        slot = await AvailabilityService.create_or_update_slot(
            session=session,
            aircraft_id=slot_data.aircraftId,
            start=slot_data.start,
            end=slot_data.end,
            status=slot_data.status,
            source=slot_data.source,
            notes=slot_data.notes
        )
        
        return SlotResponse(
            id=str(slot.id),
            aircraft_id=slot.aircraft_id,
            start_time=slot.start_time.isoformat(),
            end_time=slot.end_time.isoformat(),
            status=slot.status,
            source=slot.source,
            notes=slot.notes,
            created_at=slot.created_at.isoformat(),
            updated_at=slot.updated_at.isoformat()
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating/updating slot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create or update slot"
        )

@router.post("/ics/sync")
async def sync_ics_calendar(
    aircraftId: str = Query(..., description="Aircraft ID to sync"),
    ics_url: Optional[str] = Query(None, description="Override ICS URL"),
    db: AsyncSession = Depends(get_session)
):
    """
    Sync aircraft availability from ICS calendar.
    Creates slots with source="ICS".
    """
    try:
        result = await sync_aircraft_ics(aircraftId, db, ics_url)
        return {
            "success": True,
            "message": f"ICS sync completed for aircraft {aircraftId}",
            "result": result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"ICS sync error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ICS sync failed: {str(e)}"
        )
