# SkyRide v2.0 Operations Report

**Generated:** {date}  
**Environment:** Production  
**PostgreSQL/Redis Stack**

## System Health

### Database Status
- [ ] PostgreSQL connection: ✅ Connected
- [ ] Database version: PostgreSQL 15.x
- [ ] Active connections: X/100
- [ ] Database size: XXX MB
- [ ] Last backup: YYYY-MM-DD HH:MM

### Redis Cache Status  
- [ ] Redis connection: ✅ Connected
- [ ] Redis version: 7.x
- [ ] Memory usage: XXX MB / 512 MB
- [ ] Active holds: X holds
- [ ] Cache hit ratio: XX%

### API Health
- [ ] Backend health check: ✅ Healthy
- [ ] Response time: XXX ms (avg)
- [ ] Error rate: X.X% (last 24h)
- [ ] Uptime: XX.X% (last 7 days)

## Data Import Status

### Recent Imports
```
Operators: X imported, X updated, X errors
Aircraft: X imported, X updated, X errors  
Listings: X imported, X updated, X errors
Routes: X imported, X updated, X errors
```

### Import Errors
```bash
# Check for recent import error files
ls -la import_errors_*.csv | head -5

# Latest error summary:
- Row 15: Missing operator code
- Row 23: Invalid aircraft registration
- Row 34: Route not found: ABC-DEF
```

## Pricing & Quotes

### Quote Generation Test
```bash
# Test pricing calculation
curl -X POST https://booking.skyride.city/api/quotes \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "PTY", 
    "destination": "BLB",
    "date": "2025-01-15",
    "passengers": 2
  }'
```

**Result:**
```json
{
  "token": "quote_abc123",
  "breakdown": {
    "basePrice": 2500.00,
    "serviceFee": 125.00,
    "surcharges": [],
    "subtotal": 2625.00,
    "itbms": 183.75,
    "totalPrice": 2808.75
  },
  "currency": "USD"
}
```

## Availability & Holds

### Availability Check
```bash
# Test availability system
curl "https://booking.skyride.city/api/availability?aircraftId=aircraft_001&dateRange=2025-01-01..2025-01-31"
```

**Result:**
- Total slots: XX
- Available: XX slots
- Busy: XX slots  
- On hold: XX slots
- Maintenance: XX slots

### Active Holds Test
```bash
# Create test hold
curl -X POST https://booking.skyride.city/api/holds \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-$(date +%s)" \
  -d '{
    "listing_id": "test_listing_123",
    "customer_email": "test@skyride.city"
  }'
```

**Hold Expiration Test:**
- Hold created: ✅ Success
- Hold expires: YYYY-MM-DD HH:MM:SS
- TTL remaining: XXXX seconds
- Idempotency: ✅ Working

## Payment Integration

### Wompi Webhook Verification
```bash
# Recent webhook events
curl https://booking.skyride.city/api/admin/webhook-events?limit=5
```

**Status:**
- Webhook signature: ✅ Valid HMAC-SHA256
- Event processing: ✅ Idempotent 
- Payment confirmations: X events (last 24h)
- Failed events: X events
- Retry handling: ✅ Working

### Test Payment Flow
- [ ] Payment link creation: ✅ Working
- [ ] Webhook delivery: ✅ Verified
- [ ] Booking status update: ✅ PAID status
- [ ] Duplicate event handling: ✅ Idempotent

## WhatsApp Integration

### Template Messaging Test
```bash
# Test WhatsApp template
curl -X POST https://booking.skyride.city/api/wa/send-template \
  -H "Content-Type: application/json" \
  -d '{
    "template": "quote_created",
    "to": "+507-6000-0000", 
    "params": {
      "customer_name": "Test Customer",
      "quote_amount": "2500",
      "quote_link": "https://booking.skyride.city/q/test123"
    }
  }'
```

**Result:**
- Template send: ✅ Success
- Message logging: ✅ Recorded
- Response time: XXX ms

## Widget & WordPress

### Widget Functionality
```bash
# Test widget.js availability
curl -I https://booking.skyride.city/widget.js
```

**Widget Status:**
- Widget script: ✅ Available (HTTP 200)
- File size: XX KB
- CDN caching: ✅ Enabled
- CORS headers: ✅ Configured

### WordPress Blocks Test
- [ ] Block registration: ✅ Loaded
- [ ] Asset enqueuing: ✅ skyride-frontend.js
- [ ] CSS loading: ✅ skyride-blocks.css  
- [ ] Widget initialization: ✅ Working
- [ ] Quote creation: ✅ Working

## Analytics (GA4)

### Event Tracking Verification
**Debug Mode Events (last hour):**
- view_item: X events
- add_to_cart: X events  
- begin_checkout: X events
- purchase: X events
- generate_lead: X events

**Cross-Domain Tracking:**
- Linker domains: ✅ skyride.city, booking.skyride.city
- Client ID persistence: ✅ Working
- Enhanced ecommerce: ✅ Configured

## Security & Performance

### CORS Configuration
```
CORS_ORIGINS=https://www.skyride.city,https://booking.skyride.city
```
- [ ] CORS headers: ✅ Configured
- [ ] OPTIONS preflight: ✅ Working
- [ ] Domain restrictions: ✅ Enforced

### CSP Headers
- [ ] Content Security Policy: ✅ Active
- [ ] Script sources: ✅ Whitelisted
- [ ] Font/image sources: ✅ Configured

### Rate Limiting  
- [ ] API rate limits: ✅ Active (100 req/min)
- [ ] Redis-based limiting: ✅ Working
- [ ] Webhook rate limits: ✅ Protected

## Backup Status

### Database Backups
```bash
# Check recent backups
ls -la /backups/postgres/ | head -5
```

**Backup Status:**
- Last PostgreSQL backup: YYYY-MM-DD HH:MM
- Backup size: XXX MB
- Retention: 30 days
- S3 sync: ✅ Enabled

### Redis Snapshots
- Last snapshot: YYYY-MM-DD HH:MM  
- Snapshot size: XX MB
- AOF enabled: ✅ Yes

## Action Items

### Critical (P0)
- [ ] No critical issues

### Important (P1)  
- [ ] Monitor hold expiration cleanup
- [ ] Optimize availability query performance
- [ ] Set up alerting for webhook failures

### Nice to Have (P2)
- [ ] Add more comprehensive error logging
- [ ] Implement query result caching
- [ ] Add performance metrics dashboard

## Monitoring Setup

### Health Checks
- [ ] /api/health endpoint: ✅ Active
- [ ] Database connectivity: ✅ Monitored  
- [ ] Redis connectivity: ✅ Monitored
- [ ] External API dependencies: ✅ Tracked

### Alerts Configured
- [ ] High error rate (>5%): ✅ Alert
- [ ] Database connection failures: ✅ Alert  
- [ ] Redis memory usage >80%: ✅ Alert
- [ ] Webhook processing delays: ✅ Alert

---

**Report generated by:** `scripts/gen_report.py`  
**Next report:** Scheduled for YYYY-MM-DD  
**On-call:** SkyRide Operations Team
