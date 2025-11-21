# Smart City AI - Start All Services
# This script starts all services in separate windows

$projectPath = "C:\Users\Thiya\OneDrive\Documents\Smart city AI"

Write-Host "🚀 Starting Smart City AI System..." -ForegroundColor Cyan
Write-Host ""

# Start MinIO
Write-Host "Starting MinIO Server..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectPath'; minio.exe server minio-data --console-address ':9001'"
)
Start-Sleep -Seconds 2

# Start FastAPI
Write-Host "Starting FastAPI Backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectPath'; conda activate venv; uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
)
Start-Sleep -Seconds 3

# Start Celery Worker
Write-Host "Starting Celery Worker..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectPath'; conda activate venv; celery -A tasks.celery_worker worker --loglevel=info -P solo"
)
Start-Sleep -Seconds 2

# Start Redis Consumer
Write-Host "Starting Redis Consumer..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectPath'; conda activate venv; python tasks/redis_consumer.py"
)
Start-Sleep -Seconds 2

# Start Vision Pipeline
Write-Host "Starting Vision Pipeline (GPU)..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectPath'; conda activate venv; python vision/yolov11_pipeline.py"
)

Write-Host ""
Write-Host "✅ All services are starting..." -ForegroundColor Green
Write-Host ""
Write-Host "Services:" -ForegroundColor Yellow
Write-Host "  - MinIO Console: http://localhost:9001" -ForegroundColor Cyan
Write-Host "  - MinIO API: http://localhost:9000" -ForegroundColor Cyan
Write-Host "  - FastAPI: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  - Redis: localhost:6379" -ForegroundColor Cyan
Write-Host "  - PostgreSQL: localhost:5432" -ForegroundColor Cyan
Write-Host ""
Write-Host "Wait 10-15 seconds for all services to initialize..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Run './check_status.py' to verify all services are running" -ForegroundColor Yellow
Write-Host ""
