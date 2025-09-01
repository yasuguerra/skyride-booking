"""
Availability API for querying aircraft availability with holds integration.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import logging

from ...database_postgres import get_session
from ...services.availability import AvailabilityService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Availability"])


class AvailabilityResponse(BaseModel):
    """Response model for availability queries."""
    aircraft_id: Optional[str]
    date_range: str
    slots: List[Dict[str, Any]]
    summary: Dict[str, int]


def parse_date_range(date_range: str) -> tuple[datetime, datetime]:
    """Parse date range string in format YYYY-MM-DD..YYYY-MM-DD"""
    try:
        start_str, end_str = date_range.split("..")
        start_date = datetime.strptime(start_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_str, "%Y-%m-%d")
        end_date = end_date.replace(hour=23, minute=59, second=59)
        return start_date, end_date
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date range format. Use YYYY-MM-DD..YYYY-MM-DD"
        )


@router.get("/availability", response_model=AvailabilityResponse)
async def get_availability(
    aircraftId: Optional[str] = Query(None, description="Filter by aircraft ID"),
    dateRange: str = Query(..., description="Date range in format YYYY-MM-DD..YYYY-MM-DD"),
    session: AsyncSession = Depends(get_session)
):
    """
    Get aircraft availability with hold information overlay.
    
    Returns availability slots enriched with real-time hold status from Redis.
    Slots marked as AVAILABLE may show as ON_HOLD if there's an active hold.
    
    - **aircraftId**: Optional filter for specific aircraft
    - **dateRange**: Date range in format YYYY-MM-DD..YYYY-MM-DD
    """
    try:
        start_date, end_date = parse_date_range(dateRange)
        
        slots = await AvailabilityService.get_availability(
            session=session,
            aircraft_id=aircraftId,
            start_date=start_date,
            end_date=end_date
        )
        
        # Generate summary statistics
        summary = {
            "total_slots": len(slots),
            "available": len([s for s in slots if s["effective_status"] == "AVAILABLE"]),
            "busy": len([s for s in slots if s["effective_status"] == "BUSY"]), 
            "maintenance": len([s for s in slots if s["effective_status"] == "MAINTENANCE"]),
            "on_hold": len([s for s in slots if s["effective_status"] == "ON_HOLD"])
        }
        
        return AvailabilityResponse(
            aircraft_id=aircraftId,
            date_range=dateRange,
            slots=slots,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Error fetching availability: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch availability data"
        )


@router.get("/availability/check")
async def check_slot_availability(
    aircraftId: str = Query(..., description="Aircraft ID to check"),
    start: datetime = Query(..., description="Start time (UTC)"),
    end: datetime = Query(..., description="End time (UTC)"),
    session: AsyncSession = Depends(get_session)
):
    """
    Check if a specific time slot is available for booking.
    
    Returns detailed availability information including conflicts and hold status.
    Useful for validating booking requests before creating holds.
    
    - **aircraftId**: Aircraft to check
    - **start**: Start time in UTC
    - **end**: End time in UTC
    """
    try:
        result = await AvailabilityService.check_slot_availability(
            session=session,
            aircraft_id=aircraftId,
            start_time=start,
            end_time=end
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error checking slot availability: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to check slot availability"
        )
