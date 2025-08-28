"""
Enhanced Holds API with idempotency support and concurrency protection.
"""
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import logging
import hashlib

from ...database_postgres import get_session
from ...redis_service import get_redis, RedisService
from ...services.availability import AvailabilityService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Holds"])


class HoldRequest(BaseModel):
    """Request model for creating holds."""
    listing_id: str
    customer_email: str
    customer_phone: Optional[str] = None
    duration_minutes: int = 1440  # 24 hours default


class HoldResponse(BaseModel):
    """Response model for hold creation."""
    hold_id: str
    listing_id: str
    status: str
    expires_at: datetime
    remaining_seconds: int
    created_from_idempotency: bool = False


@router.post("/holds", response_model=HoldResponse)
async def create_hold(
    hold_request: HoldRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_session),
    redis: RedisService = Depends(get_redis)
):
    """
    Create a hold on a listing with idempotency support.
    
    If an Idempotency-Key header is provided, this endpoint will return
    the same result for repeated requests with the same key (within 24h).
    
    This prevents duplicate hold creation in case of network retries
    or user double-clicks.
    
    - **listing_id**: ID of the listing to hold
    - **customer_email**: Customer email for the hold
    - **customer_phone**: Optional customer phone
    - **duration_minutes**: Hold duration (default 24 hours)
    
    Headers:
    - **Idempotency-Key**: Optional key for request idempotency
    """
    try:
        # Check idempotency first
        if idempotency_key:
            # Hash the key for consistent storage
            key_hash = hashlib.sha256(idempotency_key.encode()).hexdigest()
            existing_result = await redis.get_idempotency_result(key_hash)
            
            if existing_result:
                logger.info(f"Returning cached result for idempotency key: {idempotency_key}")
                existing_result["created_from_idempotency"] = True
                return HoldResponse(**existing_result)
        
        # Validate listing exists (this would need actual implementation)
        # For now, we'll proceed with hold creation
        
        # Create hold with Redis atomic operation
        hold_created = await redis.create_hold_lock(
            listing_id=hold_request.listing_id,
            hold_duration_minutes=hold_request.duration_minutes
        )
        
        if not hold_created:
            # Hold already exists - check if it's the same request
            existing_hold = await redis.get_hold_info(hold_request.listing_id)
            if existing_hold:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "LISTING_ALREADY_ON_HOLD",
                        "message": f"Listing {hold_request.listing_id} is already on hold",
                        "existing_hold": existing_hold
                    }
                )
        
        # Get hold information for response
        hold_info = await redis.get_hold_info(hold_request.listing_id)
        if not hold_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve hold information after creation"
            )
        
        # Calculate expires_at
        created_at = datetime.fromtimestamp(hold_info["created_at"])
        expires_at = created_at.timestamp() + hold_info["expires_in_seconds"]
        expires_at_dt = datetime.fromtimestamp(expires_at)
        
        # Create response
        hold_response = {
            "hold_id": f"hold_{hold_request.listing_id}_{hold_info['created_at']}",
            "listing_id": hold_request.listing_id,
            "status": "ACTIVE",
            "expires_at": expires_at_dt,
            "remaining_seconds": hold_info["remaining_seconds"],
            "created_from_idempotency": False
        }
        
        # Store result for idempotency if key provided
        if idempotency_key:
            key_hash = hashlib.sha256(idempotency_key.encode()).hexdigest()
            await redis.store_idempotency_key(key_hash, hold_response)
        
        logger.info(f"Created hold for listing {hold_request.listing_id}")
        return HoldResponse(**hold_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating hold: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create hold"
        )


@router.get("/holds/{listing_id}")
async def get_hold_status(
    listing_id: str,
    redis: RedisService = Depends(get_redis)
):
    """
    Get current hold status for a listing.
    
    Returns hold information if active, or null if no hold exists.
    """
    try:
        hold_info = await redis.get_hold_info(listing_id)
        
        if not hold_info:
            return {
                "hold_exists": False,
                "listing_id": listing_id
            }
        
        # Calculate expires_at
        created_at = datetime.fromtimestamp(hold_info["created_at"])
        expires_at = created_at.timestamp() + hold_info["expires_in_seconds"]
        expires_at_dt = datetime.fromtimestamp(expires_at)
        
        return {
            "hold_exists": True,
            "hold_id": f"hold_{listing_id}_{hold_info['created_at']}",
            "listing_id": listing_id,
            "status": "ACTIVE",
            "expires_at": expires_at_dt,
            "remaining_seconds": hold_info["remaining_seconds"]
        }
        
    except Exception as e:
        logger.error(f"Error getting hold status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get hold status"
        )


@router.delete("/holds/{listing_id}")
async def release_hold(
    listing_id: str,
    redis: RedisService = Depends(get_redis)
):
    """
    Release a hold on a listing.
    
    This makes the listing available for booking again.
    """
    try:
        released = await redis.release_hold_lock(listing_id)
        
        if not released:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active hold found for listing {listing_id}"
            )
        
        return {
            "status": "RELEASED",
            "listing_id": listing_id,
            "message": f"Hold released for listing {listing_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error releasing hold: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to release hold"
        )
