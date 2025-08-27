from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database
import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost:5432/charter_db')
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()
Base = declarative_base()

# Async database connection
database = Database(DATABASE_URL)

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()