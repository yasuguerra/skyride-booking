"""
SkyRide Booking Platform - PostgreSQL Version
FastAPI server with PostgreSQL, Redis, Wompi integration, and Chatrace WhatsApp
Maintains all existing endpoints while using PostgreSQL backend
"""

from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any, Literal
import uuid
from datetime import datetime, timedelta, timezone
import httpx
import hmac
import hashlib
import json
from enum import Enum
import redis.asyncio as aioredis

# Import our new PostgreSQL models and database
from database_postgres import get_db, init_db, close_db
from models_postgres import (
    Operator, Aircraft, Route, Listing, Customer, Quote, Hold, 
    Booking, Payment, MessageLog, EventLog, Policy, WebhookEvent,
    ListingType, ListingStatus, QuoteStatus, HoldStatus, 
    BookingStatus, PaymentProvider, PaymentStatus
)
from redis_service import get_redis, RedisService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app
app = FastAPI(title="SkyRide Booking API - PostgreSQL", version="2.0.0")
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Enums for request/response models (matching existing API)
class ListingTypeEnum(str, Enum):
    CHARTER = "CHARTER"
    EMPTY_LEG = "EMPTY_LEG"
    SEAT = "SEAT"

class PaymentProviderEnum(str, Enum):
    WOMPI = "WOMPI"
    YAPPY = "YAPPY"
    MANUAL = "MANUAL"

# Pydantic models for API (matching existing API)
class QuoteCreate(BaseModel):
    listingId: str
    passengers: int
    departureDate: str
    returnDate: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class HoldCreate(BaseModel):
    token: str
    depositAmount: Optional[float] = None

class CheckoutCreate(BaseModel):
    orderId: str
    provider: PaymentProviderEnum = PaymentProviderEnum.WOMPI

class WhatsAppTemplate(BaseModel):
    template: str
    to: str
    params: Dict[str, str] = {}
    deepLink: Optional[str] = None

class N8NQuoteRequest(BaseModel):
    listingId: Optional[str] = None
    passengers: int
    departureDate: str
    returnDate: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    leadId: Optional[str] = None

class N8NNotifyRequest(BaseModel):
    template: str
    to: str
    params: Dict[str, str] = {}
    quoteToken: Optional[str] = None

# Utility Functions
async def create_wompi_payment_link(booking: Booking, amount: float) -> Optional[str]:
    """Create Wompi Payment Link - PRODUCTION VERSION"""
    
    # Check if we're in dry run mode (only for staging)
    dry_run = os.getenv('PAYMENTS_DRY_RUN', 'false').lower() == 'true'
    
    if dry_run:
        # Return mock URL in DRY_RUN mode (staging only)
        return f"https://checkout.wompi.pa/l/mock_{booking.id.hex[:8]}"
    
    try:
        # PRODUCTION WOMPI INTEGRATION
        wompi_url = "https://api.wompi.co/v1/payment_links"
        headers = {
            "Authorization": f"Bearer {os.getenv('WOMPI_PRIVATE_KEY')}",
            "Content-Type": "application/json"
        }
        
        # Create payment link with fixed amount
        payload = {
            "name": f"SkyRide Booking - {booking.booking_number}",
            "description": f"Charter flight booking #{booking.booking_number}",
            "single_use": True,
            "collect_shipping": False,
            "currency": "USD",
            "amount_in_cents": int(amount * 100),  # Fixed amount in cents
            "redirect_url": f"{os.getenv('BASE_URL')}/success?booking={booking.id}",
            "metadata": {
                "booking_id": str(booking.id),
                "booking_number": booking.booking_number,
                "lead_id": booking.quote.lead_id if booking.quote else None
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(wompi_url, headers=headers, json=payload)
            
            if response.status_code == 201:
                data = response.json()
                return data.get("data", {}).get("permalink")
            else:
                logger.error(f"Wompi error: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Failed to create Wompi payment link: {e}")
        return None

def verify_wompi_webhook(payload: bytes, signature: str) -> bool:
    """Verify Wompi webhook signature - PRODUCTION VERSION"""
    
    # Always verify in production
    dry_run = os.getenv('PAYMENTS_DRY_RUN', 'false').lower() == 'true'
    if dry_run:
        return True  # Skip verification in staging
        
    secret = os.getenv('WOMPI_WEBHOOK_SECRET')
    if not secret:
        return False
        
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

async def send_whatsapp_template(template: WhatsAppTemplate) -> bool:
    """Send WhatsApp template via Chatrace - PRODUCTION VERSION"""
    
    try:
        chatrace_url = f"{os.getenv('CHATRACE_API_URL')}/messages/template"
        headers = {
            "Authorization": f"Bearer {os.getenv('CHATRACE_API_TOKEN')}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "template_name": template.template,
            "to": template.to,
            "parameters": template.params
        }
        
        if template.deepLink:
            payload["parameters"]["link"] = template.deepLink
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(chatrace_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                logger.info(f"✅ WhatsApp template {template.template} sent to {template.to}")
                return True
            else:
                logger.error(f"Chatrace error: {response.status_code} - {response.text}")
                return False
            
    except Exception as e:
        logger.error(f"Failed to send WhatsApp template: {e}")
        return False

# API Endpoints - Maintaining existing URLs and contracts

# Public Listings
@api_router.get("/listings")
async def get_listings(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    date: Optional[str] = None,
    passengers: Optional[int] = None,
    type: Optional[ListingTypeEnum] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get filtered listings - PostgreSQL version"""
    
    # Build query with filters
    query = select(Listing).join(Operator).join(Aircraft).join(Route).where(
        Listing.status == ListingStatus.ACTIVE
    )
    
    if origin:
        query = query.where(Route.origin.ilike(f"%{origin}%"))
    
    if destination:
        query = query.where(Route.destination.ilike(f"%{destination}%"))
        
    if passengers:
        query = query.where(Listing.max_passengers >= passengers)
        
    if type:
        query = query.where(Listing.type == type.value)
    
    # Order by featured, then created_at
    query = query.order_by(Listing.featured.desc(), Listing.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    listings = result.scalars().all()
    
    # Convert to dict format matching existing API
    response_data = []
    for listing in listings:
        # Populate relationships
        operator_result = await db.execute(select(Operator).where(Operator.id == listing.operator_id))
        operator = operator_result.scalar_one()
        
        aircraft_result = await db.execute(select(Aircraft).where(Aircraft.id == listing.aircraft_id))
        aircraft = aircraft_result.scalar_one()
        
        route_result = await db.execute(select(Route).where(Route.id == listing.route_id))
        route = route_result.scalar_one()
        
        listing_dict = {
            "_id": str(listing.id),
            "id": str(listing.id),
            "operatorId": str(listing.operator_id),
            "aircraftId": str(listing.aircraft_id),
            "routeId": str(listing.route_id),
            "type": listing.type.value,
            "status": listing.status.value,
            "basePrice": listing.base_price,
            "serviceFee": listing.service_fee,
            "totalPrice": listing.total_price,
            "maxPassengers": listing.max_passengers,
            "confirmationSLA": listing.confirmation_sla,
            "title": listing.title,
            "description": listing.description,
            "amenities": listing.amenities,
            "images": listing.images,
            "featured": listing.featured,
            "boosted": listing.boosted,
            "createdAt": listing.created_at.isoformat(),
            "updatedAt": listing.updated_at.isoformat(),
            "operator": {
                "_id": str(operator.id),
                "name": operator.name,
                "code": operator.code,
                "email": operator.email,
                "logo": operator.logo
            },
            "aircraft": {
                "_id": str(aircraft.id),
                "model": aircraft.model,
                "registration": aircraft.registration,
                "capacity": aircraft.capacity,
                "images": aircraft.images
            },
            "route": {
                "_id": str(route.id),
                "origin": route.origin,
                "destination": route.destination,
                "distance": route.distance,
                "duration": route.duration
            }
        }
        response_data.append(listing_dict)
    
    return response_data

@api_router.post("/quotes")
async def create_quote(quote_data: QuoteCreate, db: AsyncSession = Depends(get_db)):
    """Create a new quote - PostgreSQL version"""
    
    # Get listing
    listing_result = await db.execute(select(Listing).where(Listing.id == quote_data.listingId))
    listing = listing_result.scalar_one_or_none()
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Calculate pricing
    service_fee = listing.service_fee
    base_price = listing.base_price
    total_price = base_price + service_fee
    
    # Create quote
    quote = Quote(
        token=str(uuid.uuid4()).replace('-', ''),
        listing_id=listing.id,
        passengers=quote_data.passengers,
        departure_date=datetime.fromisoformat(quote_data.departureDate),
        return_date=datetime.fromisoformat(quote_data.returnDate) if quote_data.returnDate else None,
        base_price=base_price,
        service_fee=service_fee,
        total_price=total_price,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=48),  # 48h expiration
        source="web"
    )
    
    # Handle customer
    if quote_data.email:
        customer_result = await db.execute(select(Customer).where(Customer.email == quote_data.email))
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            customer = Customer(
                email=quote_data.email,
                phone=quote_data.phone,
                full_name=quote_data.email.split('@')[0]  # Simple default
            )
            db.add(customer)
            await db.flush()
            
        quote.customer_id = customer.id
    
    # Save quote
    db.add(quote)
    await db.commit()
    await db.refresh(quote)
    
    hosted_quote_url = f"{os.getenv('BASE_URL')}/q/{quote.token}"
    
    return {
        "token": quote.token,
        "expiresAt": quote.expires_at.isoformat(),
        "hostedQuoteUrl": hosted_quote_url,
        "totalPrice": total_price,
        "serviceFee": service_fee,
        "basePrice": base_price
    }

@api_router.get("/quotes/{token}")
async def get_quote(token: str, db: AsyncSession = Depends(get_db)):
    """Get quote by token - PostgreSQL version"""
    
    quote_result = await db.execute(select(Quote).where(Quote.token == token))
    quote = quote_result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Check if expired
    if quote.expires_at < datetime.now(timezone.utc):
        quote.status = QuoteStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=410, detail="Quote expired")
    
    # Mark as viewed
    if not quote.viewed_at:
        quote.viewed_at = datetime.now(timezone.utc)
        await db.commit()
    
    # Get related data
    listing_result = await db.execute(select(Listing).where(Listing.id == quote.listing_id))
    listing = listing_result.scalar_one()
    
    operator_result = await db.execute(select(Operator).where(Operator.id == listing.operator_id))
    operator = operator_result.scalar_one()
    
    aircraft_result = await db.execute(select(Aircraft).where(Aircraft.id == listing.aircraft_id))
    aircraft = aircraft_result.scalar_one()
    
    route_result = await db.execute(select(Route).where(Route.id == listing.route_id))
    route = route_result.scalar_one()
    
    return {
        "_id": str(quote.id),
        "id": str(quote.id),
        "token": quote.token,
        "listingId": str(quote.listing_id),
        "passengers": quote.passengers,
        "departureDate": quote.departure_date.isoformat(),
        "returnDate": quote.return_date.isoformat() if quote.return_date else None,
        "basePrice": quote.base_price,
        "serviceFee": quote.service_fee,
        "totalPrice": quote.total_price,
        "status": quote.status.value,
        "expiresAt": quote.expires_at.isoformat(),
        "viewedAt": quote.viewed_at.isoformat() if quote.viewed_at else None,
        "createdAt": quote.created_at.isoformat(),
        "listing": {
            "_id": str(listing.id),
            "title": listing.title,
            "description": listing.description,
            "maxPassengers": listing.max_passengers,
            "amenities": listing.amenities
        },
        "operator": {
            "_id": str(operator.id),
            "name": operator.name,
            "code": operator.code
        },
        "aircraft": {
            "_id": str(aircraft.id),
            "model": aircraft.model,
            "capacity": aircraft.capacity
        },
        "route": {
            "_id": str(route.id),
            "origin": route.origin,
            "destination": route.destination
        }
    }

@api_router.post("/holds")
async def create_hold(
    hold_data: HoldCreate, 
    db: AsyncSession = Depends(get_db),
    redis: RedisService = Depends(get_redis)
):
    """Create a hold from quote - PostgreSQL + Redis version"""
    
    quote_result = await db.execute(select(Quote).where(Quote.token == hold_data.token))
    quote = quote_result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    if quote.status != QuoteStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Quote is not active")
    
    # Check if listing is already on hold (Redis lock)
    listing_id = str(quote.listing_id)
    if await redis.is_on_hold(listing_id):
        raise HTTPException(status_code=409, detail="Listing is already on hold")
    
    # Create Redis hold lock (24 hours)
    hold_created = await redis.create_hold_lock(listing_id, hold_duration_minutes=1440)
    
    if not hold_created:
        raise HTTPException(status_code=409, detail="Failed to create hold lock")
    
    # Create hold record in PostgreSQL
    hold = Hold(
        quote_id=quote.id,
        deposit_amount=hold_data.depositAmount,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)  # 24h hold
    )
    
    db.add(hold)
    await db.commit()
    await db.refresh(hold)
    
    return {
        "holdId": str(hold.id),
        "expiresAt": hold.expires_at.isoformat(),
        "message": "Hold created successfully"
    }

@api_router.post("/checkout")
async def create_checkout(checkout_data: CheckoutCreate, db: AsyncSession = Depends(get_db)):
    """Create checkout for booking - PostgreSQL version"""
    
    order_id = checkout_data.orderId
    
    # First try to find existing booking
    booking_result = await db.execute(select(Booking).where(Booking.id == order_id))
    booking = booking_result.scalar_one_or_none()
    
    if not booking:
        # Try to find quote and create booking from it
        quote_result = await db.execute(
            select(Quote).where(or_(Quote.id == order_id, Quote.token == order_id))
        )
        quote = quote_result.scalar_one_or_none()
        
        if quote:
            # Create booking from quote
            booking_number = f"SR{datetime.now(timezone.utc).strftime('%Y%m%d')}{quote.token[:8].upper()}"
            
            booking = Booking(
                quote_id=quote.id,
                operator_id=quote.listing.operator_id,
                booking_number=booking_number,
                total_amount=quote.total_price,
                departure_date=quote.departure_date,
                return_date=quote.return_date,
                status=BookingStatus.PENDING
            )
            
            db.add(booking)
            await db.commit()
            await db.refresh(booking)
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking or quote not found")
    
    if checkout_data.provider == PaymentProviderEnum.WOMPI:
        payment_link = await create_wompi_payment_link(booking, booking.total_amount)
        
        if payment_link:
            # Create payment record
            payment = Payment(
                booking_id=booking.id,
                provider=PaymentProvider.WOMPI,
                amount=booking.total_amount,
                payment_link_url=payment_link,
                description=f"Booking #{booking.booking_number}"
            )
            
            db.add(payment)
            await db.commit()
            
            return {"paymentLinkUrl": payment_link}
        else:
            # Fallback to open link
            fallback_url = "https://checkout.wompi.pa/l/VPOS_eMc65m"
            return {
                "paymentLinkUrl": fallback_url,
                "amount": booking.total_amount,
                "message": "Please enter the exact amount when paying"
            }
    
    raise HTTPException(status_code=400, detail="Payment provider not available")

# Webhook Endpoints
@api_router.post("/webhooks/wompi")
async def wompi_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Wompi webhooks - PRODUCTION VERSION"""
    
    payload = await request.body()
    signature = request.headers.get("x-wompi-signature", "")
    
    if not verify_wompi_webhook(payload, signature):
        logger.warning("Invalid Wompi webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        data = json.loads(payload.decode('utf-8'))
        event = data.get("event")
        transaction = data.get("data", {})
        
        # Find payment by metadata
        metadata = transaction.get("metadata", {})
        booking_id = metadata.get("booking_id")
        
        if booking_id:
            booking_result = await db.execute(select(Booking).where(Booking.id == booking_id))
            booking = booking_result.scalar_one_or_none()
            
            payment_result = await db.execute(select(Payment).where(Payment.booking_id == booking_id))
            payment = payment_result.scalar_one_or_none()
            
            if booking and payment:
                if event == "payment.paid":
                    # Update payment
                    payment.status = PaymentStatus.PAID
                    payment.paid_at = datetime.now(timezone.utc)
                    payment.external_id = transaction.get("id")
                    payment.webhook_payload = data
                    
                    # Update booking
                    booking.status = BookingStatus.PAID
                    booking.fully_paid_at = datetime.now(timezone.utc)
                    booking.paid_amount = booking.total_amount
                    
                    await db.commit()
                    
                    logger.info(f"✅ Payment confirmed for booking {booking.booking_number}")
                    
                elif event == "payment.failed":
                    payment.status = PaymentStatus.FAILED
                    payment.failed_at = datetime.now(timezone.utc)
                    payment.failure_reason = transaction.get("failure_reason")
                    payment.webhook_payload = data
                    
                    await db.commit()
                    
                    logger.info(f"❌ Payment failed for booking {booking.booking_number}")
    
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        
    return {"status": "ok"}

@api_router.post("/webhooks/yappy")
async def yappy_webhook():
    """Handle Yappy webhooks - stub for next iteration"""
    return {"status": "ok", "message": "Yappy integration coming soon"}

@api_router.post("/webhooks/wa")
async def whatsapp_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle WhatsApp webhooks from Chatrace - PRODUCTION VERSION"""
    
    try:
        data = await request.json()
        
        # Log incoming WhatsApp event
        message_log = MessageLog(
            channel="WHATSAPP",
            direction="INBOUND",
            content=data.get("message", {}).get("text", ""),
            wa_id=data.get("from"),
            message_id=data.get("id"),
            status="DELIVERED",
            message_metadata=data
        )
        
        db.add(message_log)
        await db.commit()
        
        logger.info(f"📱 WhatsApp message logged from {data.get('from')}")
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
    
    return {"status": "ok"}

# WhatsApp Integration
@api_router.post("/wa/send-template")
async def send_template(template: WhatsAppTemplate, db: AsyncSession = Depends(get_db)):
    """Send WhatsApp template - PRODUCTION VERSION"""
    
    success = await send_whatsapp_template(template)
    
    # Log outbound message
    message_log = MessageLog(
        channel="WHATSAPP",
        direction="OUTBOUND",
        template=template.template,
        wa_id=template.to,
        status="SENT" if success else "FAILED",
        message_metadata=template.dict()
    )
    
    db.add(message_log)
    await db.commit()
    
    return {"success": success}

# n8n Integration (same endpoints)
@api_router.post("/n8n/quotes")
async def n8n_create_quote(quote_data: N8NQuoteRequest, db: AsyncSession = Depends(get_db)):
    """n8n integration for creating quotes - PostgreSQL version"""
    
    listing = None
    if quote_data.listingId:
        listing_result = await db.execute(select(Listing).where(Listing.id == quote_data.listingId))
        listing = listing_result.scalar_one_or_none()
    
    if not listing:
        # Find first active charter listing as fallback
        listing_result = await db.execute(
            select(Listing).where(
                and_(Listing.status == ListingStatus.ACTIVE, Listing.type == ListingType.CHARTER)
            ).limit(1)
        )
        listing = listing_result.scalar_one_or_none()
    
    if not listing:
        raise HTTPException(status_code=404, detail="No listings available")
    
    # Create quote
    quote = Quote(
        token=str(uuid.uuid4()).replace('-', ''),
        listing_id=listing.id,
        passengers=quote_data.passengers,
        departure_date=datetime.fromisoformat(quote_data.departureDate),
        return_date=datetime.fromisoformat(quote_data.returnDate) if quote_data.returnDate else None,
        base_price=listing.base_price,
        service_fee=listing.service_fee,
        total_price=listing.total_price,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),  # Longer for n8n
        source="n8n",
        lead_id=quote_data.leadId
    )
    
    db.add(quote)
    await db.commit()
    await db.refresh(quote)
    
    hosted_quote_url = f"{os.getenv('BASE_URL')}/q/{quote.token}"
    
    return {
        "token": quote.token,
        "hostedQuoteUrl": hosted_quote_url,
        "paymentLinkUrl": f"{os.getenv('BASE_URL')}/checkout/{quote.id}"
    }

@api_router.post("/n8n/notify")
async def n8n_notify(notify_data: N8NNotifyRequest, db: AsyncSession = Depends(get_db)):
    """n8n integration for triggering notifications"""
    
    template = WhatsAppTemplate(
        template=notify_data.template,
        to=notify_data.to,
        params=notify_data.params,
        deepLink=f"{os.getenv('BASE_URL')}/q/{notify_data.quoteToken}" if notify_data.quoteToken else None
    )
    
    success = await send_whatsapp_template(template)
    
    # Log the message
    message_log = MessageLog(
        channel="WHATSAPP",
        direction="OUTBOUND",
        template=template.template,
        wa_id=template.to,
        status="SENT" if success else "FAILED",
        message_metadata=template.dict()
    )
    
    db.add(message_log)
    await db.commit()
    
    return {"success": success}

# Health Check
@api_router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint - PostgreSQL version"""
    
    try:
        # Test database connection
        await db.execute(select(1))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
    
    return {
        "status": "ok",
        "database": db_status,
        "database_type": "PostgreSQL",
        "features": {
            "empty_legs": os.getenv('EMPTY_LEGS_ENABLED', 'false').lower() == 'true',
            "yappy": os.getenv('YAPPY_ENABLED', 'false').lower() == 'true'
        },
        "payments_dry_run": os.getenv('PAYMENTS_DRY_RUN', 'false').lower() == 'true',
        "version": "2.0.0"
    }

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database and Redis on startup"""
    logger.info("🚀 Starting SkyRide Platform - PostgreSQL Version")
    
    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")
    
    # Initialize Redis
    from redis_service import redis_service
    await redis_service.connect()
    logger.info("✅ Redis connected")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    logger.info("🛑 Shutting down SkyRide Platform")
    
    # Close database connections
    await close_db()
    logger.info("📴 Database connections closed")
    
    # Close Redis connections
    from redis_service import redis_service
    await redis_service.disconnect()
    logger.info("📴 Redis disconnected")

# CSP Header for iframe embedding
@app.middleware("http")
async def add_csp_header(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "frame-ancestors https://www.skyride.city"
    return response

# GA4 Cross-domain tracking middleware
@app.middleware("http")
async def add_ga4_headers(request, call_next):
    response = await call_next(request)
    if "booking.skyride.city" in str(request.url):
        response.headers["X-GA4-Cross-Domain"] = "enabled"
    return response