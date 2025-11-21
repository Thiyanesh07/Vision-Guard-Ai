import redis
import json

def publish_event(event):
    """
    Publishes an event to the Redis channel.

    Args:
        event (dict): The event payload to publish.
    """
    redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
    channel = 'events'
    redis_client.publish(channel, json.dumps(event))

if __name__ == "__main__":
    # Example event payload
    event = {
        "id": "incident_123",
        "incident": "accident",
        "confidence": 0.85,
        "frames": [
            "s3://frames/incident_123_f1.jpg",
            "s3://frames/incident_123_f2.jpg"
        ],
        "timestamp": "2025-11-18T12:00:00Z",
        "location": {
            "lat": 11.0222,
            "lon": 77.0133
        }
    }

    publish_event(event)