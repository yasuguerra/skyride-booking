# SkyRide Booking Platform v2.0

**Production-ready charter flight booking system for Panama.**

## 🚀 Quick Start

### Local Development
```bash
# Backend
cd backend
cp .env.example .env
pip install -r requirements.txt
alembic upgrade head
python start_server.py

# Frontend  
cd frontend
npm install
npm start
```

### Production (Supabase)
```bash
# Set environment variables
export DATABASE_URL="postgresql://postgres.xxx:password@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
export DATABASE_URL_MIGRATIONS="postgresql://postgres.xxx:password@aws-0-us-west-1.pooler.supabase.com:5432/postgres?sslmode=require"

# Run migrations
cd backend && alembic upgrade head

# Start services
docker-compose up -d
```

## 🏗️ Architecture

### Stack
- **Database**: PostgreSQL (Supabase) with SSL
- **Cache**: Redis for holds and rate limiting
- **Backend**: FastAPI + SQLAlchemy (asyncio)
- **Frontend**: React + shadcn/ui

### Key Features
- ✅ **Real-time availability** with slot management
- ✅ **Idempotent payments** with Wompi webhooks (HMAC-SHA256)
- ✅ **Rate limiting** (5 req/min on quotes/holds)
- ✅ **WhatsApp messaging** via Chatrace templates
- ✅ **ICS calendar import** for aircraft availability
- ✅ **Embeddable widget** for WordPress/external sites
- ✅ **Health monitoring** with comprehensive checks

## 📡 API Endpoints

### Core Booking
```
GET    /api/health                     # System health check
GET    /api/availability               # Query available slots  
POST   /api/quotes                     # Generate flight quotes (rate limited)
GET    /api/quotes/{token}             # Retrieve quote details
POST   /api/holds                      # Create booking holds (rate limited)
POST   /api/bookings                   # Confirm bookings
```

### Operations
```
POST   /api/ops/slots/upsert           # Manage availability slots
POST   /api/ops/ics/sync               # Sync ICS calendar
```

### Integrations
```
POST   /api/webhooks/wompi             # Wompi payment webhooks
POST   /api/wa/send-template           # WhatsApp templates
```

## 🛡️ Security & Reliability

### Payment Security
- **Wompi webhook verification**: HMAC-SHA256 signature validation
- **Idempotency protection**: Prevents duplicate payment processing
- **Audit logging**: All transactions logged with WebhookEvent

### Rate Limiting
- **POST /api/quotes**: 5 requests per minute per IP
- **POST /api/holds**: 5 requests per minute per IP
- **Redis sliding window**: Automatic cleanup and reset

### Availability Protection
- **Redis-based holds**: Prevent double-booking during checkout
- **Slot validation**: Overlap detection and conflict resolution
- **Multi-source slots**: Portal, ICS calendar, Google Calendar

## 🌍 Deployment

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://...supabase.com:6543/postgres?sslmode=require
DATABASE_URL_MIGRATIONS=postgresql://...supabase.com:5432/postgres?sslmode=require

# Cache
REDIS_URL=redis://localhost:6379/0

# Payments
WOMPI_PUBLIC_KEY=pub_xxx
WOMPI_PRIVATE_KEY=prv_xxx
WOMPI_WEBHOOK_SECRET=xxx

# WhatsApp
CHATRACE_TOKEN=xxx
WHATSAPP_ENABLED=true
```

### Health Check Response
```json
{
  "status": "ok",
  "version": "2.0.0", 
  "database_type": "PostgreSQL/Supabase",
  "db": true,
  "redis": true
}
```

## 📊 Monitoring

### Operations Reports
```bash
# Generate health report
python scripts/gen_report.py

# Database backup
./scripts/pg_backup.sh

# ICS calendar sync
python scripts/sync_ics_all.py
```

### CI/CD Pipeline
- **Backend**: ruff linting + pytest
- **Frontend**: build validation
- **Redis services**: Health checks included

## 📚 Documentation

- [**Availability System**](docs/README_AVAILABILITY.md) - Slot management and holds
- [**Import System**](docs/README_IMPORTS.md) - ICS calendar import (v1)
- [**Pricing Engine**](docs/README_PRICING.md) - Dynamic pricing calculations
- [**Widget System**](docs/README_WIDGET.md) - Embeddable booking widget
- [**Go-Live Guide**](docs/GO_LIVE.md) - Production deployment checklist

## 🇵🇦 Panama Configuration

**Timezone**: America/Panama  
**Currency**: USD  
**Primary Routes**: PTY ↔ BLB, DAV, CHX  
**WhatsApp Format**: +507XXXXXXXX

---

**Version**: v2.0.0 (PostgreSQL/Supabase)  
**Branch**: release/v2.0-postgres  
**Status**: Production Ready ✅
