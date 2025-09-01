# Availability System Documentation

## Overview
SkyRide availability system manages aircraft time slots for booking. Supports multiple sources: manual, ICS calendar import, and Google Calendar sync.

## Components

### 1. AvailabilitySlot Model
- `aircraft_id`: Aircraft identifier
- `start_time`, `end_time`: UTC timestamps
- `duration_hours`: Calculated duration
- `source`: PORTAL, ICS, GOOGLE
- `is_available`: Availability flag
- `metadata`: JSON with additional data

### 2. Availability Service
Location: `backend/services/availability.py`

Key methods:
- `create_or_update_slot()`: Upsert slots with overlap validation
- `get_availability()`: Query available slots by date range
- `check_slot_availability()`: Verify slot availability with hold checking

### 3. ICS Calendar Import
Location: `backend/integrations/ics_importer.py`

- Imports from `.ics` calendar URLs
- Creates slots with `source="ICS"`
- Supports timezone conversion (Panama → UTC)
- Manual sync via `/api/ops/ics/sync`
- Batch sync via `scripts/sync_ics_all.py`

### 4. Hold Integration
Availability checks include active Redis holds:
- Check `hold:{aircraft_id}:{date}` patterns
- Prevent double-booking during checkout

## API Endpoints

### Query Availability
```
GET /api/availability?dateRange=2025-01-01..2025-01-31
```

### Manual Slot Management  
```
POST /api/ops/slots/upsert
{
  "aircraftId": "N123AB",
  "start": "2025-01-15T10:00:00Z",
  "end": "2025-01-15T18:00:00Z",
  "status": "AVAILABLE",
  "source": "PORTAL"
}
```

### ICS Calendar Sync
```
POST /api/ops/ics/sync?aircraftId=N123AB&ics_url=https://...
```

## Configuration

### Aircraft Calendar URLs
Set `calendar_url` in Aircraft model for automatic ICS sync.

### Environment Variables
- `TZ=America/Panama`: Default timezone
- Aircraft metadata can include calendar sync settings

## Data Flow

1. **ICS Import**: External calendar → AvailabilitySlot (source=ICS)
2. **Manual Entry**: Operations → AvailabilitySlot (source=PORTAL)  
3. **Availability Query**: Filter by date + check holds
4. **Booking**: Create hold → validate availability → confirm booking

## Monitoring

- ICS sync logs aircraft sync results
- Overlap validation prevents conflicting slots
- Hold system prevents race conditions during booking
