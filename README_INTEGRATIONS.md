# Charter Aviation System - Integration Guide

## 🎯 System Overview

This is a complete charter aviation booking system with:
- **PostgreSQL** database with normalized schema
- **Excel/CSV data import** system
- **Real-time pricing engine** with taxes and service fees
- **Wompi payment integration** (Panama)
- **WhatsApp/Chatrace messaging** integration
- **Beautiful React admin interface**

## 📊 Current Status: FULLY OPERATIONAL ✅

### ✅ Working Components (Ready to Use)
1. **Data Import System** - Import operators, aircraft, flights, airports, routes from Excel/CSV
2. **Quote Generation** - Real-time pricing with taxes (ITBMS 7%) and service fees (5%)
3. **API Endpoints** - Complete REST API for all operations
4. **Admin Interface** - Beautiful React UI for managing imports and system health
5. **Database Schema** - Fully normalized PostgreSQL schema with relationships
6. **Pricing Engine** - Sophisticated pricing with surcharges, overrides, and tax calculations

### 🔧 Integration Setup Required

To enable full functionality, you need to configure these integrations:

## 1. Wompi Payment Integration (Panama)

**Required Credentials:**
```env
WOMPI_BASE_URL="https://api.wompi.pa"
WOMPI_PUBLIC_KEY="pub_test_your_key_here"     # Get from Wompi dashboard
WOMPI_PRIVATE_KEY="prv_test_your_key_here"    # Get from Wompi dashboard  
WOMPI_INTEGRITY_KEY="test_integrity_key_here" # For widget (optional)
WOMPI_WEBHOOK_SECRET="your_webhook_secret"    # For webhook signature validation
```

**How to Get Credentials:**
1. Sign up at [Wompi Panama](https://wompi.pa)
2. Go to your dashboard → API Keys
3. Copy test/production keys to `.env` file
4. Configure webhook URL: `https://your-domain.com/api/webhooks/wompi`

**Features Once Configured:**
- Create payment links for bookings
- Process payments with webhook notifications
- Automatic booking status updates (PENDING → PAID)
- Support for test and production environments

## 2. WhatsApp/Chatrace Integration

**Required Credentials:**
```env
CHATRACE_BASE_URL="https://api.chatrace.com"
CHATRACE_API_KEY="your_chatrace_key_here"      # Get from Chatrace
CHATRACE_INSTANCE_ID="your_instance_id_here"   # Your WhatsApp instance
CHATRACE_PHONE_NUMBER="15557298766"            # Your WhatsApp number
```

**How to Get Credentials:**
1. Sign up at [Chatrace](https://chatrace.com)
2. Connect your WhatsApp Business account
3. Get API key and instance ID from dashboard
4. Configure webhook URL: `https://your-domain.com/api/webhooks/wa`

**Features Once Configured:**
- Send template messages to customers
- Receive inbound WhatsApp messages  
- Booking confirmations and notifications
- Customer support integration

**Fallback (Works Now):**
- Click-to-Chat URLs: `https://wa.me/15557298766?text=message`
- No API key required for basic click-to-chat functionality

## 3. Redis Integration (Optional)

For production deployment, configure Redis for:
- Hold management (aircraft availability locks)
- Session storage
- Caching

```env
REDIS_URL="redis://your-redis-server:6379"
```

## 📋 Sample Data Included

The system comes with comprehensive sample data:

### Operators (5)
- Sky Ride Charter (PTY base) - info@skyride.com
- Aero Panama (PAC base) - contact@aeropanama.com  
- Central Air Charter (DAV base) - sales@centralair.pa
- Bocas Aviation (BOC base) - booking@bocasaviation.com
- Pacific Wings (CHX base) - info@pacificwings.pa

### Aircraft (6)
- Cessna Citation X (12 seats) - $150/hour ground time
- Beechcraft King Air 350 (9 seats) - $120/hour ground time
- Piper Navajo (8 seats) - $100/hour ground time
- Cessna 208 Caravan (14 seats) - $80/hour ground time
- DHC-6 Twin Otter (19 seats) - $90/hour ground time
- Embraer Phenom 300 (11 seats) - $200/hour ground time

### Routes & Pricing
- **PTY → BOC**: $1,200 (Panama City to Bocas del Toro)
- **PTY → CHX**: $1,500 (Panama City to Changuinola)  
- **DAV → PTY**: $900 (David to Panama City)
- **BOC → CHX**: $400 (Inter-island shuttle)
- **PTY → RIH**: $2,200 (Panama City to Eastern Panama)

## 🚀 Getting Started

### 1. Test the System (No Credentials Required)
```bash
# Visit the admin interface
open https://your-domain.com/admin

# Test quote generation
curl -X POST https://your-domain.com/api/quotes \
  -H "Content-Type: application/json" \
  -d '{"listing_id":"<listing-id>","passengers":2,"trip_type":"ONE_WAY"}'

# Import your own data
# Use the admin interface to upload Excel/CSV files
```

### 2. Configure Integrations
1. Update `/app/backend/.env` with your credentials
2. Restart the backend: `sudo supervisorctl restart backend`
3. Test integrations through the admin interface

### 3. Production Deployment
- Configure proper domain name
- Set up HTTPS/SSL certificates  
- Use production API keys
- Configure monitoring and backups

## 🔍 Testing Integration

Run the comprehensive test suite:
```bash
cd /app/backend
python integration_test.py
```

This tests:
- ✅ All API endpoints
- ✅ Quote generation with real pricing
- ✅ Database connectivity
- ✅ Webhook endpoints
- ✅ WhatsApp click-to-chat URLs

## 📞 Support

The system is production-ready with proper error handling, logging, and validation. For technical support or customization:

1. **System Health**: Check `/api/health` endpoint
2. **Import Logs**: View detailed import error reports in admin interface
3. **API Documentation**: All endpoints follow REST conventions
4. **Database Schema**: Fully documented in `/app/backend/models.py`

## 🎯 Next Steps

1. **Add Your Credentials** - Configure Wompi and Chatrace in `.env`
2. **Import Your Data** - Use admin interface to import your fleet and routes
3. **Customize Branding** - Update company info and colors in frontend
4. **Deploy to Production** - Set up proper hosting and monitoring

The system is designed to handle real charter operations with proper business logic, security, and scalability.