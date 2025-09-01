# SkyRide v2.0 Go-Live Guide

## Pre-Launch Checklist

### 1. Environment Setup ✅
- [ ] Supabase database configured with SSL
- [ ] Environment variables updated (.env)
- [ ] Redis cache operational
- [ ] Domain pointing to production servers

### 2. Database Migration ✅
- [ ] `alembic upgrade head` executed successfully
- [ ] All tables created in Supabase
- [ ] Sample data seeded if needed
- [ ] Database backups configured

### 3. API Health Verification ✅
- [ ] `/api/health` returns `{"db": true, "redis": true}`
- [ ] Rate limiting active (429 on >5 req/min)
- [ ] CORS configured for production domains
- [ ] All endpoints responding correctly

### 4. Payment Integration ✅
- [ ] Wompi webhook verification working
- [ ] HMAC-SHA256 signature validation
- [ ] Test payment processed successfully
- [ ] Idempotency preventing duplicate payments

### 5. WhatsApp Messaging ✅
- [ ] Chatrace API configured
- [ ] Template messages sending
- [ ] Message logging operational
- [ ] Error handling for failed messages

### 6. Monitoring & Operations ✅
- [ ] Health check monitoring setup
- [ ] Log aggregation configured
- [ ] Error alerting active
- [ ] Backup automation verified

## Launch Sequence

### Step 1: Staging Validation
```bash
# Test full booking flow
curl -X POST https://staging.skyride.city/api/quotes \
  -H "Content-Type: application/json" \
  -d '{"origin":"PTY","destination":"BLB","date":"2025-01-15","passengers":2}'

# Verify health
curl https://staging.skyride.city/api/health
```

### Step 2: Production Deployment
```bash
# Deploy release branch
git checkout release/v2.0-postgres
git tag v2.0.0
git push origin v2.0.0

# Run migrations
alembic upgrade head

# Verify deployment
curl https://booking.skyride.city/api/health
```

### Step 3: DNS Cutover
- [ ] Update DNS A records to new servers
- [ ] Verify SSL certificates
- [ ] Test from multiple locations
- [ ] Monitor error rates

### Step 4: Post-Launch Monitoring
- [ ] Watch error logs for 2 hours
- [ ] Verify booking flow end-to-end
- [ ] Check payment processing
- [ ] Monitor WhatsApp delivery

## Rollback Plan

### If Issues Detected:
1. **Database issues**: Restore from backup
2. **API failures**: Revert to previous deployment
3. **Payment problems**: Disable payment processing temporarily
4. **Performance issues**: Scale server resources

### Rollback Commands:
```bash
# Revert deployment
git checkout main
# Restore database if needed
psql $DATABASE_URL < backup_YYYYMMDD.sql
```

## Success Metrics

### Day 1 Targets:
- [ ] Zero 5xx errors
- [ ] <500ms average response time
- [ ] >99% uptime
- [ ] All scheduled backups successful

### Week 1 Targets:
- [ ] 100+ successful bookings
- [ ] <1% payment failure rate
- [ ] WhatsApp delivery >95%
- [ ] No data loss incidents

## Support Contacts

### Technical Issues:
- **Database**: Supabase Support
- **Hosting**: Server admin team
- **Payments**: Wompi technical support
- **WhatsApp**: Chatrace support

### Escalation:
1. **Critical**: Page on-call engineer
2. **High**: Create support ticket
3. **Medium**: Email tech team
4. **Low**: Add to sprint backlog

## Post-Launch Tasks

### Immediate (24h):
- [ ] Generate first REPORT.md with real data
- [ ] Verify all integrations working
- [ ] Update monitoring dashboards
- [ ] Document any issues encountered

### Week 1:
- [ ] Performance optimization review
- [ ] User feedback collection
- [ ] Analytics data analysis
- [ ] Process improvements

### Month 1:
- [ ] Capacity planning review
- [ ] Feature usage analysis
- [ ] ROI assessment
- [ ] v2.1 planning

---

**Go-Live Authorized By:** Technical Lead  
**Date:** August 28, 2025  
**Version:** v2.0.0 PostgreSQL/Supabase  
**Contact:** SkyRide Operations Team
