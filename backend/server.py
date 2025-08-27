from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Payment Integrations - PRODUCTION READY (no more DRY_RUN by default)
PAYMENTS_DRY_RUN = os.getenv('PAYMENTS_DRY_RUN', 'false').lower() == 'true'  # Only true for staging

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="SkyRide Booking API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Enums
class ListingType(str, Enum):
    CHARTER = "CHARTER"
    EMPTY_LEG = "EMPTY_LEG"
    SEAT = "SEAT"

class ListingStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SOLD_OUT = "SOLD_OUT"
    EXPIRED = "EXPIRED"

class QuoteStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CONVERTED = "CONVERTED"
    ABANDONED = "ABANDONED"

class HoldStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CONVERTED = "CONVERTED"
    CANCELLED = "CANCELLED"

class BookingStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class PaymentProvider(str, Enum):
    WOMPI = "WOMPI"
    YAPPY = "YAPPY"
    MANUAL = "MANUAL"

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PAID = "PAID"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"

# Models
class Operator(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: str
    email: str
    phone: Optional[str] = None
    website: Optional[str] = None
    logo: Optional[str] = None
    active: bool = True
    distributionOptIn: bool = False
    priceFloor: Optional[float] = None
    emptyLegWindow: Optional[int] = None
    acceptanceRate: float = 0
    avgResponseTime: int = 0
    cancelationRate: float = 0
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Aircraft(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operatorId: str
    model: str
    registration: str
    capacity: int
    hourlyRate: Optional[float] = None
    images: List[str] = []
    active: bool = True
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Route(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    origin: str
    destination: str
    distance: Optional[float] = None
    duration: Optional[int] = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Listing(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operatorId: str
    aircraftId: str
    routeId: str
    type: ListingType = ListingType.CHARTER
    status: ListingStatus = ListingStatus.ACTIVE
    basePrice: float
    serviceFee: float = 0
    pricePerSeat: Optional[float] = None
    totalPrice: float
    availableFrom: Optional[datetime] = None
    availableTo: Optional[datetime] = None
    maxPassengers: int
    availableSeats: Optional[int] = None
    confirmationSLA: Optional[int] = None
    flexibleWindow: Optional[int] = None
    departureWindow: Optional[datetime] = None
    title: Optional[str] = None
    description: Optional[str] = None
    amenities: List[str] = []
    images: List[str] = []
    featured: bool = False
    boosted: bool = False
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Quote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    token: str = Field(default_factory=lambda: str(uuid.uuid4()).replace('-', ''))
    listingId: str
    customerId: Optional[str] = None
    passengers: int
    departureDate: datetime
    returnDate: Optional[datetime] = None
    basePrice: float
    serviceFee: float
    totalPrice: float
    status: QuoteStatus = QuoteStatus.ACTIVE
    expiresAt: datetime
    viewedAt: Optional[datetime] = None
    leadId: Optional[str] = None
    source: Optional[str] = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Hold(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    quoteId: str
    depositAmount: Optional[float] = None
    status: HoldStatus = HoldStatus.ACTIVE
    expiresAt: datetime
    depositPaid: bool = False
    depositPaidAt: Optional[datetime] = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Customer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    phone: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    preferredLanguage: str = "en"
    marketingOptIn: bool = False
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    quoteId: str
    operatorId: str
    customerId: Optional[str] = None
    holdId: Optional[str] = None
    bookingNumber: str = Field(default_factory=lambda: f"SR{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}")
    status: BookingStatus = BookingStatus.PENDING
    totalAmount: float
    paidAmount: float = 0
    departureDate: datetime
    returnDate: Optional[datetime] = None
    paymentDue: Optional[datetime] = None
    fullyPaidAt: Optional[datetime] = None
    notes: Optional[str] = None
    internalNotes: Optional[str] = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bookingId: str
    provider: PaymentProvider
    amount: float
    currency: str = "USD"
    status: PaymentStatus = PaymentStatus.PENDING
    externalId: Optional[str] = None
    paymentLinkUrl: Optional[str] = None
    webhookPayload: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    failureReason: Optional[str] = None
    paidAt: Optional[datetime] = None
    failedAt: Optional[datetime] = None
    expiredAt: Optional[datetime] = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Request Models
class ListingFilters(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    date: Optional[str] = None
    passengers: Optional[int] = None
    type: Optional[ListingType] = None
    maxPrice: Optional[float] = None
    featured: Optional[bool] = None

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
    provider: PaymentProvider = PaymentProvider.WOMPI

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
def prepare_for_mongo(data):
    """Prepare data for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

def parse_from_mongo(item):
    """Parse data from MongoDB"""
    if isinstance(item, dict):
        for key, value in item.items():
            if isinstance(value, str) and key.endswith('At'):
                try:
                    item[key] = datetime.fromisoformat(value)
                except:
                    pass
            # Convert ObjectId to string for _id fields and any field ending with 'Id'
            elif (key == '_id' or key.endswith('Id')) and hasattr(value, '__str__') and 'ObjectId' in str(type(value)):
                item[key] = str(value)
            # Recursively parse nested dictionaries
            elif isinstance(value, dict):
                item[key] = parse_from_mongo(value)
            # Parse lists of dictionaries
            elif isinstance(value, list):
                item[key] = [parse_from_mongo(v) if isinstance(v, dict) else v for v in value]
        
        # Add 'id' field for frontend compatibility
        if '_id' in item and 'id' not in item:
            item['id'] = item['_id']
    return item

async def create_wompi_payment_link(booking: Booking, amount: float) -> Optional[str]:
    """Create Wompi Payment Link - PRODUCTION VERSION"""
    
    if PAYMENTS_DRY_RUN:
        # Return mock URL only in staging (DRY_RUN mode)
        return f"https://checkout.wompi.pa/l/mock_{booking.id[:8]}"
    
    try:
        # PRODUCTION WOMPI INTEGRATION
        wompi_url = "https://api.wompi.co/v1/payment_links"
        headers = {
            "Authorization": f"Bearer {os.getenv('WOMPI_PRIVATE_KEY')}",
            "Content-Type": "application/json"
        }
        
        # Create payment link with fixed amount
        payload = {
            "name": f"SkyRide Booking - {booking.bookingNumber}",
            "description": f"Charter flight booking #{booking.bookingNumber}",
            "single_use": True,
            "collect_shipping": False,
            "currency": "USD",
            "amount_in_cents": int(amount * 100),  # Fixed amount in cents
            "redirect_url": f"{os.getenv('BASE_URL')}/success?booking={booking.id}",
            "metadata": {
                "booking_id": booking.id,
                "booking_number": booking.bookingNumber
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(wompi_url, headers=headers, json=payload)
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"✅ Wompi payment link created for booking {booking.bookingNumber}")
                return data.get("data", {}).get("permalink")
            else:
                logger.error(f"Wompi error: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Failed to create Wompi payment link: {e}")
        return None

def verify_wompi_webhook(payload: bytes, signature: str) -> bool:
    """Verify Wompi webhook signature - PRODUCTION VERSION"""
    
    if PAYMENTS_DRY_RUN:
        return True  # Skip verification only in staging
        
    secret = os.getenv('WOMPI_WEBHOOK_SECRET')
    if not secret:
        logger.error("WOMPI_WEBHOOK_SECRET not configured")
        return False
        
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

async def send_whatsapp_template(template: WhatsAppTemplate) -> bool:
    """Send WhatsApp template via Chatrace"""
    if os.getenv('DRY_RUN', 'true').lower() == 'true':
        logger.info(f"DRY_RUN: Would send WhatsApp template {template.template} to {template.to}")
        return True
        
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
            
        async with httpx.AsyncClient() as client:
            response = await client.post(chatrace_url, headers=headers, json=payload)
            return response.status_code == 200
            
    except Exception as e:
        logger.error(f"Failed to send WhatsApp template: {e}")
        return False

# API Endpoints

# Public Listings
@api_router.get("/listings", response_model=List[Dict[str, Any]])
async def get_listings(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    date: Optional[str] = None,
    passengers: Optional[int] = None,
    type: Optional[ListingType] = None,
    limit: int = 20
):
    """Get filtered listings"""
    filter_query = {"status": "ACTIVE"}
    
    if origin:
        # Get route IDs for origin
        routes = await db.routes.find({"origin": {"$regex": origin, "$options": "i"}}).to_list(100)
        if routes:
            route_ids = [route["_id"] for route in routes]
            filter_query["routeId"] = {"$in": route_ids}
    
    if destination:
        routes = await db.routes.find({"destination": {"$regex": destination, "$options": "i"}}).to_list(100)
        if routes:
            route_ids = [route["_id"] for route in routes]
            if "routeId" in filter_query:
                filter_query["routeId"]["$in"] = list(set(filter_query["routeId"]["$in"]) & set(route_ids))
            else:
                filter_query["routeId"] = {"$in": route_ids}
    
    if passengers:
        filter_query["maxPassengers"] = {"$gte": passengers}
        
    if type:
        filter_query["type"] = type.value
    
    listings = await db.listings.find(filter_query).limit(limit).to_list(limit)
    
    # Populate with operator, aircraft, route data
    for listing in listings:
        # Get operator
        operator = await db.operators.find_one({"_id": listing["operatorId"]})
        listing["operator"] = operator
        
        # Get aircraft
        aircraft = await db.aircraft.find_one({"_id": listing["aircraftId"]})
        listing["aircraft"] = aircraft
        
        # Get route
        route = await db.routes.find_one({"_id": listing["routeId"]})
        listing["route"] = route
        
        listing = parse_from_mongo(listing)
    
    return listings

@api_router.post("/quotes", response_model=Dict[str, Any])
async def create_quote(quote_data: QuoteCreate):
    """Create a new quote"""
    # Get listing
    listing = await db.listings.find_one({"_id": quote_data.listingId})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Calculate pricing
    service_fee = listing["serviceFee"]
    base_price = listing["basePrice"]
    total_price = base_price + service_fee
    
    # Create quote
    quote = Quote(
        listingId=quote_data.listingId,
        passengers=quote_data.passengers,
        departureDate=datetime.fromisoformat(quote_data.departureDate),
        returnDate=datetime.fromisoformat(quote_data.returnDate) if quote_data.returnDate else None,
        basePrice=base_price,
        serviceFee=service_fee,
        totalPrice=total_price,
        expiresAt=datetime.now(timezone.utc) + timedelta(hours=48),  # 48h expiration
        source="web"
    )
    
    # Handle customer
    customer_id = None
    if quote_data.email:
        customer = await db.customers.find_one({"email": quote_data.email})
        if not customer:
            customer = Customer(
                email=quote_data.email,
                phone=quote_data.phone
            )
            customer_dict = prepare_for_mongo(customer.dict())
            await db.customers.insert_one(customer_dict)
            customer_id = customer.id
        else:
            customer_id = customer["_id"]
        
        quote.customerId = customer_id
    
    # Save quote
    quote_dict = prepare_for_mongo(quote.dict())
    await db.quotes.insert_one(quote_dict)
    
    hosted_quote_url = f"{os.getenv('BASE_URL')}/q/{quote.token}"
    
    return {
        "token": quote.token,
        "expiresAt": quote.expiresAt.isoformat(),
        "hostedQuoteUrl": hosted_quote_url,
        "totalPrice": total_price,
        "serviceFee": service_fee,
        "basePrice": base_price
    }

@api_router.get("/quotes/{token}", response_model=Dict[str, Any])
async def get_quote(token: str):
    """Get quote by token"""
    quote = await db.quotes.find_one({"token": token})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Check if expired
    if datetime.fromisoformat(quote["expiresAt"]) < datetime.now(timezone.utc):
        await db.quotes.update_one(
            {"token": token},
            {"$set": {"status": "EXPIRED", "updatedAt": datetime.now(timezone.utc).isoformat()}}
        )
        raise HTTPException(status_code=410, detail="Quote expired")
    
    # Mark as viewed
    if not quote.get("viewedAt"):
        await db.quotes.update_one(
            {"token": token},
            {"$set": {"viewedAt": datetime.now(timezone.utc).isoformat()}}
        )
    
    # Get listing details
    listing = await db.listings.find_one({"_id": quote["listingId"]})
    operator = await db.operators.find_one({"_id": listing["operatorId"]})
    aircraft = await db.aircraft.find_one({"_id": listing["aircraftId"]})
    route = await db.routes.find_one({"_id": listing["routeId"]})
    
    quote = parse_from_mongo(quote)
    
    return {
        **quote,
        "listing": parse_from_mongo(listing),
        "operator": parse_from_mongo(operator),
        "aircraft": parse_from_mongo(aircraft),
        "route": parse_from_mongo(route)
    }

@api_router.post("/holds", response_model=Dict[str, Any])
async def create_hold(hold_data: HoldCreate):
    """Create a hold from quote"""
    quote = await db.quotes.find_one({"token": hold_data.token})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    if quote["status"] != "ACTIVE":
        raise HTTPException(status_code=400, detail="Quote is not active")
    
    # Create hold
    hold = Hold(
        quoteId=str(quote["_id"]),
        depositAmount=hold_data.depositAmount,
        expiresAt=datetime.now(timezone.utc) + timedelta(hours=24)  # 24h hold
    )
    
    hold_dict = prepare_for_mongo(hold.dict())
    await db.holds.insert_one(hold_dict)
    
    return {
        "holdId": hold.id,
        "expiresAt": hold.expiresAt.isoformat(),
        "message": "Hold created successfully"
    }

@api_router.post("/checkout", response_model=Dict[str, Any])
async def create_checkout(checkout_data: CheckoutCreate):
    """Create checkout for booking"""
    order_id = checkout_data.orderId
    
    # First try to find existing booking
    booking = await db.bookings.find_one({"_id": order_id})
    
    if not booking:
        # If not found, try to find quote and create booking from it
        quote = await db.quotes.find_one({"_id": order_id})
        if not quote:
            # Try by token
            quote = await db.quotes.find_one({"token": order_id})
        
        if quote:
            # Create booking from quote
            booking_number = f"SR{datetime.now(timezone.utc).strftime('%Y%m%d')}{quote['token'][:8].upper()}"
            
            booking_data = {
                "_id": str(uuid.uuid4()),
                "quoteId": str(quote["_id"]),
                "operatorId": "op_panama_elite",  # Default for MVP
                "totalAmount": quote["totalPrice"],
                "departureDate": quote["departureDate"],
                "returnDate": quote.get("returnDate"),
                "status": "PENDING",
                "bookingNumber": booking_number,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "updatedAt": datetime.now(timezone.utc).isoformat()
            }
            
            await db.bookings.insert_one(booking_data)
            booking = booking_data
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking or quote not found")
    
    if checkout_data.provider == PaymentProvider.WOMPI:
        # Create mock booking object for payment link generation
        mock_booking = type('MockBooking', (), {
            'id': booking.get('_id'),
            'bookingNumber': booking.get('bookingNumber', 'UNKNOWN'),
            'totalAmount': booking.get('totalAmount', 0)
        })()
        
        payment_link = await create_wompi_payment_link(mock_booking, booking["totalAmount"])
        
        if payment_link:
            # Create payment record
            payment_data = {
                "_id": str(uuid.uuid4()),
                "bookingId": booking["_id"],
                "provider": "WOMPI",
                "amount": booking["totalAmount"],
                "paymentLinkUrl": payment_link,
                "description": f"Booking #{booking['bookingNumber']}",
                "status": "PENDING",
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "updatedAt": datetime.now(timezone.utc).isoformat()
            }
            
            await db.payments.insert_one(payment_data)
            
            return {"paymentLinkUrl": payment_link}
        else:
            # Fallback to open link
            fallback_url = "https://checkout.wompi.pa/l/VPOS_eMc65m"
            return {
                "paymentLinkUrl": fallback_url,
                "amount": booking["totalAmount"],
                "message": "Please enter the exact amount when paying"
            }
    
    raise HTTPException(status_code=400, detail="Payment provider not available")

# Webhook Endpoints
@api_router.post("/webhooks/wompi")
async def wompi_webhook(request):
    """Handle Wompi webhooks"""
    payload = await request.body()
    signature = request.headers.get("X-Signature", "")
    
    if not verify_wompi_webhook(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        data = json.loads(payload)
        event = data.get("event")
        transaction = data.get("data", {})
        
        # Find payment by metadata
        metadata = transaction.get("metadata", {})
        booking_id = metadata.get("booking_id")
        
        if booking_id:
            booking = await db.bookings.find_one({"_id": booking_id})
            payment = await db.payments.find_one({"bookingId": booking_id})
            
            if booking and payment:
                if event == "payment.paid":
                    # Update payment
                    await db.payments.update_one(
                        {"_id": payment["_id"]},
                        {"$set": {
                            "status": "PAID",
                            "paidAt": datetime.now(timezone.utc).isoformat(),
                            "externalId": transaction.get("id"),
                            "webhookPayload": data
                        }}
                    )
                    
                    # Update booking
                    await db.bookings.update_one(
                        {"_id": booking_id},
                        {"$set": {
                            "status": "PAID",
                            "fullyPaidAt": datetime.now(timezone.utc).isoformat(),
                            "paidAmount": booking["totalAmount"]
                        }}
                    )
                    
                elif event == "payment.failed":
                    await db.payments.update_one(
                        {"_id": payment["_id"]},
                        {"$set": {
                            "status": "FAILED",
                            "failedAt": datetime.now(timezone.utc).isoformat(),
                            "failureReason": transaction.get("failure_reason"),
                            "webhookPayload": data
                        }}
                    )
    
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        
    return {"status": "ok"}

@api_router.post("/webhooks/yappy")
async def yappy_webhook():
    """Handle Yappy webhooks - stub for next iteration"""
    return {"status": "ok", "message": "Yappy integration coming soon"}

@api_router.post("/webhooks/wa")
async def whatsapp_webhook():
    """Handle WhatsApp webhooks from Chatrace"""
    return {"status": "ok"}

# WhatsApp Integration
@api_router.post("/wa/send-template")
async def send_template(template: WhatsAppTemplate):
    """Send WhatsApp template"""
    success = await send_whatsapp_template(template)
    return {"success": success}

# n8n Integration
@api_router.post("/n8n/quotes", response_model=Dict[str, Any])
async def n8n_create_quote(quote_data: N8NQuoteRequest):
    """n8n integration for creating quotes"""
    # Create quote similar to regular endpoint
    if quote_data.listingId:
        listing = await db.listings.find_one({"_id": quote_data.listingId})
    else:
        # Find first active charter listing as fallback
        listing = await db.listings.find_one({"status": "ACTIVE", "type": "CHARTER"})
    
    if not listing:
        raise HTTPException(status_code=404, detail="No listings available")
    
    # Create quote
    quote = Quote(
        listingId=listing["_id"],
        passengers=quote_data.passengers,
        departureDate=datetime.fromisoformat(quote_data.departureDate),
        returnDate=datetime.fromisoformat(quote_data.returnDate) if quote_data.returnDate else None,
        basePrice=listing["basePrice"],
        serviceFee=listing["serviceFee"],
        totalPrice=listing["totalPrice"],
        expiresAt=datetime.now(timezone.utc) + timedelta(hours=72),  # Longer for n8n
        source="n8n",
        leadId=quote_data.leadId
    )
    
    quote_dict = prepare_for_mongo(quote.dict())
    await db.quotes.insert_one(quote_dict)
    
    hosted_quote_url = f"{os.getenv('BASE_URL')}/q/{quote.token}"
    
    return {
        "token": quote.token,
        "hostedQuoteUrl": hosted_quote_url,
        "paymentLinkUrl": f"{os.getenv('BASE_URL')}/checkout/{quote.id}"
    }

@api_router.post("/n8n/notify")
async def n8n_notify(notify_data: N8NNotifyRequest):
    """n8n integration for triggering notifications"""
    template = WhatsAppTemplate(
        template=notify_data.template,
        to=notify_data.to,
        params=notify_data.params,
        deepLink=f"{os.getenv('BASE_URL')}/q/{notify_data.quoteToken}" if notify_data.quoteToken else None
    )
    
    success = await send_whatsapp_template(template)
    return {"success": success}

# Health Check
@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "features": {
            "empty_legs": os.getenv('EMPTY_LEGS_ENABLED', 'false').lower() == 'true',
            "yappy": os.getenv('YAPPY_ENABLED', 'false').lower() == 'true'
        },
        "dry_run": os.getenv('DRY_RUN', 'true').lower() == 'true'
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# CSP Header for iframe embedding
@app.middleware("http")
async def add_csp_header(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "frame-ancestors https://www.skyride.city"
    return response