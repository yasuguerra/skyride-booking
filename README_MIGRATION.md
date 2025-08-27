# SkyRide Platform Migration Guide

## 🎯 Migration Overview

This document outlines the complete migration of SkyRide from MongoDB to PostgreSQL, activation of real payment/messaging integrations, and new feature implementations.

## 📋 Migration Checklist

### ✅ Completed
- [x] PostgreSQL models and schema design
- [x] Alembic migration system setup
- [x] MongoDB to PostgreSQL migration scripts
- [x] Redis integration for locks and caching
- [x] Wompi production payment integration (no DRY_RUN)
- [x] Chatrace WhatsApp production integration
- [x] Availability system Phase 1
- [x] WordPress Gutenberg blocks
- [x] GA4 cross-domain analytics
- [x] Docker development environment

### 🔄 In Progress
- [ ] Production PostgreSQL deployment (Supabase)
- [ ] Data migration execution
- [ ] ICS calendar import (optional)
- [ ] Empty Legs auto-detection

### ⏳ Pending
- [ ] Production deployment
- [ ] DNS and SSL configuration
- [ ] Performance optimization
- [ ] Security audit

## 🚀 Quick Start - Development

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Development Setup

1. **Clone and Setup Environment**
```bash
git clone <repository>
cd skyride-platform
cp .env.example .env
# Edit .env with your credentials
```

2. **Start Development Stack**
```bash
# Start PostgreSQL + Redis + Backend + Frontend
docker-compose -f docker-compose.dev.yml up -d

# Or start with admin tools
docker-compose -f docker-compose.dev.yml --profile admin up -d
```

3. **Run Database Migration**
```bash
# Run Alembic migrations
docker-compose exec backend alembic upgrade head

# Migrate data from MongoDB (if available)
docker-compose exec backend python migrate_mongo_to_postgres.py
```

4. **Access Services**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- pgAdmin: http://localhost:5050 (with admin profile)
- Redis Commander: http://localhost:8081 (with admin profile)

## 🔧 Configuration

### Environment Variables

#### Database
```env
POSTGRES_URL=postgresql+asyncpg://skyride_user:skyride_password@localhost:5432/skyride
REDIS_URL=redis://localhost:6379/0
```

#### Payment Integration (Production)
```env
WOMPI_PUBLIC_KEY=pk_prod_xxxxx
WOMPI_PRIVATE_KEY=sk_prod_xxxxx
WOMPI_WEBHOOK_SECRET=whsec_xxxxx
WOMPI_ENV=prod
PAYMENTS_DRY_RUN=false
```

#### WhatsApp Integration (Production)
```env
CHATRACE_API_URL=https://api.chatrace.com/v1
CHATRACE_API_TOKEN=cr_xxxxx
```

#### Analytics & Tracking
```env
GA_MEASUREMENT_ID=G-XXXXXXXXXX
```

#### Feature Flags
```env
EMPTY_LEGS_ENABLED=true
YAPPY_ENABLED=false
```

### WordPress Integration

1. **Install Plugin**
```bash
# Copy the WordPress plugin file
cp wordpress-gutenberg-block.php /path/to/wordpress/wp-content/plugins/skyride-blocks.php
cp skyride-blocks.css /path/to/wordpress/wp-content/plugins/assets/
```

2. **Activate Plugin**
- Go to WordPress Admin → Plugins
- Activate "SkyRide Booking Blocks"

3. **Configure Settings**
- Go to Settings → SkyRide
- Enter GA4 Measurement ID
- Save settings

4. **Use Blocks**
- In Gutenberg editor, search for "SkyRide"
- Add "SkyRide Quote CTA" or "SkyRide Hot Deals" blocks

## 📊 API Changes and New Endpoints

### New Endpoints
```http
# Availability System
GET /api/availability?aircraftId={id}&dateFrom={date}&dateTo={date}

# Redis Hold Management
POST /api/holds/redis-lock
{
  "listingId": "uuid",
  "holdDurationMinutes": 1440
}

# WordPress Integration
GET /api/wordpress/hot-deals?limit=6
GET /api/wordpress/quote-cta

# Analytics Tracking
POST /api/analytics/track-event
{
  "event": "quote_viewed",
  "parameters": {...},
  "client_id": "client_123"
}
```

### Updated Endpoints
All existing endpoints maintain the same contracts but now:
- Use PostgreSQL instead of MongoDB
- Have production-ready payment integration
- Include real WhatsApp messaging
- Support Redis-based locking

## 🔄 Migration Process

### 1. Data Migration (MongoDB → PostgreSQL)

```bash
# Backup existing MongoDB data
mongodump --uri="mongodb://localhost:27017/skyride" --out=backup/

# Run migration script
python migrate_mongo_to_postgres.py

# Verify migration
python -c "
import asyncio
from database_postgres import get_db
from models_postgres import Listing

async def check():
    async with get_db() as db:
        result = await db.execute(select(Listing))
        listings = result.scalars().all()
        print(f'Migrated {len(listings)} listings')

asyncio.run(check())
"
```

### 2. Feature Activation

```bash
# Update environment variables
export PAYMENTS_DRY_RUN=false
export EMPTY_LEGS_ENABLED=true
export CHATRACE_API_TOKEN=your_real_token

# Restart services
docker-compose restart backend
```

### 3. WordPress Deployment

```bash
# Deploy to WordPress
scp wordpress-gutenberg-block.php user@wordpress:/wp-content/plugins/
scp skyride-blocks.css user@wordpress:/wp-content/themes/theme/assets/
```

## 🧪 Testing

### Backend Testing
```bash
# Full test suite
python cli_test_wompi.py full

# Individual tests
python cli_test_wompi.py health
python cli_test_wompi.py listings
python cli_test_wompi.py quote
```

### Frontend Testing
```bash
# Start development server
yarn start

# Run tests
yarn test

# Build for production
yarn build
```

### Integration Testing
```bash
# Test PostgreSQL connection
python -c "
import asyncio
from database_postgres import init_db
asyncio.run(init_db())
print('✅ PostgreSQL connected')
"

# Test Redis connection
redis-cli ping

# Test Wompi integration
curl -X POST https://booking.skyride.city/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"orderId":"test","provider":"WOMPI"}'
```

## 📈 Performance Monitoring

### Database Performance
```sql
-- Check table sizes
SELECT * FROM analytics.table_sizes;

-- Check slow queries
SELECT * FROM analytics.query_performance;

-- Check connection count
SELECT count(*) FROM pg_stat_activity;
```

### Redis Monitoring
```bash
# Check Redis info
redis-cli info

# Monitor commands
redis-cli monitor

# Check memory usage
redis-cli memory usage
```

### Application Metrics
- API response times: Available in backend logs
- Payment success rates: Track via Wompi webhooks
- User engagement: GA4 cross-domain tracking

## 🛠️ Troubleshooting

### Common Issues

1. **Database Connection Failed**
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up postgres
```

2. **Redis Lock Issues**
```bash
# Clear all Redis locks
redis-cli FLUSHALL

# Check active locks
redis-cli KEYS "hold:*"
```

3. **Payment Integration Errors**
```bash
# Check Wompi configuration
curl -H "Authorization: Bearer $WOMPI_PRIVATE_KEY" \
  https://api.wompi.co/v1/merchants

# Verify webhook signature
python -c "
import hmac, hashlib
payload = b'test'
secret = 'your_webhook_secret'
sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
print(f'Test signature: {sig}')
"
```

4. **WordPress Block Issues**
```php
// Check if plugin is loaded
var_dump(class_exists('SkyRideGutenbergBlocks'));

// Test API connection
$response = wp_remote_get('https://booking.skyride.city/api/health');
var_dump(wp_remote_retrieve_response_code($response));
```

## 🔒 Security Considerations

### Production Checklist
- [ ] Change all default passwords
- [ ] Enable Redis authentication
- [ ] Configure PostgreSQL SSL
- [ ] Set up proper CORS origins
- [ ] Enable webhook signature verification
- [ ] Configure CSP headers
- [ ] Set up monitoring and alerting
- [ ] Regular security audits

### Access Control
- Database: Role-based access with limited permissions
- Redis: Password authentication and command renaming
- API: Rate limiting and input validation
- Webhooks: Signature verification and IP whitelisting

## 📞 Support

### Documentation
- API Documentation: `/api/docs` (Swagger UI)
- Database Schema: See `models_postgres.py`
- Frontend Components: See `src/components/`

### Monitoring
- Application Logs: `docker-compose logs -f backend`
- Database Logs: `docker-compose logs -f postgres`
- Redis Logs: `docker-compose logs -f redis`

### Contact
- Technical Issues: Check logs and troubleshooting guide
- Integration Support: Review API documentation
- Security Concerns: Follow security checklist

---

## 🎉 Migration Complete!

Once this migration is complete, SkyRide will have:

✅ **Modern PostgreSQL backend** with proper relationships and indexing
✅ **Production-ready payment processing** with Wompi integration
✅ **Real-time WhatsApp messaging** via Chatrace
✅ **Advanced availability management** with Redis-based locking
✅ **WordPress integration** with custom Gutenberg blocks
✅ **Cross-domain analytics** with GA4 tracking
✅ **Scalable Docker deployment** with monitoring tools

The platform is now enterprise-ready and can handle production workloads with proper monitoring, caching, and real-time features.