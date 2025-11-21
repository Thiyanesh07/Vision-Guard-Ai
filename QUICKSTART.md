# Quick Setup Guide - From Zero to Running

## Prerequisites to Install (One-time)

### 1. Python 3.10
```powershell
# Download from python.org
# During installation, check "Add Python to PATH"
python --version  # Verify: should show 3.10.x
```

### 2. PostgreSQL 14+ with PostGIS
```powershell
# Download: https://www.postgresql.org/download/windows/
# During install:
# - Remember the password for user 'postgres'
# - Include Stack Builder
# - Use Stack Builder to install PostGIS extension
```

### 3. Redis
**Option A - WSL (Recommended):**
```powershell
wsl --install
# Restart computer if prompted
wsl
sudo apt-get update
sudo apt-get install redis-server -y
sudo service redis-server start
redis-cli ping  # Should return PONG
```

**Option B - Memurai (Native Windows):**
```powershell
# Download: https://www.memurai.com/
# Install and start as Windows service
```

### 4. MinIO
```powershell
# Download MinIO
Invoke-WebRequest -Uri "https://dl.min.io/server/minio/release/windows-amd64/minio.exe" -OutFile "$env:USERPROFILE\minio.exe"

# Create data directory
New-Item -Path "$env:USERPROFILE\minio-data" -ItemType Directory

# Start MinIO (keep this terminal open)
& "$env:USERPROFILE\minio.exe" server "$env:USERPROFILE\minio-data" --console-address ":9001"

# Access console: http://localhost:9001
# Default login: minioadmin / minioadmin
```

### 5. CUDA Toolkit 12.6
```powershell
# Download: https://developer.nvidia.com/cuda-downloads
# Follow installer
# Verify:
nvcc --version
nvidia-smi
```

---

## Project Setup (Run Once)

### Step 1: Navigate to Project
```powershell
cd "c:\Users\Thiya\OneDrive\Documents\Smart city AI"
```

### Step 2: Run Automated Setup
```powershell
.\setup.ps1
```

This script will:
- ✓ Check prerequisites
- ✓ Create virtual environment
- ✓ Install all Python packages
- ✓ Create .env file
- ✓ Guide you through database setup
- ✓ Create models directory

### Step 3: Configure Environment
Edit `.env` file:
```powershell
notepad .env
```

Update these values:
```env
# Database (update password)
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/smart_city_ai

# MinIO (if you changed credentials)
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Your camera stream
STREAM_URL=rtsp://your-camera-ip/stream
# Or use test video:
# STREAM_URL=video.mp4

# Model path
YOLO_MODEL_PATH=models/yolov11-nano.onnx
```

### Step 4: Create Database
```powershell
# Open new terminal
psql -U postgres

# In psql:
CREATE DATABASE smart_city_ai;
\c smart_city_ai
CREATE EXTENSION postgis;
\q
```

### Step 5: Run Migrations
```powershell
# Back in project directory
alembic upgrade head
```

### Step 6: Get YOLOv11 Model

**Option A - Download pretrained:**
```powershell
# Download yolov11n.pt from Ultralytics
# Then export to ONNX:
python -c "from ultralytics import YOLO; YOLO('yolov11n.pt').export(format='onnx')"
# Move yolov11n.onnx to models/yolov11-nano.onnx
```

**Option B - Train custom model:**
See Ultralytics documentation for training on your dataset.

---

## Running the System (Daily Use)

### Start All Services (Separate Terminals)

**Terminal 1 - Redis:**
```powershell
# If using WSL:
wsl
sudo service redis-server start
redis-cli ping
```

**Terminal 2 - MinIO:**
```powershell
& "$env:USERPROFILE\minio.exe" server "$env:USERPROFILE\minio-data" --console-address ":9001"
```

**Terminal 3 - Celery Worker:**
```powershell
cd "c:\Users\Thiya\OneDrive\Documents\Smart city AI"
.\venv\Scripts\Activate.ps1
celery -A tasks.celery_worker worker --loglevel=info --pool=solo
```

**Terminal 4 - FastAPI Backend:**
```powershell
cd "c:\Users\Thiya\OneDrive\Documents\Smart city AI"
.\venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 5 - Redis Consumer:**
```powershell
cd "c:\Users\Thiya\OneDrive\Documents\Smart city AI"
.\venv\Scripts\Activate.ps1
python tasks/redis_consumer.py
```

**Terminal 6 - Vision Pipeline:**
```powershell
cd "c:\Users\Thiya\OneDrive\Documents\Smart city AI"
.\venv\Scripts\Activate.ps1
python vision/yolov11_pipeline.py
```

### OR Use Service Manager:
```powershell
.\start-services.ps1
# Select service to start from menu
```

---

## Testing

### Test Individual Components:
```powershell
.\venv\Scripts\Activate.ps1
python test_system.py
```

### Test API:
```powershell
# Open browser: http://localhost:8000/docs
```

### Check Service Status:
```powershell
# Redis
redis-cli ping

# PostgreSQL
pg_isready

# MinIO
curl http://localhost:9000/minio/health/live

# FastAPI
curl http://localhost:8000/health
```

---

## Troubleshooting

### Virtual Environment Not Activating:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Import Errors:
```powershell
cd "c:\Users\Thiya\OneDrive\Documents\Smart city AI"
.\venv\Scripts\Activate.ps1
$env:PYTHONPATH = $PWD
```

### Database Connection Failed:
```powershell
# Check PostgreSQL is running:
pg_isready

# Check credentials in .env match psql
psql -U postgres -d smart_city_ai
```

### GPU Not Detected:
```powershell
python -c "import torch; print(torch.cuda.is_available())"
# If False, reinstall PyTorch:
pip uninstall torch torchvision
pip install torch==2.2.0+cu121 torchvision==0.17.0+cu121 --extra-index-url https://download.pytorch.org/whl/cu121
```

### Redis Not Starting (WSL):
```powershell
wsl
sudo service redis-server status
sudo service redis-server start
```

### Port Already in Use:
```powershell
# Find process using port 8000:
netstat -ano | findstr :8000
# Kill process:
taskkill /PID <PID> /F
```

---

## Daily Workflow

### Morning Startup:
1. Start Redis (if not running)
2. Start MinIO
3. Run `.\start-services.ps1` and start each service

### Development:
1. Edit code
2. Services auto-reload (FastAPI, Celery with --reload)
3. Monitor logs in each terminal

### Shutdown:
1. Press Ctrl+C in each terminal
2. Stop MinIO
3. (Optional) Stop Redis

---

## Useful Commands

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install new package
pip install package-name
pip freeze > requirements.txt

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# View database
psql -U postgres -d smart_city_ai
\dt  # List tables
SELECT * FROM incidents;

# Check Redis
redis-cli
KEYS *
GET key

# View MinIO files
# Open http://localhost:9001 in browser
```

---

## File Locations

- **Configuration**: `.env`
- **Models**: `models/yolov11-nano.onnx`
- **Logs**: Check each terminal output
- **Database**: PostgreSQL (connect via psql)
- **Storage**: MinIO at `C:\Users\YourUser\minio-data`
- **Virtual Environment**: `venv/`

---

## URLs

- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001
- **API Health**: http://localhost:8000/health
- **WebSocket**: ws://localhost:8000/ws

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| `alembic: command not found` | Activate venv: `.\venv\Scripts\Activate.ps1` |
| `No module named 'config'` | Set PYTHONPATH: `$env:PYTHONPATH = $PWD` |
| `Connection refused` | Start the required service |
| `Access denied` | Check firewall, run as Administrator |
| `Out of memory` | Reduce frame buffer size in config |
| `Model not found` | Check YOLO_MODEL_PATH in .env |

---

## Next Steps After Setup

1. **Test with sample video** before using RTSP
2. **Fine-tune YOLO model** on your incident types
3. **Adjust confidence threshold** in .env
4. **Build frontend dashboard** using WebSocket
5. **Integrate LLM service** for verification
6. **Deploy to production** using Docker

---

## Need Help?

1. Check logs in each terminal
2. Run `python test_system.py`
3. Review SETUP.md for detailed info
4. Check GPU_SETUP.md for GPU issues
5. Review README.md for architecture
