"""
Test script to verify the Smart City AI system components
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_health():
    """Test API health endpoint"""
    print("Testing API Health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✓ API is healthy")
            return True
        else:
            print(f"✗ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ API connection failed: {e}")
        return False

def test_create_incident():
    """Test creating an incident"""
    print("\nTesting Incident Creation...")
    incident_data = {
        "incident": "accident",
        "confidence": 0.85,
        "frame_urls": [
            "http://localhost:9000/frames/test_frame_1.jpg",
            "http://localhost:9000/frames/test_frame_2.jpg"
        ],
        "timestamp": datetime.now().isoformat(),
        "location": {
            "lat": 11.0222,
            "lon": 77.0133
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/incidents/create", json=incident_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Incident created: {result['id']}")
            return result['id']
        else:
            print(f"✗ Failed to create incident: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"✗ Request failed: {e}")
        return None

def test_list_incidents():
    """Test listing incidents"""
    print("\nTesting Incident Listing...")
    try:
        response = requests.get(f"{BASE_URL}/incidents/list")
        if response.status_code == 200:
            incidents = response.json()
            print(f"✓ Found {len(incidents)} incidents")
            for inc in incidents:
                print(f"  - {inc['id']}: {inc['incident_type']} ({inc['verification_status']})")
            return True
        else:
            print(f"✗ Failed to list incidents: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {e}")
        return False

def test_get_incident(incident_id):
    """Test getting a specific incident"""
    print(f"\nTesting Get Incident {incident_id}...")
    try:
        response = requests.get(f"{BASE_URL}/incidents/{incident_id}")
        if response.status_code == 200:
            incident = response.json()
            print(f"✓ Retrieved incident:")
            print(f"  Type: {incident['incident_type']}")
            print(f"  Confidence: {incident['confidence']}")
            print(f"  Status: {incident['verification_status']}")
            print(f"  Location: {incident['location']}")
            return True
        else:
            print(f"✗ Failed to get incident: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {e}")
        return False

def test_verify_incident(incident_id):
    """Test verifying an incident"""
    print(f"\nTesting Incident Verification {incident_id}...")
    try:
        response = requests.post(
            f"{BASE_URL}/verify/from_llm",
            params={"id": incident_id, "status": "verified"}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Incident verified: {result}")
            return True
        else:
            print(f"✗ Failed to verify incident: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {e}")
        return False

def test_redis_connection():
    """Test Redis connection"""
    print("\nTesting Redis Connection...")
    try:
        import redis
        from config import settings
        client = redis.StrictRedis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db
        )
        client.ping()
        print("✓ Redis is connected")
        return True
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        return False

def test_minio_connection():
    """Test MinIO connection"""
    print("\nTesting MinIO Connection...")
    try:
        from storage.minio_client import minio_client, create_bucket_if_not_exists
        from config import settings
        
        # Check if MinIO is accessible
        create_bucket_if_not_exists(settings.minio_bucket)
        print(f"✓ MinIO is connected")
        print(f"  Bucket: {settings.minio_bucket}")
        return True
    except Exception as e:
        print(f"✗ MinIO connection failed: {e}")
        return False

def test_database_connection():
    """Test Database connection"""
    print("\nTesting Database Connection...")
    try:
        import asyncio
        from database.models import async_session
        
        async def check_db():
            async with async_session() as session:
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
        
        asyncio.run(check_db())
        print("✓ Database is connected")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Smart City AI - System Test")
    print("=" * 60)
    
    # Test infrastructure
    redis_ok = test_redis_connection()
    minio_ok = test_minio_connection()
    db_ok = test_database_connection()
    
    # Test API
    api_ok = test_health()
    
    if not api_ok:
        print("\n⚠ API is not running. Start it with:")
        print("uvicorn backend.main:app --reload")
        return
    
    # Test CRUD operations
    test_list_incidents()
    incident_id = test_create_incident()
    
    if incident_id:
        test_get_incident(incident_id)
        test_verify_incident(incident_id)
        test_list_incidents()
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"  Redis: {'✓' if redis_ok else '✗'}")
    print(f"  MinIO: {'✓' if minio_ok else '✗'}")
    print(f"  Database: {'✓' if db_ok else '✗'}")
    print(f"  API: {'✓' if api_ok else '✗'}")
    print("=" * 60)

if __name__ == "__main__":
    main()
