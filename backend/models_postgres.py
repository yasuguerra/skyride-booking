"""
SQLAlchemy Models for PostgreSQL
Equivalent to MongoDB collections with proper relationships
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Index, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum
from database_postgres import Base

# Enums
class ListingType(str, enum.Enum):
    CHARTER = "CHARTER"
    EMPTY_LEG = "EMPTY_LEG"
    SEAT = "SEAT"

class ListingStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SOLD_OUT = "SOLD_OUT"
    EXPIRED = "EXPIRED"

class QuoteStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CONVERTED = "CONVERTED"
    ABANDONED = "ABANDONED"

class HoldStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CONVERTED = "CONVERTED"
    CANCELLED = "CANCELLED"

class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class PaymentProvider(str, enum.Enum):
    WOMPI = "WOMPI"
    YAPPY = "YAPPY"
    MANUAL = "MANUAL"

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PAID = "PAID"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"

class MessageChannel(str, enum.Enum):
    WHATSAPP = "WHATSAPP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    SYSTEM = "SYSTEM"

class MessageDirection(str, enum.Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"

class MessageStatus(str, enum.Enum):
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    FAILED = "FAILED"
    PENDING = "PENDING"

class SlotStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    MAINTENANCE = "MAINTENANCE"

class SlotSource(str, enum.Enum):
    PORTAL = "PORTAL"
    ICS = "ICS"
    GOOGLE = "GOOGLE"

# Models
class Operator(Base):
    __tablename__ = "operators"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)
    logo = Column(String(500), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    
    # SaaS settings
    distribution_opt_in = Column(Boolean, default=False, nullable=False)
    price_floor = Column(Float, nullable=True)
    empty_leg_window = Column(Integer, nullable=True)  # minutes
    
    # Score metrics
    acceptance_rate = Column(Float, default=0.0, nullable=False)
    avg_response_time = Column(Integer, default=0, nullable=False)  # seconds
    cancellation_rate = Column(Float, default=0.0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    aircraft = relationship("Aircraft", back_populates="operator", cascade="all, delete-orphan")
    listings = relationship("Listing", back_populates="operator")
    bookings = relationship("Booking", back_populates="operator")
    
    __table_args__ = (
        Index("idx_operators_active_code", "active", "code"),
    )

class Aircraft(Base):
    __tablename__ = "aircraft"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operator_id = Column(UUID(as_uuid=True), ForeignKey("operators.id"), nullable=False)
    model = Column(String(255), nullable=False)
    registration = Column(String(50), unique=True, nullable=False, index=True)
    capacity = Column(Integer, nullable=False)
    hourly_rate = Column(Float, nullable=True)
    images = Column(ARRAY(String), default=[])
    active = Column(Boolean, default=True, nullable=False)
    
    # ICS Calendar import (optional)
    ics_url = Column(String(500), nullable=True)
    ics_last_sync = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    operator = relationship("Operator", back_populates="aircraft")
    listings = relationship("Listing", back_populates="aircraft")
    availability_slots = relationship("AvailabilitySlot", back_populates="aircraft")
    busy_blocks = relationship("BusyBlock", back_populates="aircraft")
    
    __table_args__ = (
        Index("idx_aircraft_operator_active", "operator_id", "active"),
    )

class Route(Base):
    __tablename__ = "routes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    origin = Column(String(255), nullable=False, index=True)
    destination = Column(String(255), nullable=False, index=True)
    distance = Column(Float, nullable=True)  # nautical miles
    duration = Column(Integer, nullable=True)  # minutes
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    listings = relationship("Listing", back_populates="route")
    
    __table_args__ = (
        Index("idx_routes_origin_destination", "origin", "destination"),
    )

class Listing(Base):
    __tablename__ = "listings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operator_id = Column(UUID(as_uuid=True), ForeignKey("operators.id"), nullable=False)
    aircraft_id = Column(UUID(as_uuid=True), ForeignKey("aircraft.id"), nullable=False)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    
    type = Column(SQLEnum(ListingType), default=ListingType.CHARTER, nullable=False)
    status = Column(SQLEnum(ListingStatus), default=ListingStatus.ACTIVE, nullable=False)
    
    # Pricing
    base_price = Column(Float, nullable=False)
    service_fee = Column(Float, default=0.0, nullable=False)
    price_per_seat = Column(Float, nullable=True)  # For SEAT type
    total_price = Column(Float, nullable=False)  # base_price + service_fee
    
    # Availability
    available_from = Column(DateTime(timezone=True), nullable=True)
    available_to = Column(DateTime(timezone=True), nullable=True)
    max_passengers = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=True)  # For SEAT/EMPTY_LEG
    
    # Charter specific
    confirmation_sla = Column(Integer, nullable=True)  # hours
    
    # Empty Leg specific  
    flexible_window = Column(Integer, nullable=True)  # minutes
    departure_window = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    amenities = Column(ARRAY(String), default=[])
    images = Column(ARRAY(String), default=[])
    featured = Column(Boolean, default=False, nullable=False)
    boosted = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    operator = relationship("Operator", back_populates="listings")
    aircraft = relationship("Aircraft", back_populates="listings")
    route = relationship("Route", back_populates="listings")
    quotes = relationship("Quote", back_populates="listing")
    
    __table_args__ = (
        Index("idx_listings_status_type", "status", "type"),
        Index("idx_listings_featured_boosted", "featured", "boosted"),
    )

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    
    # Personal info
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)  # Computed field
    
    # Legal identification
    legal_id = Column(String(50), nullable=True)
    legal_id_type = Column(String(10), nullable=True)
    
    # Address information
    address_line_1 = Column(String(255), nullable=True)
    address_line_2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    country = Column(String(2), default="PA")
    postal_code = Column(String(10), nullable=True)
    
    # Preferences
    preferred_language = Column(String(5), default="en")
    marketing_opt_in = Column(Boolean, default=False, nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    quotes = relationship("Quote", back_populates="customer")
    bookings = relationship("Booking", back_populates="customer")
    messages = relationship("MessageLog", back_populates="customer")

class Quote(Base):
    __tablename__ = "quotes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(100), unique=True, nullable=False, index=True)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    
    # Quote details
    passengers = Column(Integer, nullable=False)
    departure_date = Column(DateTime(timezone=True), nullable=False)
    return_date = Column(DateTime(timezone=True), nullable=True)
    
    # Pricing breakdown
    base_price = Column(Float, nullable=False)
    service_fee = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Status & timing
    status = Column(SQLEnum(QuoteStatus), default=QuoteStatus.ACTIVE, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    lead_id = Column(String(100), nullable=True)  # External lead tracking
    source = Column(String(50), nullable=True)  # "web", "whatsapp", "api"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    listing = relationship("Listing", back_populates="quotes")
    customer = relationship("Customer", back_populates="quotes")
    holds = relationship("Hold", back_populates="quote")
    bookings = relationship("Booking", back_populates="quote")
    events = relationship("EventLog", back_populates="quote")
    
    __table_args__ = (
        Index("idx_quotes_status_expires", "status", "expires_at"),
        Index("idx_quotes_token_status", "token", "status"),
    )

class Hold(Base):
    __tablename__ = "holds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id"), nullable=False)
    
    # Hold details
    deposit_amount = Column(Float, nullable=True)
    status = Column(SQLEnum(HoldStatus), default=HoldStatus.ACTIVE, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Payment info
    deposit_paid = Column(Boolean, default=False, nullable=False)
    deposit_paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    quote = relationship("Quote", back_populates="holds")
    booking = relationship("Booking", back_populates="hold", uselist=False)
    
    __table_args__ = (
        Index("idx_holds_status_expires", "status", "expires_at"),
    )

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id"), nullable=False)
    operator_id = Column(UUID(as_uuid=True), ForeignKey("operators.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    hold_id = Column(UUID(as_uuid=True), ForeignKey("holds.id"), nullable=True)
    
    # Booking details
    booking_number = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    
    # Pricing
    total_amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0, nullable=False)
    
    # Dates
    departure_date = Column(DateTime(timezone=True), nullable=False)
    return_date = Column(DateTime(timezone=True), nullable=True)
    
    # Payment timing
    payment_due = Column(DateTime(timezone=True), nullable=True)
    fully_paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    booking_metadata = Column(JSON, nullable=True)  # Changed from 'metadata'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    quote = relationship("Quote", back_populates="bookings")
    operator = relationship("Operator", back_populates="bookings")
    customer = relationship("Customer", back_populates="bookings")
    hold = relationship("Hold", back_populates="booking")
    payments = relationship("Payment", back_populates="booking")
    events = relationship("EventLog", back_populates="booking")
    
    __table_args__ = (
        Index("idx_bookings_status_date", "status", "departure_date"),
        Index("idx_bookings_number", "booking_number"),
    )

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)
    
    # Payment details
    provider = Column(SQLEnum(PaymentProvider), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    
    # Provider specific data
    external_id = Column(String(255), nullable=True, index=True)  # Wompi/Yappy transaction ID
    payment_link_url = Column(String(1000), nullable=True)
    webhook_payload = Column(JSON, nullable=True)
    
    # Additional information
    description = Column(String(500), nullable=True)
    failure_reason = Column(String(500), nullable=True)
    
    # Timing
    paid_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    expired_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    booking = relationship("Booking", back_populates="payments")
    webhook_events = relationship("WebhookEvent", back_populates="payment")
    
    __table_args__ = (
        Index("idx_payments_status_date", "status", "created_at"),
        Index("idx_payments_external_id", "external_id"),
    )

class MessageLog(Base):
    __tablename__ = "message_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    
    # Message details
    channel = Column(SQLEnum(MessageChannel), nullable=False)
    direction = Column(SQLEnum(MessageDirection), nullable=False)
    template = Column(String(100), nullable=True)  # Template name for outbound
    content = Column(Text, nullable=True)  # Message content
    
    # WhatsApp specific
    wa_id = Column(String(100), nullable=True)  # WhatsApp ID
    message_id = Column(String(255), nullable=True, index=True)  # External message ID
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.SENT, nullable=False)
    
    # Context
    quote_id = Column(UUID(as_uuid=True), nullable=True)
    booking_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Metadata
    message_metadata = Column(JSON, nullable=True)  # Changed from 'metadata'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    customer = relationship("Customer", back_populates="messages")
    
    __table_args__ = (
        Index("idx_messages_channel_direction", "channel", "direction"),
        Index("idx_messages_status_date", "status", "created_at"),
    )

class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=True)
    
    # Webhook data
    event_type = Column(String(100), nullable=False, index=True)
    external_event_id = Column(String(255), nullable=True, index=True)  # Wompi event ID
    payload = Column(JSON, nullable=False)
    signature = Column(String(500), nullable=False)
    
    # Processing status
    processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processing_error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    external_created_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    payment = relationship("Payment", back_populates="webhook_events")
    
    __table_args__ = (
        Index("idx_webhooks_processed_date", "processed", "received_at"),
        Index("idx_webhooks_event_type", "event_type"),
    )

class EventLog(Base):
    __tablename__ = "event_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event details
    event = Column(String(100), nullable=False, index=True)  # e.g., "quote_viewed", "hold_created"
    entity = Column(String(50), nullable=False)  # e.g., "quote", "booking"
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Context
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id"), nullable=True)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Event data
    data = Column(JSON, nullable=True)
    
    # GA4 tracking
    session_id = Column(String(100), nullable=True)
    client_id = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    quote = relationship("Quote", back_populates="events")
    booking = relationship("Booking", back_populates="events")
    
    __table_args__ = (
        Index("idx_events_entity", "entity", "entity_id"),
        Index("idx_events_date", "created_at"),
    )

# New Availability Models
class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aircraft_id = Column(UUID(as_uuid=True), ForeignKey("aircraft.id"), nullable=False)
    
    # Slot details
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(SQLEnum(SlotStatus), default=SlotStatus.AVAILABLE, nullable=False)
    source = Column(SQLEnum(SlotSource), default=SlotSource.PORTAL, nullable=False)
    
    # Metadata
    notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)  # Operator user ID
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    aircraft = relationship("Aircraft", back_populates="availability_slots")
    
    __table_args__ = (
        Index("idx_slots_aircraft_time", "aircraft_id", "start_time", "end_time"),
        Index("idx_slots_status_source", "status", "source"),
    )

class BusyBlock(Base):
    __tablename__ = "busy_blocks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aircraft_id = Column(UUID(as_uuid=True), ForeignKey("aircraft.id"), nullable=False)
    
    # Block details
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    source = Column(SQLEnum(SlotSource), nullable=False)
    
    # External reference
    external_id = Column(String(255), nullable=True)  # ICS event UID, Google event ID
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    aircraft = relationship("Aircraft", back_populates="busy_blocks")
    
    __table_args__ = (
        Index("idx_busy_blocks_aircraft_time", "aircraft_id", "start_time", "end_time"),
        Index("idx_busy_blocks_external_id", "external_id"),
    )

# PriceBook Models for dynamic pricing
class PriceBook(Base):
    __tablename__ = "price_books"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    
    # Effective dates
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    
    # Configuration
    base_currency = Column(String(3), default="USD", nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    surcharges = relationship("Surcharge", back_populates="price_book")
    overrides = relationship("PriceOverride", back_populates="price_book")

class Surcharge(Base):
    __tablename__ = "surcharges"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    price_book_id = Column(UUID(as_uuid=True), ForeignKey("price_books.id"), nullable=False)
    
    # Surcharge details
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    type = Column(String(20), nullable=False)  # 'FIXED', 'PERCENTAGE'
    amount = Column(Float, nullable=False)
    
    # Conditions
    aircraft_type = Column(String(100), nullable=True)
    route_pattern = Column(String(255), nullable=True)  # regex pattern
    min_passengers = Column(Integer, nullable=True)
    max_passengers = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    price_book = relationship("PriceBook", back_populates="surcharges")

class PriceOverride(Base):
    __tablename__ = "price_overrides"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    price_book_id = Column(UUID(as_uuid=True), ForeignKey("price_books.id"), nullable=False)
    
    # Override details
    aircraft_id = Column(UUID(as_uuid=True), ForeignKey("aircraft.id"), nullable=True)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=True)
    override_price = Column(Float, nullable=False)
    
    # Effective dates
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    price_book = relationship("PriceBook", back_populates="overrides")

class Policy(Base):
    __tablename__ = "policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False, index=True)  # "cancellation", "protection", "terms"
    content = Column(Text, nullable=False)  # HTML content
    version = Column(String(20), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index("idx_policies_type_active", "type", "active"),
    )