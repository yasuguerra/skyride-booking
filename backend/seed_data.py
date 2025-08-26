#!/usr/bin/env python3
"""
SkyRide Database Seeder
Seeds the database with sample operators, aircraft, routes, and listings
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from pathlib import Path

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def seed_database():
    """Seed the database with sample data"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🌱 Seeding SkyRide database...")
    
    # Clear existing data
    collections = ['operators', 'aircraft', 'routes', 'listings', 'quotes', 'holds', 'bookings', 'customers', 'payments']
    for collection in collections:
        await db[collection].delete_many({})
        print(f"   Cleared {collection}")
    
    # Sample Operators
    operators = [
        {
            "_id": "op_panama_elite",
            "name": "Panama Elite Aviation",
            "code": "PEA001", 
            "email": "ops@panamaelite.com",
            "phone": "+507-6789-1234",
            "website": "https://panamaelite.com",
            "logo": "https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=200&h=200&fit=crop&crop=center",
            "active": True,
            "distributionOptIn": True,
            "priceFloor": 2500.0,
            "emptyLegWindow": 180,
            "acceptanceRate": 0.92,
            "avgResponseTime": 1200,
            "cancelationRate": 0.03,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "op_sky_charter",
            "name": "Sky Charter Panama",
            "code": "SCP002",
            "email": "bookings@skycharter.pa",
            "phone": "+507-6789-5678", 
            "website": "https://skycharter.pa",
            "logo": "https://images.unsplash.com/photo-1540979388789-6cee28a1cdc9?w=200&h=200&fit=crop&crop=center",
            "active": True,
            "distributionOptIn": True,
            "priceFloor": 3000.0,
            "emptyLegWindow": 120,
            "acceptanceRate": 0.89,
            "avgResponseTime": 900,
            "cancelationRate": 0.05,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.operators.insert_many(operators)
    print(f"   ✅ Created {len(operators)} operators")
    
    # Sample Aircraft
    aircraft = [
        {
            "_id": "ac_bell407_1",
            "operatorId": "op_panama_elite",
            "model": "Bell 407",
            "registration": "HP-2001PE",
            "capacity": 6,
            "hourlyRate": 3500.0,
            "images": [
                "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop",
                "https://images.unsplash.com/photo-1540979388789-6cee28a1cdc9?w=800&h=600&fit=crop"
            ],
            "active": True,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "ac_bell206_1", 
            "operatorId": "op_panama_elite",
            "model": "Bell 206",
            "registration": "HP-2002PE",
            "capacity": 4,
            "hourlyRate": 2800.0,
            "images": [
                "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop"
            ],
            "active": True,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "ac_as350_1",
            "operatorId": "op_sky_charter", 
            "model": "Airbus AS350",
            "registration": "HP-3001SC",
            "capacity": 5,
            "hourlyRate": 4200.0,
            "images": [
                "https://images.unsplash.com/photo-1540979388789-6cee28a1cdc9?w=800&h=600&fit=crop"
            ],
            "active": True,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.aircraft.insert_many(aircraft)
    print(f"   ✅ Created {len(aircraft)} aircraft")
    
    # Sample Routes
    routes = [
        {
            "_id": "rt_ptyctr_sancarlo",
            "origin": "Panama City",
            "destination": "San Carlos",
            "distance": 180.0,
            "duration": 75,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "rt_ptyctr_bocas",
            "origin": "Panama City", 
            "destination": "Bocas del Toro",
            "distance": 320.0,
            "duration": 130,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "rt_ptyctr_david",
            "origin": "Panama City",
            "destination": "David",
            "distance": 380.0,
            "duration": 150,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "rt_ptyctr_colon",
            "origin": "Panama City",
            "destination": "Colon",
            "distance": 95.0,
            "duration": 45,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.routes.insert_many(routes)
    print(f"   ✅ Created {len(routes)} routes")
    
    # Sample Listings
    listings = [
        {
            "_id": "ls_ptyctr_sancarlo_bell407",
            "operatorId": "op_panama_elite",
            "aircraftId": "ac_bell407_1",
            "routeId": "rt_ptyctr_sancarlo",
            "type": "CHARTER",
            "status": "ACTIVE",
            "basePrice": 4200.0,
            "serviceFee": 210.0,
            "totalPrice": 4410.0,
            "maxPassengers": 6,
            "confirmationSLA": 2,
            "title": "Panama City to San Carlos Charter",
            "description": "Luxury helicopter charter service to San Carlos with stunning aerial views of Panama's coastline.",
            "amenities": ["WiFi", "Refreshments", "Noise-canceling headsets", "Photography service"],
            "images": [
                "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop",
                "https://images.unsplash.com/photo-1540979388789-6cee28a1cdc9?w=800&h=600&fit=crop"
            ],
            "featured": True,
            "boosted": False,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "ls_ptyctr_bocas_as350",
            "operatorId": "op_sky_charter",
            "aircraftId": "ac_as350_1", 
            "routeId": "rt_ptyctr_bocas",
            "type": "CHARTER",
            "status": "ACTIVE",
            "basePrice": 8400.0,
            "serviceFee": 420.0,
            "totalPrice": 8820.0,
            "maxPassengers": 5,
            "confirmationSLA": 3,
            "title": "Panama City to Bocas del Toro Charter",
            "description": "Premium helicopter charter to the beautiful Bocas del Toro archipelago.",
            "amenities": ["WiFi", "Gourmet catering", "Champagne service", "Professional photography"],
            "images": [
                "https://images.unsplash.com/photo-1540979388789-6cee28a1cdc9?w=800&h=600&fit=crop"
            ],
            "featured": True,
            "boosted": True,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "ls_ptyctr_david_bell206",
            "operatorId": "op_panama_elite",
            "aircraftId": "ac_bell206_1",
            "routeId": "rt_ptyctr_david",
            "type": "CHARTER", 
            "status": "ACTIVE",
            "basePrice": 6200.0,
            "serviceFee": 310.0,
            "totalPrice": 6510.0,
            "maxPassengers": 4,
            "confirmationSLA": 4,
            "title": "Panama City to David Charter",
            "description": "Convenient helicopter charter service to David, perfect for business or leisure travel.",
            "amenities": ["WiFi", "Light refreshments", "Noise-canceling headsets"],
            "images": [
                "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop"
            ],
            "featured": False,
            "boosted": False,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "ls_ptyctr_colon_bell407",
            "operatorId": "op_panama_elite",
            "aircraftId": "ac_bell407_1",
            "routeId": "rt_ptyctr_colon",
            "type": "CHARTER",
            "status": "ACTIVE", 
            "basePrice": 2800.0,
            "serviceFee": 140.0,
            "totalPrice": 2940.0,
            "maxPassengers": 6,
            "confirmationSLA": 1,
            "title": "Panama City to Colon Express",
            "description": "Quick helicopter shuttle service to Colon, ideal for cruise connections.",
            "amenities": ["WiFi", "Express boarding", "Luggage assistance"],
            "images": [
                "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop"
            ],
            "featured": False,
            "boosted": False,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.listings.insert_many(listings)
    print(f"   ✅ Created {len(listings)} listings")
    
    # Sample Customer
    customers = [
        {
            "_id": "cust_demo_001",
            "email": "demo@skyride.city",
            "phone": "+507-6000-1234",
            "firstName": "Demo",
            "lastName": "User",
            "preferredLanguage": "en",
            "marketingOptIn": True,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.customers.insert_many(customers)
    print(f"   ✅ Created {len(customers)} customers")
    
    # Sample Policies
    policies = [
        {
            "_id": "pol_cancellation",
            "name": "Cancellation Policy",
            "type": "cancellation",
            "content": "<h3>SkyRide Cancellation Policy</h3><p>Free cancellation up to 24 hours before departure. Cancellations within 24 hours are subject to a 50% fee.</p>",
            "version": "1.0",
            "active": True,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "pol_protection",
            "name": "Sky Ride Protection",
            "type": "protection", 
            "content": "<h3>Sky Ride Protection</h3><ul><li>Weather delay coverage</li><li>Aircraft substitution guarantee</li><li>24/7 concierge support</li><li>Full refund protection</li></ul>",
            "version": "1.0",
            "active": True,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.policies.insert_many(policies)
    print(f"   ✅ Created {len(policies)} policies")
    
    print("\n🎉 Database seeding completed successfully!")
    print("\nSample data created:")
    print(f"   - {len(operators)} Operators")  
    print(f"   - {len(aircraft)} Aircraft")
    print(f"   - {len(routes)} Routes")
    print(f"   - {len(listings)} Listings")
    print(f"   - {len(customers)} Customers")
    print(f"   - {len(policies)} Policies")
    
    print("\n🔗 Test the platform:")
    print(f"   - Visit: {os.getenv('BASE_URL', 'http://localhost:3000')}")
    print(f"   - API Health: {os.getenv('BASE_URL', 'http://localhost:3000')}/api/health")
    
    # Close connection
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())