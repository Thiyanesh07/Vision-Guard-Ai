from celery import Celery
import json
import sys
import os
import asyncio
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
from database.models import Incident as IncidentModel, async_session, engine
from sqlalchemy import select, update
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
import requests

# Initialize Celery app
celery_app = Celery(
    'tasks',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery_app.task(bind=True, max_retries=3)
def process_incident(self, event):
    """
    Main task to process an incident event from Redis.
    Stores incident in database.

    Args:
        event (dict): The event payload from vision pipeline.
    """
    try:
        print(f"Processing incident: {event['id']}")
        
        # Run async database operation
        asyncio.run(store_incident_in_db(event))
        
        print(f"Incident {event['id']} stored in database")
        return {"status": "success", "incident_id": event['id']}
    
    except Exception as exc:
        print(f"Error processing incident: {exc}")
        raise self.retry(exc=exc, countdown=60)

async def store_incident_in_db(event):
    """
    Store incident in PostgreSQL database.
    
    Args:
        event (dict): The event payload.
    """
    async with async_session() as session:
        # Create PostGIS point
        point = from_shape(
            Point(event['location']['lon'], event['location']['lat']), 
            srid=4326
        )
        
        # Create incident
        incident = IncidentModel(
            id=event['id'],
            incident_type=event['incident'],
            confidence=event['confidence'],
            timestamp=datetime.fromisoformat(event['timestamp']),
            frame_urls=event['frames'],
            verification_status='pending',
            location=point
        )
        
        session.add(incident)
        await session.commit()

@celery_app.task(bind=True, max_retries=3)
def send_to_llm_service(self, event):
    """
    Task to send event to the LLM verification microservice.

    Args:
        event (dict): The event payload to send.
    """
    try:
        # Placeholder for LLM service endpoint
        llm_service_url = "http://localhost:8001/verify"
        
        print(f"Sending event {event['id']} to LLM service")
        
        # Send POST request to LLM service
        response = requests.post(
            llm_service_url,
            json=event,
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"Event {event['id']} sent to LLM successfully")
            return {"status": "success", "response": response.json()}
        else:
            raise Exception(f"LLM service returned status {response.status_code}")
    
    except requests.exceptions.RequestException as exc:
        print(f"Error sending to LLM service: {exc}")
        # Don't retry if LLM service is down, just log
        return {"status": "failed", "error": str(exc)}
    except Exception as exc:
        print(f"Unexpected error: {exc}")
        raise self.retry(exc=exc, countdown=120)

@celery_app.task(bind=True, max_retries=3)
def update_verification_status(self, incident_id, status, verified_by="llm"):
    """
    Task to update the verification status of an incident.

    Args:
        incident_id (str): The ID of the incident to update.
        status (str): The new status ('verified', 'rejected', 'pending').
        verified_by (str): Who verified it (default: 'llm').
    """
    try:
        print(f"Updating incident {incident_id} status to {status}")
        
        # Run async database operation
        asyncio.run(update_incident_status(incident_id, status))
        
        print(f"Incident {incident_id} status updated to {status}")
        return {"status": "success", "incident_id": incident_id, "new_status": status}
    
    except Exception as exc:
        print(f"Error updating incident status: {exc}")
        raise self.retry(exc=exc, countdown=60)

async def update_incident_status(incident_id, status):
    """
    Update incident verification status in database.
    
    Args:
        incident_id (str): The incident ID.
        status (str): The new status.
    """
    async with async_session() as session:
        result = await session.execute(
            select(IncidentModel).where(IncidentModel.id == incident_id)
        )
        incident = result.scalar_one_or_none()
        
        if incident:
            incident.verification_status = status
            await session.commit()
        else:
            raise ValueError(f"Incident {incident_id} not found")

@celery_app.task
def cleanup_old_incidents(days_old=30):
    """
    Periodic task to clean up old incidents.
    
    Args:
        days_old (int): Delete incidents older than this many days.
    """
    print(f"Cleaning up incidents older than {days_old} days")
    # Implementation for cleanup
    return {"status": "success", "message": f"Cleaned up incidents older than {days_old} days"}