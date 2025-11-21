# Quick Setup Guide

## Prerequisites Installation (Windows)

### 1. Install PostgreSQL with PostGIS
1. Download PostgreSQL 14+ from https://www.postgresql.org/download/windows/
2. During installation, include Stack Builder
3. Use Stack Builder to install PostGIS extension

### 2. Install Redis
Option A - WSL (Recommended):
```powershell
wsl --install
wsl
sudo apt-get update
sudo apt-get install redis-server
sudo service redis-server start
```

Option B - Memurai (Native Windows):
1. Download from https://www.memurai.com/
2. Install and start service

### 3. Install MinIO
```powershell
# Download MinIO
Invoke-WebRequest -Uri "https://dl.min.io/server/minio/release/windows-amd64/minio.exe" -OutFile "C:\Program Files\minio.exe"

# Create data directory
New-Item -Path "C:\minio-data" -ItemType Directory

# Start MinIO
& "C:\Program Files\minio.exe" server C:\minio-data --console-address ":9001"
```

### 4. Install CUDA Toolkit 12.6
1. Download from https://developer.nvidia.com/cuda-downloads
2. Follow installation wizard
3. Verify: `nvcc --version`

## Project Setup

### Step 1: Create Environment File
```powershell
cd "c:\Users\Thiya\OneDrive\Documents\Smart city AI"
Copy-Item .env.example .env
```

Edit `.env` with your settings:
- Database credentials
- Stream URL
- Model path

### Step 2: Install Python Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Setup Database
```powershell
# Create database
psql -U postgres
CREATE DATABASE smart_city_ai;
\c smart_city_ai
CREATE EXTENSION postgis;
\q

# Run migrations
alembic upgrade head
```

### Step 4: Setup YOLOv11 Model
```powershell
# Create models directory
New-Item -Path "models" -ItemType Directory

# Place your yolov11-nano.onnx in models/
# Or export from PyTorch:
# python
# from ultralytics import YOLO
# model = YOLO('yolov11n.pt')
# model.export(format='onnx')
```

### Step 5: Start Services

Use the startup script:
```powershell
.\start-services.ps1
```

Or manually in separate terminals:

**Terminal 1:**
```powershell
redis-server
```

**Terminal 2:**
```powershell
minio server C:\minio-data --console-address ":9001"
```

**Terminal 3:**
```powershell
celery -A tasks.celery_worker worker --loglevel=info --pool=solo
```

**Terminal 4:**
```powershell
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 5:**
```powershell
python tasks/redis_consumer.py
```

**Terminal 6:**
```powershell
python vision/yolov11_pipeline.py
```

## Verification

1. **Check API**: http://localhost:8000/docs
2. **Check MinIO**: http://localhost:9001 (admin/admin123)
3. **Check Redis**: `redis-cli ping` should return `PONG`
4. **Check Database**: `psql -U postgres -d smart_city_ai -c "\dt"`

## Test the System

```python
# test_system.py
import requests
import json

# Test API
response = requests.get("http://localhost:8000/health")
print(f"API Health: {response.json()}")

# List incidents
incidents = requests.get("http://localhost:8000/incidents/list")
print(f"Incidents: {incidents.json()}")
```

## Troubleshooting

### Import Errors
```powershell
# Ensure you're in the project directory
cd "c:\Users\Thiya\OneDrive\Documents\Smart city AI"
$env:PYTHONPATH = $PWD
```

### Database Connection Issues
```powershell
# Check PostgreSQL is running
pg_isready

# Verify connection
psql -U postgres -d smart_city_ai
```

### CUDA Issues
```powershell
# Verify CUDA
nvidia-smi

# Reinstall ONNX Runtime GPU
pip uninstall onnxruntime-gpu
pip install onnxruntime-gpu
```

### Redis Issues (WSL)
```powershell
wsl
sudo service redis-server start
redis-cli ping
```

## Next Steps

1. Configure your RTSP camera stream in `.env`
2. Train or obtain YOLOv11 model for urban incidents
3. Test with sample video first
4. Integrate with LLM service for verification
5. Build dashboard frontend

## Production Deployment

For production, consider:
1. Docker Compose for orchestration
2. Nginx for reverse proxy
3. SSL certificates
4. Load balancing
5. Monitoring (Prometheus + Grafana)
6. Log aggregation (ELK Stack)
