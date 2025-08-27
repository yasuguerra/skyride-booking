"""
SkyRide Server Launcher
Automatically selects between MongoDB and PostgreSQL server based on DB_BACKEND setting
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check which database backend to use
db_backend = os.getenv('DB_BACKEND', 'mongo').lower()

print(f"🔍 DB_BACKEND setting: {db_backend}", file=sys.stderr)
print(f"🔍 Environment loaded from: {os.path.abspath('.env')}", file=sys.stderr)

if db_backend == 'postgres':
    # Import and use PostgreSQL server
    from server_postgres import app
    print("🚀 Starting SkyRide with PostgreSQL backend", file=sys.stderr)
else:
    # Import and use MongoDB server (default)
    from server import app  
    print("🚀 Starting SkyRide with MongoDB backend", file=sys.stderr)

# The app is now available as 'app' for uvicorn