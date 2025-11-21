import redis
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
from tasks.celery_worker import process_incident, send_to_llm_service

def consume_events():
    """
    Consumes events from the Redis channel and triggers Celery tasks.
    """
    redis_client = redis.StrictRedis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db
    )
    pubsub = redis_client.pubsub()
    channel = 'events'
    pubsub.subscribe(channel)

    print(f"Redis Consumer started")
    print(f"Subscribed to Redis channel: {channel}")
    print(f"Waiting for events...")

    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                event = json.loads(message['data'])
                print(f"\n{'='*60}")
                print(f"Received event: {event['id']}")
                print(f"Incident Type: {event['incident']}")
                print(f"Confidence: {event['confidence']:.2f}")
                print(f"Frames: {len(event.get('frames', []))} uploaded")
                print(f"{'='*60}\n")
                
                # Trigger Celery tasks asynchronously
                
                # 1. Store incident in database
                process_incident.delay(event)
                print(f"✓ Queued database storage task for {event['id']}")
                
                # 2. Send to LLM service for verification (optional)
                # Uncomment when LLM service is ready
                # send_to_llm_service.delay(event)
                # print(f"✓ Queued LLM verification task for {event['id']}")
                
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
            except Exception as e:
                print(f"Error processing event: {e}")

if __name__ == "__main__":
    try:
        consume_events()
    except KeyboardInterrupt:
        print("\nShutting down Redis consumer...")
    except Exception as e:
        print(f"Fatal error: {e}")