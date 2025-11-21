"""Quick status checker for all Smart City AI services"""
import requests
import redis
from config import settings

def check_services():
    status = {
        "PostgreSQL": False,
        "Redis": False,
        "MinIO": False,
        "FastAPI": False,
        "Overall": False
    }
    
    # Check Redis
    try:
        r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=settings.redis_db)
        r.ping()
        status["Redis"] = True
        print("✓ Redis: Running")
    except Exception as e:
        print(f"✗ Redis: Not running ({e})")
    
    # Check MinIO
    try:
        response = requests.get(f"http://{settings.minio_endpoint}/minio/health/live", timeout=2)
        if response.status_code == 200:
            status["MinIO"] = True
            print("✓ MinIO: Running")
    except Exception as e:
        print(f"✗ MinIO: Not running ({e})")
    
    # Check FastAPI
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            status["FastAPI"] = True
            print("✓ FastAPI: Running")
    except Exception as e:
        print(f"✗ FastAPI: Not running ({e})")
    
    # Check PostgreSQL (via FastAPI health)
    if status["FastAPI"]:
        status["PostgreSQL"] = True
        print("✓ PostgreSQL: Running (verified via API)")
    else:
        print("? PostgreSQL: Cannot verify (API not running)")
    
    status["Overall"] = all([status["Redis"], status["MinIO"], status["FastAPI"]])
    
    print("\n" + "="*50)
    if status["Overall"]:
        print("🎉 ALL SERVICES RUNNING - System Ready!")
    else:
        print("⚠️  Some services not running - Check above")
    print("="*50)
    
    return status

if __name__ == "__main__":
    check_services()
