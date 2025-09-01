"""
WhatsApp API routes for SkyRide
Template messaging with logging
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from database_postgres import get_db
from integrations.whatsapp import WhatsAppService, TEMPLATES
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wa", tags=["WhatsApp"])

class SendTemplateRequest(BaseModel):
    """Request to send WhatsApp template."""
    template: str = Field(..., description="Template name")
    to: str = Field(..., description="Phone number in international format (+507XXXXXXXX)")
    params: Dict[str, Any] = Field(default_factory=dict, description="Template parameters")

class SendTemplateResponse(BaseModel):
    """Response from template send."""
    status: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    template: str
    to: str

@router.post("/send-template", response_model=SendTemplateResponse)
async def send_template(
    request: SendTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send WhatsApp template message.
    
    Available templates:
    - quote_created: Customer quote notification
    - booking_confirmed: Booking confirmation  
    - payment_received: Payment confirmation
    - flight_reminder: Flight reminder
    """
    
    # Validate template
    if request.template not in TEMPLATES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid template. Available: {list(TEMPLATES.keys())}"
        )
    
    # Validate phone format
    if not request.to.startswith("+507"):
        raise HTTPException(
            status_code=400,
            detail="Phone number must be in Panama format (+507XXXXXXXX)"
        )
    
    # Send template
    whatsapp = WhatsAppService()
    result = await whatsapp.send_template(
        template=request.template,
        to=request.to,
        params=request.params,
        db=db
    )
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail=f"WhatsApp error: {result.get('error', 'Unknown error')}"
        )
    
    return SendTemplateResponse(
        status=result["status"],
        message_id=result.get("response", {}).get("message_id"),
        template=request.template,
        to=request.to
    )

@router.get("/templates")
async def list_templates():
    """List available WhatsApp templates."""
    return {
        "templates": TEMPLATES,
        "usage": {
            "quote_created": "Sent when a new quote is created",
            "booking_confirmed": "Sent when booking is confirmed",
            "payment_received": "Sent when payment is processed",
            "flight_reminder": "Sent before flight departure"
        }
    }

@router.get("/status")
async def whatsapp_status():
    """Get WhatsApp service status."""
    whatsapp = WhatsAppService()
    return {
        "enabled": whatsapp.enabled,
        "configured": bool(whatsapp.chatrace_token),
        "endpoint": whatsapp.chatrace_url
    }
