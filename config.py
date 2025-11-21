from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database Configuration
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/smart_city_ai"
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    
    # MinIO Configuration
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket: str = "frames"
    
    # Vision Model Configuration
    yolo_model_path: str = "models/yolov11-nano.onnx"
    stream_url: str = "rtsp://example.com/stream"
    confidence_threshold: float = 0.5
    frame_buffer_size: int = 16
    frames_to_extract: int = 4
    
    # Location Configuration
    default_lat: float = 11.0222
    default_lon: float = 77.0133
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
