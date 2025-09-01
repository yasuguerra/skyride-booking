# Pricing Engine Documentation

## Overview
SkyRide pricing engine calculates charter flight costs using distance, aircraft type, and dynamic pricing factors.

## Components

### 1. Base Pricing Model
- Distance calculation using airport coordinates
- Aircraft-specific hourly rates
- Minimum flight time billing (usually 1 hour)

### 2. Price Factors
- **Peak season**: 1.2x multiplier (Dec-Mar)
- **Weekend premium**: 1.1x multiplier (Fri-Sun)
- **Short notice**: 1.15x if booking <48h
- **Empty leg discount**: 0.7x for repositioning flights

### 3. Route-Specific Pricing
Stored in `routes` table:
- Fixed base price per route
- Override distance calculations
- Special pricing for popular routes

## API

### Quote Creation
```
POST /api/quotes
{
  "origin": "PTY",
  "destination": "BLB", 
  "date": "2025-01-15",
  "passengers": 4,
  "aircraft_type": "turboprop"
}
```

### Response Structure
```json
{
  "token": "qt_abc123",
  "breakdown": {
    "base_price": 1200.00,
    "distance_km": 280,
    "flight_time_hours": 1.5,
    "aircraft_rate": 800.00,
    "factors": {
      "weekend_premium": 1.1,
      "peak_season": 1.2
    },
    "total": 1584.00
  },
  "valid_until": "2025-01-16T10:00:00Z"
}
```

## Configuration

### Aircraft Rates
Set in `aircraft` table:
```sql
UPDATE aircraft SET hourly_rate = 850.00 WHERE type = 'turboprop';
```

### Route Overrides
```sql
INSERT INTO routes (origin, destination, base_price, flight_time_hours) 
VALUES ('PTY', 'BLB', 1200.00, 1.5);
```

### Pricing Factors
Environment variables:
- `PEAK_SEASON_MULTIPLIER=1.2`
- `WEEKEND_PREMIUM=1.1`
- `SHORT_NOTICE_HOURS=48`
- `SHORT_NOTICE_MULTIPLIER=1.15`

## Business Rules

### Minimum Billing
- Minimum 1 hour billing for all flights
- Taxi time included in flight time
- Round up to nearest 15-minute increment

### Dynamic Pricing
- Real-time availability affects pricing
- High demand periods increase prices
- Empty leg opportunities decrease prices

### Quote Validity
- Standard quotes valid for 24 hours
- Hold quotes valid for 30 minutes during checkout
- Prices locked during payment process

## Audit Trail
All pricing calculations logged with:
- Quote token
- Calculation factors used
- Final price breakdown
- Timestamp and user context
