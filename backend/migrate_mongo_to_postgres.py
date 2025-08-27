#!/usr/bin/env python3
"""
Migration Script: MongoDB to PostgreSQL
Migrates existing MongoDB data to PostgreSQL with SQLAlchemy models
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
import uuid
import logging

# Add current directory to Python path
sys.path.append(os.path.dirname(__file__))

from database_postgres import async_session_factory, init_db, DATABASE_URL
from models_postgres import (
    Operator, Aircraft, Route, Listing, Customer, Quote, Hold, 
    Booking, Payment, MessageLog, EventLog, Policy, WebhookEvent
)

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoToPostgresMigrator:
    def __init__(self):
        # MongoDB connection
        self.mongo_client = AsyncIOMotorClient(os.environ['MONGO_URL'])
        self.mongo_db = self.mongo_client[os.environ['DB_NAME']]
        
        # PostgreSQL connection will use the session factory
        logger.info(f"PostgreSQL URL: {DATABASE_URL}")
        
    async def migrate_all(self):
        """Run complete migration from MongoDB to PostgreSQL"""
        logger.info("🚀 Starting MongoDB to PostgreSQL migration...")
        
        # Initialize PostgreSQL tables
        logger.info("📊 Initializing PostgreSQL database...")
        await init_db()
        
        async with async_session_factory() as session:
            try:
                # Migration order matters due to foreign key constraints
                await self.migrate_operators(session)
                await self.migrate_aircraft(session)
                await self.migrate_routes(session)
                await self.migrate_customers(session)
                await self.migrate_listings(session)
                await self.migrate_quotes(session)
                await self.migrate_holds(session)
                await self.migrate_bookings(session)
                await self.migrate_payments(session)
                await self.migrate_policies(session)
                await self.migrate_message_logs(session)
                await self.migrate_event_logs(session)
                await self.migrate_webhook_events(session)
                
                await session.commit()
                logger.info("✅ Migration completed successfully!")
                
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Migration failed: {e}")
                raise
                
    async def migrate_operators(self, session: AsyncSession):
        """Migrate operators collection"""
        logger.info("👥 Migrating operators...")
        
        cursor = self.mongo_db.operators.find({})
        count = 0
        
        async for doc in cursor:
            operator = Operator(
                id=uuid.UUID(doc['_id']) if self._is_uuid(doc['_id']) else uuid.uuid4(),
                name=doc.get('name', ''),
                code=doc.get('code', ''),
                email=doc.get('email', ''),
                phone=doc.get('phone'),
                website=doc.get('website'),
                logo=doc.get('logo'),
                active=doc.get('active', True),
                distribution_opt_in=doc.get('distributionOptIn', False),
                price_floor=doc.get('priceFloor'),
                empty_leg_window=doc.get('emptyLegWindow'),
                acceptance_rate=doc.get('acceptanceRate', 0.0),
                avg_response_time=doc.get('avgResponseTime', 0),
                cancellation_rate=doc.get('cancelationRate', 0.0),
                created_at=self._parse_datetime(doc.get('createdAt')),
                updated_at=self._parse_datetime(doc.get('updatedAt'))
            )
            session.add(operator)
            count += 1
            
        logger.info(f"   ✅ Migrated {count} operators")
        
    async def migrate_aircraft(self, session: AsyncSession):
        """Migrate aircraft collection"""
        logger.info("✈️ Migrating aircraft...")
        
        cursor = self.mongo_db.aircraft.find({})
        count = 0
        
        async for doc in cursor:
            aircraft = Aircraft(
                id=uuid.UUID(doc['_id']) if self._is_uuid(doc['_id']) else uuid.uuid4(),
                operator_id=uuid.UUID(doc['operatorId']) if self._is_uuid(doc['operatorId']) else (await self._get_first_operator_id(session)),
                model=doc.get('model', ''),
                registration=doc.get('registration', ''),
                capacity=doc.get('capacity', 1),
                hourly_rate=doc.get('hourlyRate'),
                images=doc.get('images', []),
                active=doc.get('active', True),
                ics_url=None,  # New field for ICS calendar
                ics_last_sync=None,
                created_at=self._parse_datetime(doc.get('createdAt')),
                updated_at=self._parse_datetime(doc.get('updatedAt'))
            )
            session.add(aircraft)
            count += 1
            
        logger.info(f"   ✅ Migrated {count} aircraft")
        
    async def migrate_routes(self, session: AsyncSession):
        """Migrate routes collection"""
        logger.info("🗺️ Migrating routes...")
        
        cursor = self.mongo_db.routes.find({})
        count = 0
        
        async for doc in cursor:
            route = Route(
                id=uuid.UUID(doc['_id']) if self._is_uuid(doc['_id']) else uuid.uuid4(),
                origin=doc.get('origin', ''),
                destination=doc.get('destination', ''),
                distance=doc.get('distance'),
                duration=doc.get('duration'),
                created_at=self._parse_datetime(doc.get('createdAt')),
                updated_at=self._parse_datetime(doc.get('updatedAt'))
            )
            session.add(route)
            count += 1
            
        logger.info(f"   ✅ Migrated {count} routes")
        
    async def migrate_customers(self, session: AsyncSession):
        """Migrate customers collection"""
        logger.info("👤 Migrating customers...")
        
        cursor = self.mongo_db.customers.find({})
        count = 0
        
        async for doc in cursor:
            customer = Customer(
                id=uuid.UUID(doc['_id']) if self._is_uuid(doc['_id']) else uuid.uuid4(),
                email=doc.get('email', ''),
                phone=doc.get('phone'),
                first_name=doc.get('firstName'),
                last_name=doc.get('lastName'),
                full_name=doc.get('full_name') or f"{doc.get('firstName', '')} {doc.get('lastName', '')}".strip(),
                legal_id=doc.get('legal_id'),
                legal_id_type=doc.get('legal_id_type'),
                preferred_language=doc.get('preferredLanguage', 'en'),
                marketing_opt_in=doc.get('marketingOptIn', False),
                is_active=True,
                created_at=self._parse_datetime(doc.get('createdAt')),
                updated_at=self._parse_datetime(doc.get('updatedAt'))
            )
            session.add(customer)
            count += 1
            
        logger.info(f"   ✅ Migrated {count} customers")
        
    async def migrate_listings(self, session: AsyncSession):
        """Migrate listings collection"""
        logger.info("📋 Migrating listings...")
        
        cursor = self.mongo_db.listings.find({})
        count = 0
        
        async for doc in cursor:
            listing = Listing(
                id=uuid.UUID(doc['_id']) if self._is_uuid(doc['_id']) else uuid.uuid4(),
                operator_id=uuid.UUID(doc['operatorId']) if self._is_uuid(doc['operatorId']) else (await self._get_first_operator_id(session)),
                aircraft_id=uuid.UUID(doc['aircraftId']) if self._is_uuid(doc['aircraftId']) else (await self._get_first_aircraft_id(session)),
                route_id=uuid.UUID(doc['routeId']) if self._is_uuid(doc['routeId']) else (await self._get_first_route_id(session)),
                type=doc.get('type', 'CHARTER'),
                status=doc.get('status', 'ACTIVE'),
                base_price=doc.get('basePrice', 0.0),
                service_fee=doc.get('serviceFee', 0.0),
                price_per_seat=doc.get('pricePerSeat'),
                total_price=doc.get('totalPrice', 0.0),
                available_from=self._parse_datetime(doc.get('availableFrom')),
                available_to=self._parse_datetime(doc.get('availableTo')),
                max_passengers=doc.get('maxPassengers', 1),
                available_seats=doc.get('availableSeats'),
                confirmation_sla=doc.get('confirmationSLA'),
                flexible_window=doc.get('flexibleWindow'),
                departure_window=self._parse_datetime(doc.get('departureWindow')),
                title=doc.get('title'),
                description=doc.get('description'),
                amenities=doc.get('amenities', []),
                images=doc.get('images', []),
                featured=doc.get('featured', False),
                boosted=doc.get('boosted', False),
                created_at=self._parse_datetime(doc.get('createdAt')),
                updated_at=self._parse_datetime(doc.get('updatedAt'))
            )
            session.add(listing)
            count += 1
            
        logger.info(f"   ✅ Migrated {count} listings")
        
    async def migrate_quotes(self, session: AsyncSession):
        """Migrate quotes collection"""
        logger.info("💬 Migrating quotes...")
        
        cursor = self.mongo_db.quotes.find({})
        count = 0
        
        async for doc in cursor:
            quote = Quote(
                id=uuid.UUID(doc['_id']) if self._is_uuid(doc['_id']) else uuid.uuid4(),
                token=doc.get('token', ''),
                listing_id=uuid.UUID(doc['listingId']) if self._is_uuid(doc['listingId']) else (await self._get_first_listing_id(session)),
                customer_id=uuid.UUID(doc['customerId']) if doc.get('customerId') and self._is_uuid(doc['customerId']) else None,
                passengers=doc.get('passengers', 1),
                departure_date=self._parse_datetime(doc.get('departureDate')),
                return_date=self._parse_datetime(doc.get('returnDate')),
                base_price=doc.get('basePrice', 0.0),
                service_fee=doc.get('serviceFee', 0.0),
                total_price=doc.get('totalPrice', 0.0),
                status=doc.get('status', 'ACTIVE'),
                expires_at=self._parse_datetime(doc.get('expiresAt')),
                viewed_at=self._parse_datetime(doc.get('viewedAt')),
                lead_id=doc.get('leadId'),
                source=doc.get('source'),
                created_at=self._parse_datetime(doc.get('createdAt')),
                updated_at=self._parse_datetime(doc.get('updatedAt'))
            )
            session.add(quote)
            count += 1
            
        logger.info(f"   ✅ Migrated {count} quotes")
        
    async def migrate_holds(self, session: AsyncSession):
        """Migrate holds collection"""
        logger.info("⏰ Migrating holds...")
        
        cursor = self.mongo_db.holds.find({})
        count = 0
        
        async for doc in cursor:
            hold = Hold(
                id=uuid.UUID(doc['_id']) if self._is_uuid(doc['_id']) else uuid.uuid4(),
                quote_id=uuid.UUID(doc['quoteId']) if self._is_uuid(doc['quoteId']) else (await self._get_first_quote_id(session)),
                deposit_amount=doc.get('depositAmount'),
                status=doc.get('status', 'ACTIVE'),
                expires_at=self._parse_datetime(doc.get('expiresAt')),
                deposit_paid=doc.get('depositPaid', False),
                deposit_paid_at=self._parse_datetime(doc.get('depositPaidAt')),
                created_at=self._parse_datetime(doc.get('createdAt')),
                updated_at=self._parse_datetime(doc.get('updatedAt'))
            )
            session.add(hold)
            count += 1
            
        logger.info(f"   ✅ Migrated {count} holds")
        
    async def migrate_bookings(self, session: AsyncSession):
        """Migrate bookings collection"""
        logger.info("📅 Migrating bookings...")
        
        cursor = self.mongo_db.bookings.find({})
        count = 0
        
        async for doc in cursor:
            booking = Booking(
                id=uuid.UUID(doc['_id']) if self._is_uuid(doc['_id']) else uuid.uuid4(),
                quote_id=uuid.UUID(doc['quoteId']) if self._is_uuid(doc['quoteId']) else (await self._get_first_quote_id(session)),
                operator_id=uuid.UUID(doc['operatorId']) if self._is_uuid(doc['operatorId']) else (await self._get_first_operator_id(session)),
                customer_id=uuid.UUID(doc['customerId']) if doc.get('customerId') and self._is_uuid(doc['customerId']) else None,
                hold_id=uuid.UUID(doc['holdId']) if doc.get('holdId') and self._is_uuid(doc['holdId']) else None,
                booking_number=doc.get('bookingNumber', ''),
                status=doc.get('status', 'PENDING'),
                total_amount=doc.get('totalAmount', 0.0),
                paid_amount=doc.get('paidAmount', 0.0),
                departure_date=self._parse_datetime(doc.get('departureDate')),
                return_date=self._parse_datetime(doc.get('returnDate')),
                payment_due=self._parse_datetime(doc.get('paymentDue')),
                fully_paid_at=self._parse_datetime(doc.get('fullyPaidAt')),
                notes=doc.get('notes'),
                internal_notes=doc.get('internalNotes'),
                booking_metadata=doc.get('metadata'),  # Changed field name
                created_at=self._parse_datetime(doc.get('createdAt')),
                updated_at=self._parse_datetime(doc.get('updatedAt'))
            )
            session.add(booking)
            count += 1
            
        logger.info(f"   ✅ Migrated {count} bookings")
        
    async def migrate_payments(self, session: AsyncSession):
        """Migrate payments collection"""
        logger.info("💳 Migrating payments...")
        
        cursor = self.mongo_db.payments.find({})
        count = 0
        
        async for doc in cursor:
            payment = Payment(
                id=uuid.UUID(doc['_id']) if self._is_uuid(doc['_id']) else uuid.uuid4(),
                booking_id=uuid.UUID(doc['bookingId']) if self._is_uuid(doc['bookingId']) else (await self._get_first_booking_id(session)),
                provider=doc.get('provider', 'WOMPI'),
                amount=doc.get('amount', 0.0),
                currency=doc.get('currency', 'USD'),
                status=doc.get('status', 'PENDING'),
                external_id=doc.get('externalId'),
                payment_link_url=doc.get('paymentLinkUrl'),
                webhook_payload=doc.get('webhookPayload'),
                description=doc.get('description'),
                failure_reason=doc.get('failureReason'),
                paid_at=self._parse_datetime(doc.get('paidAt')),
                failed_at=self._parse_datetime(doc.get('failedAt')),
                expired_at=self._parse_datetime(doc.get('expiredAt')),
                created_at=self._parse_datetime(doc.get('createdAt')),
                updated_at=self._parse_datetime(doc.get('updatedAt'))
            )
            session.add(payment)
            count += 1
            
        logger.info(f"   ✅ Migrated {count} payments")
        
    async def migrate_policies(self, session: AsyncSession):
        """Migrate policies collection"""
        logger.info("📋 Migrating policies...")
        
        cursor = self.mongo_db.policies.find({})
        count = 0
        
        async for doc in cursor:
            policy = Policy(
                id=uuid.UUID(doc['_id']) if self._is_uuid(doc['_id']) else uuid.uuid4(),
                name=doc.get('name', ''),
                type=doc.get('type', ''),
                content=doc.get('content', ''),
                version=doc.get('version', '1.0'),
                active=doc.get('active', True),
                created_at=self._parse_datetime(doc.get('createdAt')),
                updated_at=self._parse_datetime(doc.get('updatedAt'))
            )
            session.add(policy)
            count += 1
            
        logger.info(f"   ✅ Migrated {count} policies")
        
    async def migrate_message_logs(self, session: AsyncSession):
        """Migrate message_logs collection"""
        logger.info("📱 Migrating message logs...")
        
        if 'message_logs' in await self.mongo_db.list_collection_names():
            cursor = self.mongo_db.message_logs.find({})
            count = 0
            
            async for doc in cursor:
                message_log = MessageLog(
                    id=uuid.UUID(doc['_id']) if self._is_uuid(doc['_id']) else uuid.uuid4(),
                    customer_id=uuid.UUID(doc['customerId']) if doc.get('customerId') and self._is_uuid(doc['customerId']) else None,
                    channel=doc.get('channel', 'SYSTEM'),
                    direction=doc.get('direction', 'OUTBOUND'),
                    template=doc.get('template'),
                    content=doc.get('content'),
                    wa_id=doc.get('waId'),
                    message_id=doc.get('messageId'),
                    status=doc.get('status', 'SENT'),
                    quote_id=uuid.UUID(doc['quoteId']) if doc.get('quoteId') and self._is_uuid(doc['quoteId']) else None,
                    booking_id=uuid.UUID(doc['bookingId']) if doc.get('bookingId') and self._is_uuid(doc['bookingId']) else None,
                    metadata=doc.get('metadata'),
                    created_at=self._parse_datetime(doc.get('createdAt')),
                    updated_at=self._parse_datetime(doc.get('updatedAt'))
                )
                session.add(message_log)
                count += 1
                
            logger.info(f"   ✅ Migrated {count} message logs")
        else:
            logger.info("   ℹ️ No message logs collection found")
        
    async def migrate_event_logs(self, session: AsyncSession):
        """Migrate event_logs collection"""
        logger.info("📊 Migrating event logs...")
        
        if 'event_logs' in await self.mongo_db.list_collection_names():
            cursor = self.mongo_db.event_logs.find({})
            count = 0
            
            async for doc in cursor:
                event_log = EventLog(
                    id=uuid.UUID(doc['_id']) if self._is_uuid(doc['_id']) else uuid.uuid4(),
                    event=doc.get('event', ''),
                    entity=doc.get('entity', ''),
                    entity_id=uuid.UUID(doc['entityId']) if self._is_uuid(doc['entityId']) else uuid.uuid4(),
                    quote_id=uuid.UUID(doc['quoteId']) if doc.get('quoteId') and self._is_uuid(doc['quoteId']) else None,
                    booking_id=uuid.UUID(doc['bookingId']) if doc.get('bookingId') and self._is_uuid(doc['bookingId']) else None,
                    customer_id=uuid.UUID(doc['customerId']) if doc.get('customerId') and self._is_uuid(doc['customerId']) else None,
                    data=doc.get('data'),
                    session_id=doc.get('sessionId'),
                    client_id=doc.get('clientId'),
                    created_at=self._parse_datetime(doc.get('createdAt'))
                )
                session.add(event_log)
                count += 1
                
            logger.info(f"   ✅ Migrated {count} event logs")
        else:
            logger.info("   ℹ️ No event logs collection found")
        
    async def migrate_webhook_events(self, session: AsyncSession):
        """Migrate webhook_events collection (if exists)"""
        logger.info("🔗 Migrating webhook events...")
        
        if 'webhook_events' in await self.mongo_db.list_collection_names():
            cursor = self.mongo_db.webhook_events.find({})
            count = 0
            
            async for doc in cursor:
                webhook_event = WebhookEvent(
                    id=uuid.UUID(doc['_id']) if self._is_uuid(doc['_id']) else uuid.uuid4(),
                    payment_id=uuid.UUID(doc['paymentTransactionId']) if doc.get('paymentTransactionId') and self._is_uuid(doc['paymentTransactionId']) else None,
                    event_type=doc.get('eventType', ''),
                    external_event_id=doc.get('wompiEventId'),
                    payload=doc.get('payload', {}),
                    signature=doc.get('signature', ''),
                    processed=doc.get('processed', False),
                    processed_at=self._parse_datetime(doc.get('processedAt')),
                    processing_error=doc.get('processingError'),
                    retry_count=doc.get('retryCount', 0),
                    received_at=self._parse_datetime(doc.get('receivedAt')),
                    external_created_at=self._parse_datetime(doc.get('wompiCreatedAt'))
                )
                session.add(webhook_event)
                count += 1
                
            logger.info(f"   ✅ Migrated {count} webhook events")
        else:
            logger.info("   ℹ️ No webhook events collection found")
            
    # Helper methods
    def _is_uuid(self, value):
        """Check if value is a valid UUID"""
        if not value:
            return False
        try:
            uuid.UUID(str(value))
            return True
        except (ValueError, TypeError):
            return False
            
    def _parse_datetime(self, value):
        """Parse datetime from various formats"""
        if not value:
            return None
        
        if isinstance(value, datetime):
            return value.replace(tzinfo=timezone.utc)
        
        if isinstance(value, str):
            try:
                # Try parsing ISO format
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                try:
                    # Try parsing without timezone
                    dt = datetime.fromisoformat(value)
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    logger.warning(f"Could not parse datetime: {value}")
                    return datetime.now(timezone.utc)
        
        return datetime.now(timezone.utc)
        
    async def _get_first_operator_id(self, session: AsyncSession):
        """Get first operator ID for foreign key constraints"""
        from sqlalchemy import select
        result = await session.execute(select(Operator.id).limit(1))
        operator_id = result.scalar_one_or_none()
        
        if not operator_id:
            # Create default operator if none exists
            default_operator = Operator(
                name="Default Operator",
                code="DEFAULT",
                email="admin@skyride.city",
                active=True
            )
            session.add(default_operator)
            await session.flush()
            return default_operator.id
            
        return operator_id
        
    async def _get_first_aircraft_id(self, session: AsyncSession):
        """Get first aircraft ID for foreign key constraints"""
        from sqlalchemy import select
        result = await session.execute(select(Aircraft.id).limit(1))
        aircraft_id = result.scalar_one_or_none()
        
        if not aircraft_id:
            # Create default aircraft if none exists
            operator_id = await self._get_first_operator_id(session)
            default_aircraft = Aircraft(
                operator_id=operator_id,
                model="Default Aircraft",
                registration="DEFAULT",
                capacity=4,
                active=True
            )
            session.add(default_aircraft)
            await session.flush()
            return default_aircraft.id
            
        return aircraft_id
        
    async def _get_first_route_id(self, session: AsyncSession):
        """Get first route ID for foreign key constraints"""
        from sqlalchemy import select
        result = await session.execute(select(Route.id).limit(1))
        route_id = result.scalar_one_or_none()
        
        if not route_id:
            # Create default route if none exists
            default_route = Route(
                origin="Default Origin",
                destination="Default Destination",
                distance=100,
                duration=60
            )
            session.add(default_route)
            await session.flush()
            return default_route.id
            
        return route_id
        
    async def _get_first_listing_id(self, session: AsyncSession):
        """Get first listing ID for foreign key constraints"""
        from sqlalchemy import select
        result = await session.execute(select(Listing.id).limit(1))
        return result.scalar_one_or_none()
        
    async def _get_first_quote_id(self, session: AsyncSession):
        """Get first quote ID for foreign key constraints"""
        from sqlalchemy import select
        result = await session.execute(select(Quote.id).limit(1))
        return result.scalar_one_or_none()
        
    async def _get_first_booking_id(self, session: AsyncSession):
        """Get first booking ID for foreign key constraints"""
        from sqlalchemy import select
        result = await session.execute(select(Booking.id).limit(1))
        return result.scalar_one_or_none()

async def main():
    """Run the migration"""
    migrator = MongoToPostgresMigrator()
    
    try:
        await migrator.migrate_all()
        logger.info("🎉 Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        # Close MongoDB connection
        migrator.mongo_client.close()

if __name__ == "__main__":
    asyncio.run(main())