"""
SkyRide Server Launcher
Automatically selects between MongoDB and PostgreSQL server based on DB_BACKEND setting
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check which database backend to use
db_backend = os.getenv('DB_BACKEND', 'mongo').lower()

if db_backend == 'postgres':
    # Import and use PostgreSQL server
    from server_postgres import app
    print("🚀 Starting SkyRide with PostgreSQL backend")
else:
    # Import and use MongoDB server (default)
    from server import app  
    print("🚀 Starting SkyRide with MongoDB backend")

# The app is now available as 'app' for uvicorn