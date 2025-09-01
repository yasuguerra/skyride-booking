# Import System Documentation

## Overview
SkyRide import system handles CSV/XLSX data import for aircraft, routes, listings, and availability slots.

## ICS Calendar Import (v1)

### Purpose
Import aircraft availability from external ICS calendar feeds.

### Implementation
Location: `backend/integrations/ics_importer.py`

Features:
- Fetch ICS from URLs
- Parse VEVENT components
- Convert timezone (America/Panama → UTC)
- Create AvailabilitySlot records with `source="ICS"`
- Upsert behavior (update existing slots)

### Usage

#### Manual Sync (Single Aircraft)
```bash
POST /api/ops/ics/sync?aircraftId=N123AB&ics_url=https://example.com/cal.ics
```

#### Batch Sync (All Aircraft)
```bash
python scripts/sync_ics_all.py
```

#### Single Aircraft Script
```bash
python scripts/sync_ics_all.py N123AB
```

### Aircraft Configuration
Set `calendar_url` field in Aircraft model:
```sql
UPDATE aircraft SET calendar_url = 'https://example.com/calendar.ics' WHERE id = 'N123AB';
```

### Event Processing
- **All-day events**: Converted to 00:00-23:59 availability
- **Timed events**: Exact start/end times
- **Recurring events**: Expanded to individual slots
- **Timezone handling**: Convert to UTC for storage

### Data Model
```python
AvailabilitySlot(
    aircraft_id="N123AB",
    start_time=datetime(...),
    end_time=datetime(...), 
    source="ICS",
    metadata={
        "summary": "Available for Charter",
        "ics_sync_at": "2025-08-28T10:00:00Z"
    }
)
```

### Error Handling
- Network timeouts: 30 second limit
- Parse errors: Skip invalid events, log warnings
- Duplicate slots: Update metadata, preserve ID
- Missing aircraft: Return 404 error

### Monitoring
- Sync results logged with counts
- Failed syncs logged with aircraft ID
- Metrics: `slots_created`, `slots_updated`, `total_events`

## Future Extensions

### CSV/XLSX Import (Future)
- Bulk aircraft import
- Route data import  
- Listing batch upload
- Customer data import

### Google Calendar (Future)
- OAuth2 integration
- Real-time webhook updates
- Two-way sync capability

## Scheduling
Recommended: Daily sync via cron
```bash
0 6 * * * cd /app && python scripts/sync_ics_all.py
```
