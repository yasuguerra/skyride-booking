"""
PostgreSQL Database Configuration with SQLAlchemy
Migration from MongoDB to Postgres/Supabase
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration - Supabase with SSL support
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv(
    'POSTGRES_URL', 
    'sqlite+aiosqlite:///./skyride_postgres.db'  # SQLite for local dev only
)

# SSL configuration for Supabase
connect_args = {}
if "supabase.com" in DATABASE_URL or "sslmode=require" in DATABASE_URL:
    if DATABASE_URL.startswith("postgresql://"):
        connect_args = {
            "server_settings": {
                "application_name": "skyride_v2"
            }
        }

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_size=20,
    max_overflow=30,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base class for all models
Base = declarative_base()

# Dependency for FastAPI
async def get_session():
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

# Alias for compatibility
get_db = get_session

# Initialize database
async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Close database connections
async def close_db():
    """Close database connections"""
    await engine.dispose()