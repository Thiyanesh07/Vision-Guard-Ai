from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import Incident as IncidentModel, get_db, engine, Base
from config import settings

app = FastAPI(title="Smart City AI API", version="1.0.0")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Pydantic models
class Location(BaseModel):
    lat: float
    lon: float

class IncidentCreate(BaseModel):
    incident: str
    confidence: float
    frame_urls: List[str]
    timestamp: datetime
    location: Location

class Incident(BaseModel):
    id: str
    incident_type: str
    confidence: float
    frame_urls: List[str]
    timestamp: datetime
    location: Location
    verification_status: str = "pending"

    class Config:
        from_attributes = True

# Startup event to create tables
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/incidents/create", response_model=Incident)
async def create_incident(incident: IncidentCreate, db: AsyncSession = Depends(get_db)):
    # Create PostGIS point
    point = from_shape(Point(incident.location.lon, incident.location.lat), srid=4326)
    
    # Create incident
    db_incident = IncidentModel(
        id=f"incident_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        incident_type=incident.incident,
        confidence=incident.confidence,
        timestamp=incident.timestamp,
        frame_urls=incident.frame_urls,
        verification_status="pending",
        location=point
    )
    
    db.add(db_incident)
    await db.commit()
    await db.refresh(db_incident)
    
    # Extract location from geometry
    shape = to_shape(db_incident.location)
    location = Location(lat=shape.y, lon=shape.x)
    
    # Create response
    response = Incident(
        id=db_incident.id,
        incident_type=db_incident.incident_type,
        confidence=db_incident.confidence,
        frame_urls=db_incident.frame_urls,
        timestamp=db_incident.timestamp,
        location=location,
        verification_status=db_incident.verification_status
    )
    
    # Broadcast to WebSocket clients
    await manager.broadcast({
        "type": "new_incident",
        "data": response.dict()
    })
    
    return response

@app.get("/incidents/list", response_model=List[Incident])
async def list_incidents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IncidentModel))
    incidents = result.scalars().all()
    
    response = []
    for inc in incidents:
        shape = to_shape(inc.location)
        response.append(Incident(
            id=inc.id,
            incident_type=inc.incident_type,
            confidence=inc.confidence,
            frame_urls=inc.frame_urls,
            timestamp=inc.timestamp,
            location=Location(lat=shape.y, lon=shape.x),
            verification_status=inc.verification_status
        ))
    
    return response

@app.get("/incidents/{id}", response_model=Incident)
async def get_incident(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IncidentModel).where(IncidentModel.id == id))
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    shape = to_shape(incident.location)
    return Incident(
        id=incident.id,
        incident_type=incident.incident_type,
        confidence=incident.confidence,
        frame_urls=incident.frame_urls,
        timestamp=incident.timestamp,
        location=Location(lat=shape.y, lon=shape.x),
        verification_status=incident.verification_status
    )

@app.post("/verify/from_llm")
async def verify_from_llm(id: str, status: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IncidentModel).where(IncidentModel.id == id))
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident.verification_status = status
    await db.commit()
    
    # Broadcast update to WebSocket clients
    await manager.broadcast({
        "type": "incident_verified",
        "data": {"id": id, "status": status}
    })
    
    return {"id": id, "status": status}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}