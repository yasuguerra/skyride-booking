from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

# SQLAlchemy Models
class Airport(Base):
    __tablename__ = "airports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), unique=True, index=True, nullable=False)  # IATA/ICAO code
    name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timezone = Column(String(50), nullable=False, default='America/Panama')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Operator(Base):
    __tablename__ = "operators"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, index=True, nullable=True)
    name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    base_airport_id = Column(UUID(as_uuid=True), ForeignKey('airports.id'), nullable=True)
    payout_info = Column(JSON, nullable=True)
    flags = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    base_airport = relationship("Airport")
    aircraft = relationship("Aircraft", back_populates="operator")

class Aircraft(Base):
    __tablename__ = "aircraft"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operator_id = Column(UUID(as_uuid=True), ForeignKey('operators.id'), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(100), nullable=False)  # aircraft type/model
    seats = Column(Integer, nullable=False)
    pets_allowed = Column(Boolean, default=False)
    ground_time_price_usd = Column(Float, nullable=True)
    product_link = Column(Text, nullable=True)
    external_ref = Column(String(50), nullable=True)  # for Excel mapping
    ics_url = Column(String(500), nullable=True)  # Calendar ICS URL
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    operator = relationship("Operator", back_populates="aircraft")
    
    __table_args__ = (
        UniqueConstraint('operator_id', 'name', name='_operator_aircraft_name_uc'),
        Index('idx_aircraft_operator', 'operator_id'),
        Index('idx_aircraft_type', 'type'),
    )

class Route(Base):
    __tablename__ = "routes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    origin_id = Column(UUID(as_uuid=True), ForeignKey('airports.id'), nullable=False)
    destination_id = Column(UUID(as_uuid=True), ForeignKey('airports.id'), nullable=False)
    typical_duration_min = Column(Integer, nullable=True)
    distance_km = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    origin = relationship("Airport", foreign_keys=[origin_id])
    destination = relationship("Airport", foreign_keys=[destination_id])
    
    __table_args__ = (
        UniqueConstraint('origin_id', 'destination_id', name='_origin_destination_uc'),
        Index('idx_route_origin_dest', 'origin_id', 'destination_id'),
    )

class Listing(Base):
    __tablename__ = "listings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operator_id = Column(UUID(as_uuid=True), ForeignKey('operators.id'), nullable=False)
    aircraft_id = Column(UUID(as_uuid=True), ForeignKey('aircraft.id'), nullable=False)
    route_id = Column(UUID(as_uuid=True), ForeignKey('routes.id'), nullable=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default='ACTIVE')  # ACTIVE, INACTIVE, SUSPENDED
    departure_days = Column(String(100), nullable=True)  # JSON or comma-separated
    max_load_weight_lbs = Column(Float, nullable=True)
    listing_type = Column(String(20), default='REGULAR')  # REGULAR, EMPTY_LEG
    external_ref = Column(String(100), nullable=True)  # for Excel mapping
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    operator = relationship("Operator")
    aircraft = relationship("Aircraft")
    route = relationship("Route")
    
    __table_args__ = (
        Index('idx_listing_operator', 'operator_id'),
        Index('idx_listing_aircraft', 'aircraft_id'),
        Index('idx_listing_route', 'route_id'),
        Index('idx_listing_status', 'status'),
    )

class PriceBook(Base):
    __tablename__ = "pricebook"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operator_id = Column(UUID(as_uuid=True), ForeignKey('operators.id'), nullable=True)
    aircraft_type = Column(String(100), nullable=True)
    origin_id = Column(UUID(as_uuid=True), ForeignKey('airports.id'), nullable=False)
    destination_id = Column(UUID(as_uuid=True), ForeignKey('airports.id'), nullable=False)
    base_price = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    price_per_min = Column(Float, nullable=True)
    effective_from = Column(DateTime(timezone=True), server_default=func.now())
    effective_to = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    operator = relationship("Operator")
    origin = relationship("Airport", foreign_keys=[origin_id])
    destination = relationship("Airport", foreign_keys=[destination_id])
    
    __table_args__ = (
        Index('idx_pricebook_route_type', 'origin_id', 'destination_id', 'aircraft_type'),
        Index('idx_pricebook_operator', 'operator_id'),
        Index('idx_pricebook_effective', 'effective_from', 'effective_to'),
    )

class Surcharge(Base):
    __tablename__ = "surcharges"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    amount_type = Column(String(20), default='FIXED')  # FIXED, PERCENTAGE
    amount = Column(Float, nullable=False)
    applies_to = Column(String(50), nullable=True)  # aircraft_type, operator, route
    conditions = Column(JSON, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Tax(Base):
    __tablename__ = "taxes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)  # e.g., ITBMS
    rate = Column(Float, nullable=False)  # percentage rate
    applies_to_base = Column(Boolean, default=True)
    applies_to_surcharges = Column(Boolean, default=False)
    country = Column(String(2), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Quote(Base):
    __tablename__ = "quotes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey('listings.id'), nullable=False)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    passengers = Column(Integer, nullable=False, default=1)
    departure_date = Column(DateTime(timezone=True), nullable=True)
    return_date = Column(DateTime(timezone=True), nullable=True)
    trip_type = Column(String(20), default='ONE_WAY')  # ONE_WAY, ROUND_TRIP
    
    # Pricing breakdown
    base_price = Column(Float, nullable=False)
    surcharges = Column(Float, default=0)
    taxes = Column(Float, default=0)
    service_fee = Column(Float, default=0)
    total_price = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    
    # Quote metadata
    status = Column(String(20), default='DRAFT')  # DRAFT, SENT, EXPIRED, CONVERTED
    expires_at = Column(DateTime(timezone=True), nullable=True)
    hosted_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    listing = relationship("Listing")

class Hold(Base):
    __tablename__ = "holds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aircraft_id = Column(UUID(as_uuid=True), ForeignKey('aircraft.id'), nullable=False)
    quote_id = Column(UUID(as_uuid=True), ForeignKey('quotes.id'), nullable=True)
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default='ACTIVE')  # ACTIVE, RELEASED, EXPIRED, CONVERTED
    redis_key = Column(String(200), nullable=False)  # Redis lock key
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    aircraft = relationship("Aircraft")
    quote = relationship("Quote")

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id = Column(UUID(as_uuid=True), ForeignKey('quotes.id'), nullable=False)
    hold_id = Column(UUID(as_uuid=True), ForeignKey('holds.id'), nullable=True)
    
    # Customer info
    customer_name = Column(String(200), nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_phone = Column(String(50), nullable=True)
    
    # Booking details
    confirmation_code = Column(String(20), unique=True, nullable=False)
    status = Column(String(20), default='PENDING')  # PENDING, CONFIRMED, PAID, CANCELLED
    
    # Payment info
    payment_method = Column(String(50), nullable=True)
    payment_reference = Column(String(200), nullable=True)
    paid_amount = Column(Float, nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    quote = relationship("Quote")
    hold = relationship("Hold")

class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aircraft_id = Column(UUID(as_uuid=True), ForeignKey('aircraft.id'), nullable=False)
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    slot_type = Column(String(20), default='AVAILABLE')  # AVAILABLE, MAINTENANCE, BLOCKED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    aircraft = relationship("Aircraft")
    
    __table_args__ = (
        Index('idx_availability_aircraft_date', 'aircraft_id', 'start_datetime', 'end_datetime'),
    )

class BusyBlock(Base):
    __tablename__ = "busy_blocks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aircraft_id = Column(UUID(as_uuid=True), ForeignKey('aircraft.id'), nullable=False)
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    source = Column(String(20), default='ICS')  # ICS, MANUAL, BOOKING
    external_event_id = Column(String(200), nullable=True)
    title = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    aircraft = relationship("Aircraft")
    
    __table_args__ = (
        Index('idx_busy_block_aircraft_date', 'aircraft_id', 'start_datetime', 'end_datetime'),
    )

class MessageLog(Base):
    __tablename__ = "message_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(String(200), unique=True, nullable=False)  # External message ID
    direction = Column(String(20), nullable=False)  # OUTBOUND, INBOUND
    channel = Column(String(50), default='WHATSAPP')
    phone_number = Column(String(50), nullable=False)
    message_type = Column(String(50), nullable=True)  # template, text, media
    content = Column(Text, nullable=True)
    template_name = Column(String(100), nullable=True)
    status = Column(String(50), nullable=True)  # sent, delivered, read, failed
    booking_id = Column(UUID(as_uuid=True), ForeignKey('bookings.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    booking = relationship("Booking")

class ImportRun(Base):
    __tablename__ = "import_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_type = Column(String(50), nullable=False)  # operators, aircraft, flights, etc.
    filename = Column(String(500), nullable=False)
    status = Column(String(20), default='RUNNING')  # RUNNING, COMPLETED, FAILED
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    success_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    summary = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

class ImportError(Base):
    __tablename__ = "import_errors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_run_id = Column(UUID(as_uuid=True), ForeignKey('import_runs.id'), nullable=False)
    row_number = Column(Integer, nullable=False)
    error_type = Column(String(100), nullable=False)
    error_message = Column(Text, nullable=False)
    row_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    import_run = relationship("ImportRun")

# Pydantic Models for API
class AirportSchema(BaseModel):
    id: Optional[str] = None
    code: str
    name: str
    city: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: str = 'America/Panama'

class OperatorSchema(BaseModel):
    id: Optional[str] = None
    code: Optional[str] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    base_airport_id: Optional[str] = None
    payout_info: Optional[Dict[str, Any]] = None
    flags: Optional[Dict[str, Any]] = None

class AircraftSchema(BaseModel):
    id: Optional[str] = None
    operator_id: str
    name: str
    type: str
    seats: int
    pets_allowed: bool = False
    ground_time_price_usd: Optional[float] = None
    product_link: Optional[str] = None
    external_ref: Optional[str] = None
    ics_url: Optional[str] = None

class RouteSchema(BaseModel):
    id: Optional[str] = None
    origin_id: str
    destination_id: str
    typical_duration_min: Optional[int] = None
    distance_km: Optional[float] = None
    notes: Optional[str] = None

class ListingSchema(BaseModel):
    id: Optional[str] = None
    operator_id: str
    aircraft_id: str
    route_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str = 'ACTIVE'
    departure_days: Optional[str] = None
    max_load_weight_lbs: Optional[float] = None
    listing_type: str = 'REGULAR'
    external_ref: Optional[str] = None

class PriceBookSchema(BaseModel):
    id: Optional[str] = None
    operator_id: Optional[str] = None
    aircraft_type: Optional[str] = None
    origin_id: str
    destination_id: str
    base_price: float
    currency: str = 'USD'
    price_per_min: Optional[float] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None

class QuoteRequest(BaseModel):
    listing_id: str
    passengers: int = 1
    departure_date: Optional[datetime] = None
    return_date: Optional[datetime] = None
    trip_type: str = 'ONE_WAY'
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None

class QuoteResponse(BaseModel):
    id: str
    base_price: float
    surcharges: float
    taxes: float
    service_fee: float
    total_price: float
    currency: str
    expires_at: Optional[datetime] = None
    hosted_url: Optional[str] = None

class ImportRunResponse(BaseModel):
    id: str
    import_type: str
    filename: str
    status: str
    total_rows: int
    processed_rows: int
    success_rows: int
    error_rows: int
    summary: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

# Status Enums
class BookingStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"

class QuoteStatus(str, Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    EXPIRED = "EXPIRED"
    CONVERTED = "CONVERTED"

class HoldStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"
    CONVERTED = "CONVERTED"