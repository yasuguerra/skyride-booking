"""
WhatsApp integration for SkyRide - Template messaging via Chatrace
Enhanced with logging in MessageLog table
"""

import os
import logging
import httpx
from typing import Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from models_postgres import MessageLog
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class WhatsAppService:
    """WhatsApp template messaging service."""
    
    def __init__(self):
        self.chatrace_token = os.getenv("CHATRACE_TOKEN")
        self.chatrace_url = os.getenv("CHATRACE_URL", "https://api.chatrace.com")
        self.enabled = os.getenv("WHATSAPP_ENABLED", "false").lower() == "true"
        
        if not self.chatrace_token and self.enabled:
            logger.warning("⚠️ WhatsApp enabled but CHATRACE_TOKEN not configured")
    
    async def send_template(
        self, 
        template: str, 
        to: str, 
        params: Dict[str, Any],
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp template message.
        
        Args:
            template: Template name (quote_created, booking_confirmed, etc.)
            to: Phone number in international format
            params: Template parameters
            db: Database session for logging
        """
        
        if not self.enabled:
            logger.info(f"📱 WhatsApp disabled - would send {template} to {to}")
            return {"status": "disabled", "message": "WhatsApp not enabled"}
        
        if not self.chatrace_token:
            logger.error("❌ CHATRACE_TOKEN not configured")
            return {"status": "error", "message": "WhatsApp not configured"}
        
        # Prepare message data
        message_data = {
            "to": to,
            "template": template,
            "parameters": params,
            "language": "es"  # Panama timezone - Spanish
        }
        
        # Log message attempt
        if db:
            log_entry = MessageLog(
                id=f"wa_{int(datetime.now().timestamp())}",
                customer_phone=to,
                message_type="whatsapp_template",
                template_name=template,
                message_data=message_data,
                provider="chatrace",
                created_at=datetime.now(timezone.utc)
            )
            db.add(log_entry)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.chatrace_url}/api/v1/messages/template",
                    headers={
                        "Authorization": f"Bearer {self.chatrace_token}",
                        "Content-Type": "application/json"
                    },
                    json=message_data,
                    timeout=30.0
                )
                
                result = {
                    "status": "sent" if response.status_code == 200 else "failed",
                    "status_code": response.status_code,
                    "response": response.json() if response.status_code == 200 else response.text,
                    "template": template,
                    "to": to
                }
                
                # Update log with result
                if db and log_entry:
                    log_entry.status = "sent" if response.status_code == 200 else "failed"
                    log_entry.response_data = result
                    log_entry.sent_at = datetime.now(timezone.utc)
                    await db.commit()
                
                logger.info(f"📱 WhatsApp {template} → {to}: {result['status']}")
                return result
                
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "template": template,
                "to": to
            }
            
            # Update log with error
            if db and log_entry:
                log_entry.status = "error"
                log_entry.response_data = error_result
                await db.commit()
            
            logger.error(f"❌ WhatsApp error: {e}")
            return error_result

# Template definitions
TEMPLATES = {
    "quote_created": {
        "name": "quote_created",
        "params": ["customer_name", "route", "date", "amount", "quote_url"]
    },
    "booking_confirmed": {
        "name": "booking_confirmed", 
        "params": ["customer_name", "flight_details", "booking_reference"]
    },
    "payment_received": {
        "name": "payment_received",
        "params": ["customer_name", "amount", "booking_reference"]
    },
    "flight_reminder": {
        "name": "flight_reminder",
        "params": ["customer_name", "flight_time", "pickup_location"]
    }
}

async def send_quote_notification(
    customer_phone: str,
    customer_name: str,
    route: str,
    date: str,
    amount: str,
    quote_url: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """Send quote created notification."""
    
    whatsapp = WhatsAppService()
    return await whatsapp.send_template(
        template="quote_created",
        to=customer_phone,
        params={
            "customer_name": customer_name,
            "route": route,
            "date": date,
            "amount": amount,
            "quote_url": quote_url
        },
        db=db
    )

async def send_booking_confirmation(
    customer_phone: str,
    customer_name: str,
    flight_details: str,
    booking_reference: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """Send booking confirmation."""
    
    whatsapp = WhatsAppService()
    return await whatsapp.send_template(
        template="booking_confirmed",
        to=customer_phone,
        params={
            "customer_name": customer_name,
            "flight_details": flight_details,
            "booking_reference": booking_reference
        },
        db=db
    )
