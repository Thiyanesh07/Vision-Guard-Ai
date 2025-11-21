from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Float, JSON, DateTime
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from shapely.geometry import Point
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

DATABASE_URL = settings.database_url

# Create async engine and session
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Incident model
class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True)
    incident_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    frame_urls = Column(JSON, nullable=False)
    verification_status = Column(String, default="pending")
    location = Column(Geometry("POINT"), nullable=False)

# Dependency for database session
async def get_db():
    async with async_session() as session:
        yield session