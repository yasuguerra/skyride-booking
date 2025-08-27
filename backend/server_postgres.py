from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from databases import Database
from dotenv import load_dotenv
import os
import logging
import pandas as pd
import redis
import aioredis
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import re
import requests
import hashlib
import hmac
from pathlib import Path

# Import our models and database setup
from database import database, get_db, engine, Base
from models import *
import pricing.quoting as quoting_engine

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create all tables
Base.metadata.create_all(bind=engine)

# Initialize Redis connection
redis_client = None

app = FastAPI(title="Charter Aviation System", version="1.0.0")
api_router = APIRouter(prefix="/api")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Startup and shutdown events
@app.on_event("startup")
async def startup():
    await database.connect()
    global redis_client
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    redis_client = aioredis.from_url(redis_url, decode_responses=True)
    logger.info("Database and Redis connected")

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    if redis_client:
        await redis_client.close()
    logger.info("Database and Redis disconnected")

# Utility functions
def parse_flight_title(flight_title: str) -> tuple[Optional[str], Optional[str]]:
    """Extract origin and destination from flight title using heuristics"""
    # Common separators: –, →, /, -, to, ->, <->
    separators = ['–', '→', '->', '<->', ' to ', ' - ', ' / ']
    
    for sep in separators:
        if sep in flight_title:
            parts = flight_title.split(sep)
            if len(parts) >= 2:
                origin = parts[0].strip().upper()
                destination = parts[1].strip().upper()
                return origin, destination
    
    return None, None

def generate_confirmation_code() -> str:
    """Generate a unique booking confirmation code"""
    return f"CHR{str(uuid.uuid4())[:8].upper()}"

async def create_import_run(import_type: str, filename: str, total_rows: int) -> str:
    """Create a new import run record"""
    import_run_id = str(uuid.uuid4())
    query = """
    INSERT INTO import_runs (id, import_type, filename, status, total_rows, created_at)
    VALUES (:id, :import_type, :filename, :status, :total_rows, :created_at)
    """
    await database.execute(query, {
        "id": import_run_id,
        "import_type": import_type,
        "filename": filename,
        "status": "RUNNING",
        "total_rows": total_rows,
        "created_at": datetime.now(timezone.utc)
    })
    return import_run_id

async def log_import_error(import_run_id: str, row_number: int, error_type: str, error_message: str, row_data: dict):
    """Log an import error"""
    query = """
    INSERT INTO import_errors (id, import_run_id, row_number, error_type, error_message, row_data, created_at)
    VALUES (:id, :import_run_id, :row_number, :error_type, :error_message, :row_data, :created_at)
    """
    await database.execute(query, {
        "id": str(uuid.uuid4()),
        "import_run_id": import_run_id,
        "row_number": row_number,
        "error_type": error_type,
        "error_message": error_message,
        "row_data": json.dumps(row_data),
        "created_at": datetime.now(timezone.utc)
    })

async def complete_import_run(import_run_id: str, success_rows: int, error_rows: int, summary: dict = None):
    """Mark import run as completed"""
    query = """
    UPDATE import_runs 
    SET status = 'COMPLETED', success_rows = :success_rows, error_rows = :error_rows, 
        summary = :summary, completed_at = :completed_at, processed_rows = :processed_rows
    WHERE id = :id
    """
    await database.execute(query, {
        "id": import_run_id,
        "success_rows": success_rows,
        "error_rows": error_rows,
        "summary": json.dumps(summary) if summary else None,
        "completed_at": datetime.now(timezone.utc),
        "processed_rows": success_rows + error_rows
    })

# Import Endpoints

@api_router.post("/admin/import/operators")
async def import_operators(file: UploadFile = File(...)):
    """Import operators from Excel/CSV file"""
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="File must be Excel (.xlsx, .xls) or CSV (.csv)")
    
    try:
        # Read file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.file)
        else:
            df = pd.read_excel(file.file)
        
        import_run_id = await create_import_run("operators", file.filename, len(df))
        success_count = 0
        error_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Map columns
                operator_name = row.get('operator', '').strip()
                email = row.get('email', '').strip() if pd.notna(row.get('email')) else None
                phone = row.get('phone', '').strip() if pd.notna(row.get('phone')) else None
                base_airport = row.get('base_airport', '').strip() if pd.notna(row.get('base_airport')) else None
                
                if not operator_name:
                    raise ValueError("Operator name is required")
                
                # Create/find base airport if provided
                base_airport_id = None
                if base_airport:
                    # Check if airport exists
                    airport_query = "SELECT id FROM airports WHERE code = :code"
                    airport_result = await database.fetch_one(airport_query, {"code": base_airport.upper()})
                    
                    if not airport_result:
                        # Create new airport
                        airport_id = str(uuid.uuid4())
                        airport_insert = """
                        INSERT INTO airports (id, code, name, city, country, timezone, created_at)
                        VALUES (:id, :code, :name, :city, :country, :timezone, :created_at)
                        ON CONFLICT (code) DO NOTHING
                        """
                        await database.execute(airport_insert, {
                            "id": airport_id,
                            "code": base_airport.upper(),
                            "name": f"{base_airport.upper()} Airport",
                            "city": "Unknown",
                            "country": "PA",
                            "timezone": "America/Panama",
                            "created_at": datetime.now(timezone.utc)
                        })
                        base_airport_id = airport_id
                    else:
                        base_airport_id = str(airport_result['id'])
                
                # Upsert operator
                operator_id = str(uuid.uuid4())
                operator_upsert = """
                INSERT INTO operators (id, name, email, phone, base_airport_id, created_at, updated_at)
                VALUES (:id, :name, :email, :phone, :base_airport_id, :created_at, :updated_at)
                ON CONFLICT (name) DO UPDATE SET
                    email = EXCLUDED.email,
                    phone = EXCLUDED.phone,
                    base_airport_id = EXCLUDED.base_airport_id,
                    updated_at = EXCLUDED.updated_at
                """
                await database.execute(operator_upsert, {
                    "id": operator_id,
                    "name": operator_name,
                    "email": email,
                    "phone": phone,
                    "base_airport_id": base_airport_id,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                })
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                await log_import_error(import_run_id, idx + 1, "PROCESSING_ERROR", str(e), row.to_dict())
        
        await complete_import_run(import_run_id, success_count, error_count, {
            "operators_created": success_count,
            "errors": error_count
        })
        
        return {
            "import_run_id": import_run_id,
            "success_count": success_count,
            "error_count": error_count,
            "message": f"Processed {success_count + error_count} rows, {success_count} successful, {error_count} errors"
        }
        
    except Exception as e:
        logger.error(f"Error importing operators: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@api_router.post("/admin/import/aircraft")
async def import_aircraft(file: UploadFile = File(...)):
    """Import aircraft from Excel/CSV file"""
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="File must be Excel (.xlsx, .xls) or CSV (.csv)")
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.file)
        else:
            df = pd.read_excel(file.file)
        
        import_run_id = await create_import_run("aircraft", file.filename, len(df))
        success_count = 0
        error_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Map columns
                aircraft_name = row.get('name', '').strip()
                operator_name = row.get('operator', '').strip()
                aircraft_type = row.get('type', '').strip()
                capacity = row.get('capacity', 0)
                pets_allowed = bool(row.get('pets_allowed', False))
                ground_time_price = float(row.get('ground_time_price_usd', 0)) if pd.notna(row.get('ground_time_price_usd')) else None
                product_link = row.get('product_link', '').strip() if pd.notna(row.get('product_link')) else None
                
                if not aircraft_name or not operator_name or not aircraft_type:
                    raise ValueError("Aircraft name, operator, and type are required")
                
                if capacity <= 0:
                    raise ValueError("Capacity must be greater than 0")
                
                # Find operator
                operator_query = "SELECT id FROM operators WHERE name = :name"
                operator_result = await database.fetch_one(operator_query, {"name": operator_name})
                
                if not operator_result:
                    raise ValueError(f"Operator '{operator_name}' not found")
                
                operator_id = str(operator_result['id'])
                
                # Upsert aircraft
                aircraft_id = str(uuid.uuid4())
                aircraft_upsert = """
                INSERT INTO aircraft (id, operator_id, name, type, seats, pets_allowed, ground_time_price_usd, product_link, created_at, updated_at)
                VALUES (:id, :operator_id, :name, :type, :seats, :pets_allowed, :ground_time_price_usd, :product_link, :created_at, :updated_at)
                ON CONFLICT (operator_id, name) DO UPDATE SET
                    type = EXCLUDED.type,
                    seats = EXCLUDED.seats,
                    pets_allowed = EXCLUDED.pets_allowed,
                    ground_time_price_usd = EXCLUDED.ground_time_price_usd,
                    product_link = EXCLUDED.product_link,
                    updated_at = EXCLUDED.updated_at
                """
                await database.execute(aircraft_upsert, {
                    "id": aircraft_id,
                    "operator_id": operator_id,
                    "name": aircraft_name,
                    "type": aircraft_type,
                    "seats": int(capacity),
                    "pets_allowed": pets_allowed,
                    "ground_time_price_usd": ground_time_price,
                    "product_link": product_link,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                })
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                await log_import_error(import_run_id, idx + 1, "PROCESSING_ERROR", str(e), row.to_dict())
        
        await complete_import_run(import_run_id, success_count, error_count, {
            "aircraft_created": success_count,
            "errors": error_count
        })
        
        return {
            "import_run_id": import_run_id,
            "success_count": success_count,
            "error_count": error_count,
            "message": f"Processed {success_count + error_count} rows, {success_count} successful, {error_count} errors"
        }
        
    except Exception as e:
        logger.error(f"Error importing aircraft: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@api_router.post("/admin/import/flights")
async def import_flights(file: UploadFile = File(...)):
    """Import flights/listings from Excel/CSV file"""
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="File must be Excel (.xlsx, .xls) or CSV (.csv)")
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.file)
        else:
            df = pd.read_excel(file.file)
        
        import_run_id = await create_import_run("flights", file.filename, len(df))
        success_count = 0
        error_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Map columns
                flight_title = row.get('flight_title', '').strip()
                airplane_id = row.get('airplane_id')
                operator_id = row.get('operator_id')
                flight_duration = row.get('flight_duration_min')
                departure_days = row.get('departure_days', '').strip() if pd.notna(row.get('departure_days')) else None
                max_load_weight = float(row.get('max_load_weight_lbs')) if pd.notna(row.get('max_load_weight_lbs')) else None
                description = row.get('description', '').strip() if pd.notna(row.get('description')) else None
                price_without_itbms = float(row.get('price_without_itbms', 0)) if pd.notna(row.get('price_without_itbms')) else 0
                itbms = float(row.get('itbms', 0)) if pd.notna(row.get('itbms')) else 0
                
                if not flight_title:
                    raise ValueError("Flight title is required")
                
                # Parse origin/destination from flight title
                origin_code, destination_code = parse_flight_title(flight_title)
                route_id = None
                
                if origin_code and destination_code:
                    # Create/find airports and route
                    for airport_code, airport_name in [(origin_code, f"{origin_code} Airport"), (destination_code, f"{destination_code} Airport")]:
                        airport_query = "SELECT id FROM airports WHERE code = :code"
                        airport_result = await database.fetch_one(airport_query, {"code": airport_code})
                        
                        if not airport_result:
                            airport_id = str(uuid.uuid4())
                            airport_insert = """
                            INSERT INTO airports (id, code, name, city, country, timezone, created_at)
                            VALUES (:id, :code, :name, :city, :country, :timezone, :created_at)
                            ON CONFLICT (code) DO NOTHING
                            """
                            await database.execute(airport_insert, {
                                "id": airport_id,
                                "code": airport_code,
                                "name": airport_name,
                                "city": "Unknown",
                                "country": "PA",
                                "timezone": "America/Panama",
                                "created_at": datetime.now(timezone.utc)
                            })
                    
                    # Create/find route
                    route_query = """
                    SELECT r.id FROM routes r
                    JOIN airports o ON r.origin_id = o.id
                    JOIN airports d ON r.destination_id = d.id
                    WHERE o.code = :origin AND d.code = :destination
                    """
                    route_result = await database.fetch_one(route_query, {
                        "origin": origin_code,
                        "destination": destination_code
                    })
                    
                    if not route_result:
                        # Get airport IDs
                        origin_query = "SELECT id FROM airports WHERE code = :code"
                        dest_query = "SELECT id FROM airports WHERE code = :code"
                        origin_result = await database.fetch_one(origin_query, {"code": origin_code})
                        dest_result = await database.fetch_one(dest_query, {"code": destination_code})
                        
                        if origin_result and dest_result:
                            route_id = str(uuid.uuid4())
                            route_insert = """
                            INSERT INTO routes (id, origin_id, destination_id, typical_duration_min, created_at)
                            VALUES (:id, :origin_id, :destination_id, :typical_duration_min, :created_at)
                            """
                            await database.execute(route_insert, {
                                "id": route_id,
                                "origin_id": str(origin_result['id']),
                                "destination_id": str(dest_result['id']),
                                "typical_duration_min": int(flight_duration) if pd.notna(flight_duration) else None,
                                "created_at": datetime.now(timezone.utc)
                            })
                    else:
                        route_id = str(route_result['id'])
                else:
                    await log_import_error(import_run_id, idx + 1, "PARSING_ERROR", 
                                         f"Could not parse origin/destination from flight title: {flight_title}", 
                                         row.to_dict())
                
                # Find aircraft and operator
                aircraft_query = "SELECT id, operator_id, type FROM aircraft WHERE name = :name OR external_ref = :external_ref"
                aircraft_result = await database.fetch_one(aircraft_query, {
                    "name": str(airplane_id) if airplane_id else "",
                    "external_ref": str(airplane_id) if airplane_id else ""
                })
                
                if not aircraft_result:
                    raise ValueError(f"Aircraft with ID/name '{airplane_id}' not found")
                
                aircraft_id = str(aircraft_result['id'])
                operator_id_found = str(aircraft_result['operator_id'])
                aircraft_type = aircraft_result['type']
                
                # Create listing
                listing_id = str(uuid.uuid4())
                listing_insert = """
                INSERT INTO listings (id, operator_id, aircraft_id, route_id, title, description, departure_days, max_load_weight_lbs, external_ref, created_at, updated_at)
                VALUES (:id, :operator_id, :aircraft_id, :route_id, :title, :description, :departure_days, :max_load_weight_lbs, :external_ref, :created_at, :updated_at)
                """
                await database.execute(listing_insert, {
                    "id": listing_id,
                    "operator_id": operator_id_found,
                    "aircraft_id": aircraft_id,
                    "route_id": route_id,
                    "title": flight_title,
                    "description": description,
                    "departure_days": departure_days,
                    "max_load_weight_lbs": max_load_weight,
                    "external_ref": str(row.get('id', idx + 1)),
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                })
                
                # Create pricebook entry if pricing data exists
                if price_without_itbms > 0 and route_id:
                    origin_result = await database.fetch_one("SELECT origin_id, destination_id FROM routes WHERE id = :id", {"id": route_id})
                    if origin_result:
                        pricebook_id = str(uuid.uuid4())
                        pricebook_insert = """
                        INSERT INTO pricebook (id, operator_id, aircraft_type, origin_id, destination_id, base_price, currency, created_at)
                        VALUES (:id, :operator_id, :aircraft_type, :origin_id, :destination_id, :base_price, :currency, :created_at)
                        ON CONFLICT (operator_id, aircraft_type, origin_id, destination_id) DO UPDATE SET
                            base_price = EXCLUDED.base_price,
                            updated_at = :updated_at
                        """
                        await database.execute(pricebook_insert, {
                            "id": pricebook_id,
                            "operator_id": operator_id_found,
                            "aircraft_type": aircraft_type,
                            "origin_id": str(origin_result['origin_id']),
                            "destination_id": str(origin_result['destination_id']),
                            "base_price": price_without_itbms,
                            "currency": "USD",
                            "created_at": datetime.now(timezone.utc),
                            "updated_at": datetime.now(timezone.utc)
                        })
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                await log_import_error(import_run_id, idx + 1, "PROCESSING_ERROR", str(e), row.to_dict())
        
        await complete_import_run(import_run_id, success_count, error_count, {
            "flights_created": success_count,
            "errors": error_count
        })
        
        return {
            "import_run_id": import_run_id,
            "success_count": success_count,
            "error_count": error_count,
            "message": f"Processed {success_count + error_count} rows, {success_count} successful, {error_count} errors"
        }
        
    except Exception as e:
        logger.error(f"Error importing flights: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@api_router.post("/admin/import/airports")
async def import_airports(file: UploadFile = File(...)):
    """Import airports from CSV file (destinations_template.csv)"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV (.csv)")
    
    try:
        df = pd.read_csv(file.file)
        import_run_id = await create_import_run("airports", file.filename, len(df))
        success_count = 0
        error_count = 0
        
        for idx, row in df.iterrows():
            try:
                code = row.get('code', '').strip().upper()
                name = row.get('name', '').strip()
                city = row.get('city', '').strip()
                country = row.get('country', '').strip()
                latitude = float(row.get('latitude')) if pd.notna(row.get('latitude')) else None
                longitude = float(row.get('longitude')) if pd.notna(row.get('longitude')) else None
                timezone_str = row.get('timezone', 'America/Panama').strip()
                
                if not code or not name or not city or not country:
                    raise ValueError("Code, name, city, and country are required")
                
                # Upsert airport
                airport_id = str(uuid.uuid4())
                airport_upsert = """
                INSERT INTO airports (id, code, name, city, country, latitude, longitude, timezone, created_at, updated_at)
                VALUES (:id, :code, :name, :city, :country, :latitude, :longitude, :timezone, :created_at, :updated_at)
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                    city = EXCLUDED.city,
                    country = EXCLUDED.country,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    timezone = EXCLUDED.timezone,
                    updated_at = EXCLUDED.updated_at
                """
                await database.execute(airport_upsert, {
                    "id": airport_id,
                    "code": code,
                    "name": name,
                    "city": city,
                    "country": country,
                    "latitude": latitude,
                    "longitude": longitude,
                    "timezone": timezone_str,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                })
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                await log_import_error(import_run_id, idx + 1, "PROCESSING_ERROR", str(e), row.to_dict())
        
        await complete_import_run(import_run_id, success_count, error_count, {
            "airports_created": success_count,
            "errors": error_count
        })
        
        return {
            "import_run_id": import_run_id,
            "success_count": success_count,
            "error_count": error_count,
            "message": f"Processed {success_count + error_count} rows, {success_count} successful, {error_count} errors"
        }
        
    except Exception as e:
        logger.error(f"Error importing airports: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@api_router.post("/admin/import/routes")
async def import_routes(file: UploadFile = File(...)):
    """Import routes from CSV file (routes_template.csv)"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV (.csv)")
    
    try:
        df = pd.read_csv(file.file)
        import_run_id = await create_import_run("routes", file.filename, len(df))
        success_count = 0
        error_count = 0
        
        for idx, row in df.iterrows():
            try:
                origin_code = row.get('origin_code', '').strip().upper()
                destination_code = row.get('destination_code', '').strip().upper()
                duration_min = int(row.get('duration_min')) if pd.notna(row.get('duration_min')) else None
                distance_km = float(row.get('distance_km')) if pd.notna(row.get('distance_km')) else None
                notes = row.get('notes', '').strip() if pd.notna(row.get('notes')) else None
                
                if not origin_code or not destination_code:
                    raise ValueError("Origin and destination codes are required")
                
                # Find airports
                origin_query = "SELECT id FROM airports WHERE code = :code"
                dest_query = "SELECT id FROM airports WHERE code = :code"
                origin_result = await database.fetch_one(origin_query, {"code": origin_code})
                dest_result = await database.fetch_one(dest_query, {"code": destination_code})
                
                if not origin_result:
                    raise ValueError(f"Origin airport '{origin_code}' not found")
                if not dest_result:
                    raise ValueError(f"Destination airport '{destination_code}' not found")
                
                # Upsert route
                route_id = str(uuid.uuid4())
                route_upsert = """
                INSERT INTO routes (id, origin_id, destination_id, typical_duration_min, distance_km, notes, created_at, updated_at)
                VALUES (:id, :origin_id, :destination_id, :typical_duration_min, :distance_km, :notes, :created_at, :updated_at)
                ON CONFLICT (origin_id, destination_id) DO UPDATE SET
                    typical_duration_min = EXCLUDED.typical_duration_min,
                    distance_km = EXCLUDED.distance_km,
                    notes = EXCLUDED.notes,
                    updated_at = EXCLUDED.updated_at
                """
                await database.execute(route_upsert, {
                    "id": route_id,
                    "origin_id": str(origin_result['id']),
                    "destination_id": str(dest_result['id']),
                    "typical_duration_min": duration_min,
                    "distance_km": distance_km,
                    "notes": notes,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                })
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                await log_import_error(import_run_id, idx + 1, "PROCESSING_ERROR", str(e), row.to_dict())
        
        await complete_import_run(import_run_id, success_count, error_count, {
            "routes_created": success_count,
            "errors": error_count
        })
        
        return {
            "import_run_id": import_run_id,
            "success_count": success_count,
            "error_count": error_count,
            "message": f"Processed {success_count + error_count} rows, {success_count} successful, {error_count} errors"
        }
        
    except Exception as e:
        logger.error(f"Error importing routes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

# Get import run status
@api_router.get("/admin/import/{import_run_id}/status")
async def get_import_status(import_run_id: str):
    """Get import run status and errors"""
    # Get import run
    run_query = "SELECT * FROM import_runs WHERE id = :id"
    run_result = await database.fetch_one(run_query, {"id": import_run_id})
    
    if not run_result:
        raise HTTPException(status_code=404, detail="Import run not found")
    
    # Get errors
    errors_query = "SELECT * FROM import_errors WHERE import_run_id = :id ORDER BY row_number"
    errors = await database.fetch_all(errors_query, {"id": import_run_id})
    
    return {
        "import_run": dict(run_result),
        "errors": [dict(error) for error in errors]
    }

# Download import errors as CSV
@api_router.get("/admin/import/{import_run_id}/errors.csv")
async def download_import_errors(import_run_id: str):
    """Download import errors as CSV"""
    from fastapi.responses import StreamingResponse
    import io
    
    errors_query = "SELECT * FROM import_errors WHERE import_run_id = :id ORDER BY row_number"
    errors = await database.fetch_all(errors_query, {"id": import_run_id})
    
    if not errors:
        raise HTTPException(status_code=404, detail="No errors found for this import run")
    
    # Create CSV
    df = pd.DataFrame([dict(error) for error in errors])
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(csv_buffer.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=import_errors_{import_run_id}.csv"}
    )

# Basic health check
@api_router.get("/")
async def root():
    return {"message": "Charter Aviation System API", "status": "running", "version": "1.0.0"}

# Health check
@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        await database.fetch_one("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    try:
        # Check Redis
        await redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "unhealthy",
        "database": db_status,
        "redis": redis_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Quote Endpoints

@api_router.post("/quotes", response_model=QuoteResponse)
async def create_quote(quote_request: QuoteRequest):
    """Create a quote using the real pricing engine"""
    try:
        # Calculate quote using pricing engine
        pricing_result = await quoting_engine.calculate_quote(
            listing_id=quote_request.listing_id,
            passengers=quote_request.passengers,
            departure_date=quote_request.departure_date,
            return_date=quote_request.return_date,
            trip_type=quote_request.trip_type
        )
        
        # Create quote record
        quote_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(hours=int(os.environ.get('QUOTE_TTL_HOURS', 24)))
        hosted_url = f"https://charter.example.com/quote/{quote_id}"  # TODO: Configure proper domain
        
        quote_insert = """
        INSERT INTO quotes (id, listing_id, customer_email, customer_phone, passengers, 
                          departure_date, return_date, trip_type, base_price, surcharges, 
                          taxes, service_fee, total_price, currency, expires_at, hosted_url, created_at)
        VALUES (:id, :listing_id, :customer_email, :customer_phone, :passengers,
                :departure_date, :return_date, :trip_type, :base_price, :surcharges,
                :taxes, :service_fee, :total_price, :currency, :expires_at, :hosted_url, :created_at)
        """
        
        await database.execute(quote_insert, {
            "id": quote_id,
            "listing_id": quote_request.listing_id,
            "customer_email": quote_request.customer_email,
            "customer_phone": quote_request.customer_phone,
            "passengers": quote_request.passengers,
            "departure_date": quote_request.departure_date,
            "return_date": quote_request.return_date,
            "trip_type": quote_request.trip_type,
            "base_price": pricing_result['base_price'],
            "surcharges": pricing_result['surcharges'],
            "taxes": pricing_result['taxes'],
            "service_fee": pricing_result['service_fee'],
            "total_price": pricing_result['total_price'],
            "currency": pricing_result['currency'],
            "expires_at": expires_at,
            "hosted_url": hosted_url,
            "created_at": datetime.now(timezone.utc)
        })
        
        return QuoteResponse(
            id=quote_id,
            base_price=pricing_result['base_price'],
            surcharges=pricing_result['surcharges'],
            taxes=pricing_result['taxes'],
            service_fee=pricing_result['service_fee'],
            total_price=pricing_result['total_price'],
            currency=pricing_result['currency'],
            expires_at=expires_at,
            hosted_url=hosted_url
        )
        
    except Exception as e:
        logger.error(f"Error creating quote: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/quotes/{quote_id}")
async def get_quote(quote_id: str):
    """Get quote details"""
    quote_query = """
    SELECT q.*, l.title as listing_title, 
           o_orig.code as origin_code, o_dest.code as destination_code,
           a.name as aircraft_name, a.type as aircraft_type
    FROM quotes q
    JOIN listings l ON q.listing_id = l.id
    LEFT JOIN routes r ON l.route_id = r.id
    LEFT JOIN airports o_orig ON r.origin_id = o_orig.id
    LEFT JOIN airports o_dest ON r.destination_id = o_dest.id
    LEFT JOIN aircraft a ON l.aircraft_id = a.id
    WHERE q.id = :quote_id
    """
    
    quote = await database.fetch_one(quote_query, {"quote_id": quote_id})
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    return dict(quote)

# Availability Management

@api_router.post("/ops/slots")
async def create_availability_slot(slot_data: dict):
    """Create availability slot for aircraft"""
    try:
        aircraft_id = slot_data.get('aircraft_id')
        start_datetime = datetime.fromisoformat(slot_data.get('start_datetime'))
        end_datetime = datetime.fromisoformat(slot_data.get('end_datetime'))
        slot_type = slot_data.get('slot_type', 'AVAILABLE')
        notes = slot_data.get('notes')
        
        if not aircraft_id or not start_datetime or not end_datetime:
            raise ValueError("Aircraft ID, start datetime, and end datetime are required")
        
        if start_datetime >= end_datetime:
            raise ValueError("Start datetime must be before end datetime")
        
        # Check for overlapping slots
        overlap_query = """
        SELECT id FROM availability_slots 
        WHERE aircraft_id = :aircraft_id 
        AND (
            (start_datetime <= :start_datetime AND end_datetime > :start_datetime) OR
            (start_datetime < :end_datetime AND end_datetime >= :end_datetime) OR
            (start_datetime >= :start_datetime AND end_datetime <= :end_datetime)
        )
        """
        
        overlapping = await database.fetch_one(overlap_query, {
            "aircraft_id": aircraft_id,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime
        })
        
        if overlapping:
            raise ValueError("Slot overlaps with existing availability slot")
        
        # Create slot
        slot_id = str(uuid.uuid4())
        slot_insert = """
        INSERT INTO availability_slots (id, aircraft_id, start_datetime, end_datetime, slot_type, notes, created_at)
        VALUES (:id, :aircraft_id, :start_datetime, :end_datetime, :slot_type, :notes, :created_at)
        """
        
        await database.execute(slot_insert, {
            "id": slot_id,
            "aircraft_id": aircraft_id,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "slot_type": slot_type,
            "notes": notes,
            "created_at": datetime.now(timezone.utc)
        })
        
        return {"id": slot_id, "message": "Availability slot created successfully"}
        
    except Exception as e:
        logger.error(f"Error creating availability slot: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/availability")
async def get_availability(aircraft_id: str, date_range: str):
    """
    Get availability for aircraft in date range
    Format: date_range=YYYY-MM-DD/YYYY-MM-DD
    Returns: Available slots minus busy blocks, holds, and bookings
    """
    try:
        # Parse date range
        start_date_str, end_date_str = date_range.split('/')
        start_date = datetime.fromisoformat(start_date_str + "T00:00:00Z").replace(tzinfo=timezone.utc)
        end_date = datetime.fromisoformat(end_date_str + "T23:59:59Z").replace(tzinfo=timezone.utc)
        
        # Get availability slots
        slots_query = """
        SELECT * FROM availability_slots 
        WHERE aircraft_id = :aircraft_id 
        AND start_datetime <= :end_date AND end_datetime >= :start_date
        AND slot_type = 'AVAILABLE'
        ORDER BY start_datetime
        """
        
        slots = await database.fetch_all(slots_query, {
            "aircraft_id": aircraft_id,
            "start_date": start_date,
            "end_date": end_date
        })
        
        # Get busy blocks
        busy_query = """
        SELECT * FROM busy_blocks 
        WHERE aircraft_id = :aircraft_id 
        AND start_datetime <= :end_date AND end_datetime >= :start_date
        ORDER BY start_datetime
        """
        
        busy_blocks = await database.fetch_all(busy_query, {
            "aircraft_id": aircraft_id,
            "start_date": start_date,
            "end_date": end_date
        })
        
        # Get active holds from Redis
        hold_keys = await redis_client.keys(f"hold:*:{aircraft_id}:*")
        active_holds = []
        
        for key in hold_keys:
            hold_data = await redis_client.get(key)
            if hold_data:
                hold_info = json.loads(hold_data)
                hold_start = datetime.fromisoformat(hold_info['start_datetime'])
                hold_end = datetime.fromisoformat(hold_info['end_datetime'])
                
                if hold_start <= end_date and hold_end >= start_date:
                    active_holds.append({
                        'start_datetime': hold_info['start_datetime'],
                        'end_datetime': hold_info['end_datetime'],
                        'hold_id': hold_info['hold_id']
                    })
        
        # Get confirmed bookings
        booking_query = """
        SELECT h.start_datetime, h.end_datetime FROM bookings b
        JOIN holds h ON b.hold_id = h.id
        WHERE h.aircraft_id = :aircraft_id AND b.status IN ('CONFIRMED', 'PAID')
        AND h.start_datetime <= :end_date AND h.end_datetime >= :start_date
        ORDER BY h.start_datetime
        """
        
        bookings = await database.fetch_all(booking_query, {
            "aircraft_id": aircraft_id,
            "start_date": start_date,
            "end_date": end_date
        })
        
        return {
            "aircraft_id": aircraft_id,
            "date_range": date_range,
            "available_slots": [dict(slot) for slot in slots],
            "busy_blocks": [dict(block) for block in busy_blocks],
            "active_holds": active_holds,
            "confirmed_bookings": [dict(booking) for booking in bookings],
            "summary": {
                "total_slots": len(slots),
                "busy_blocks": len(busy_blocks),
                "active_holds": len(active_holds),
                "confirmed_bookings": len(bookings)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting availability: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Hold Management

@api_router.post("/holds")
async def create_hold(hold_data: dict):
    """Create a hold on aircraft availability"""
    try:
        aircraft_id = hold_data.get('aircraft_id')
        quote_id = hold_data.get('quote_id')
        start_datetime = datetime.fromisoformat(hold_data.get('start_datetime'))
        end_datetime = datetime.fromisoformat(hold_data.get('end_datetime'))
        
        if not aircraft_id or not start_datetime or not end_datetime:
            raise ValueError("Aircraft ID, start datetime, and end datetime are required")
        
        # Generate hold ID and Redis key
        hold_id = str(uuid.uuid4())
        redis_key = f"hold:{hold_id}:{aircraft_id}:{int(start_datetime.timestamp())}"
        
        # Hold TTL in minutes
        ttl_minutes = int(os.environ.get('HOLD_TTL_MINUTES', 15))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
        
        # Check for conflicts (atomic operation using Redis SETNX)
        conflict_keys = await redis_client.keys(f"hold:*:{aircraft_id}:*")
        
        for key in conflict_keys:
            existing_hold = await redis_client.get(key)
            if existing_hold:
                existing_data = json.loads(existing_hold)
                existing_start = datetime.fromisoformat(existing_data['start_datetime'])
                existing_end = datetime.fromisoformat(existing_data['end_datetime'])
                
                # Check for time conflict
                if (start_datetime < existing_end and end_datetime > existing_start):
                    raise HTTPException(status_code=409, detail="Time slot is already held")
        
        # Create hold in Redis with TTL
        hold_data_json = {
            "hold_id": hold_id,
            "aircraft_id": aircraft_id,
            "quote_id": quote_id,
            "start_datetime": start_datetime.isoformat(),
            "end_datetime": end_datetime.isoformat(),
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Use SETNX for atomic operation
        success = await redis_client.set(redis_key, json.dumps(hold_data_json), nx=True, ex=ttl_minutes * 60)
        
        if not success:
            raise HTTPException(status_code=409, detail="Could not acquire hold - slot may be taken")
        
        # Create hold record in database
        hold_insert = """
        INSERT INTO holds (id, aircraft_id, quote_id, start_datetime, end_datetime, redis_key, expires_at, created_at)
        VALUES (:id, :aircraft_id, :quote_id, :start_datetime, :end_datetime, :redis_key, :expires_at, :created_at)
        """
        
        await database.execute(hold_insert, {
            "id": hold_id,
            "aircraft_id": aircraft_id,
            "quote_id": quote_id,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "redis_key": redis_key,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc)
        })
        
        return {
            "hold_id": hold_id,
            "expires_at": expires_at.isoformat(),
            "ttl_minutes": ttl_minutes,
            "message": "Hold created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating hold: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/holds/{hold_id}")
async def release_hold(hold_id: str):
    """Release a hold"""
    try:
        # Get hold from database
        hold_query = "SELECT redis_key, status FROM holds WHERE id = :hold_id"
        hold = await database.fetch_one(hold_query, {"hold_id": hold_id})
        
        if not hold:
            raise HTTPException(status_code=404, detail="Hold not found")
        
        if hold['status'] != 'ACTIVE':
            raise HTTPException(status_code=400, detail="Hold is not active")
        
        # Remove from Redis
        await redis_client.delete(hold['redis_key'])
        
        # Update hold status
        hold_update = "UPDATE holds SET status = 'RELEASED', updated_at = :updated_at WHERE id = :hold_id"
        await database.execute(hold_update, {
            "hold_id": hold_id,
            "updated_at": datetime.now(timezone.utc)
        })
        
        return {"message": "Hold released successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error releasing hold: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/holds/{hold_id}")
async def get_hold_status(hold_id: str):
    """Get hold status"""
    hold_query = "SELECT * FROM holds WHERE id = :hold_id"
    hold = await database.fetch_one(hold_query, {"hold_id": hold_id})
    
    if not hold:
        raise HTTPException(status_code=404, detail="Hold not found")
    
    # Check if still active in Redis
    redis_status = await redis_client.get(hold['redis_key'])
    is_active_in_redis = redis_status is not None
    
    hold_dict = dict(hold)
    hold_dict['active_in_redis'] = is_active_in_redis
    
    return hold_dict

# Include the router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server_postgres:app", host="0.0.0.0", port=8001, reload=True)