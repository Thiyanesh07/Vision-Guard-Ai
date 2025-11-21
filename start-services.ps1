# Smart City AI - Service Startup Script
# This script helps start all required services

Write-Host "Smart City AI - Service Manager" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$projectPath = "c:\Users\Thiya\OneDrive\Documents\Smart city AI"

function Show-Menu {
    Write-Host "Select a service to start:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Redis Server"
    Write-Host "2. MinIO Server"
    Write-Host "3. Celery Worker"
    Write-Host "4. FastAPI Backend"
    Write-Host "5. Redis Consumer"
    Write-Host "6. Vision Pipeline"
    Write-Host "7. Check Service Status"
    Write-Host "8. Install Dependencies"
    Write-Host "9. Setup Database"
    Write-Host "0. Exit"
    Write-Host ""
}

function Start-RedisServer {
    Write-Host "Starting Redis Server..." -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    redis-server
}

function Start-MinIOServer {
    Write-Host "Starting MinIO Server..." -ForegroundColor Green
    Write-Host "Console: http://localhost:9001" -ForegroundColor Cyan
    Write-Host "API: http://localhost:9000" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    minio server C:\minio-data --console-address ":9001"
}

function Start-CeleryWorker {
    Write-Host "Starting Celery Worker..." -ForegroundColor Green
    Set-Location $projectPath
    celery -A tasks.celery_worker worker --loglevel=info --pool=solo
}

function Start-FastAPIBackend {
    Write-Host "Starting FastAPI Backend..." -ForegroundColor Green
    Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
    Set-Location $projectPath
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
}

function Start-RedisConsumer {
    Write-Host "Starting Redis Consumer..." -ForegroundColor Green
    Set-Location $projectPath
    python tasks/redis_consumer.py
}

function Start-VisionPipeline {
    Write-Host "Starting Vision Pipeline..." -ForegroundColor Green
    Write-Host "Make sure YOLO model is in place!" -ForegroundColor Yellow
    Set-Location $projectPath
    python vision/yolov11_pipeline.py
}

function Check-ServiceStatus {
    Write-Host "Checking Service Status..." -ForegroundColor Cyan
    Write-Host ""
    
    # Check Redis
    Write-Host "Redis: " -NoNewline
    try {
        $redisResult = redis-cli ping 2>$null
        if ($redisResult -eq "PONG") {
            Write-Host "✓ Running" -ForegroundColor Green
        } else {
            Write-Host "✗ Not Running" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ Not Installed or Not Running" -ForegroundColor Red
    }
    
    # Check PostgreSQL
    Write-Host "PostgreSQL: " -NoNewline
    try {
        $pgResult = pg_isready 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Running" -ForegroundColor Green
        } else {
            Write-Host "✗ Not Running" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ Not Installed or Not Running" -ForegroundColor Red
    }
    
    # Check MinIO
    Write-Host "MinIO: " -NoNewline
    try {
        $minioResult = Invoke-WebRequest -Uri "http://localhost:9000/minio/health/live" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($minioResult.StatusCode -eq 200) {
            Write-Host "✓ Running" -ForegroundColor Green
        } else {
            Write-Host "✗ Not Running" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ Not Running" -ForegroundColor Red
    }
    
    # Check FastAPI
    Write-Host "FastAPI Backend: " -NoNewline
    try {
        $apiResult = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($apiResult.StatusCode -eq 200) {
            Write-Host "✓ Running" -ForegroundColor Green
        } else {
            Write-Host "✗ Not Running" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ Not Running" -ForegroundColor Red
    }
    
    Write-Host ""
    Read-Host "Press Enter to continue"
}

function Install-Dependencies {
    Write-Host "Installing Python Dependencies..." -ForegroundColor Green
    Set-Location $projectPath
    pip install -r requirements.txt
    Write-Host ""
    Write-Host "Installation complete!" -ForegroundColor Green
    Read-Host "Press Enter to continue"
}

function Setup-Database {
    Write-Host "Setting up Database..." -ForegroundColor Green
    Write-Host ""
    Write-Host "Make sure PostgreSQL is running and .env is configured!" -ForegroundColor Yellow
    Write-Host ""
    
    $confirm = Read-Host "Continue with database setup? (y/n)"
    if ($confirm -eq "y") {
        Set-Location $projectPath
        Write-Host "Running Alembic migrations..." -ForegroundColor Cyan
        alembic upgrade head
        Write-Host ""
        Write-Host "Database setup complete!" -ForegroundColor Green
    }
    Read-Host "Press Enter to continue"
}

# Main loop
while ($true) {
    Clear-Host
    Show-Menu
    $choice = Read-Host "Enter your choice"
    
    switch ($choice) {
        "1" { Start-RedisServer }
        "2" { Start-MinIOServer }
        "3" { Start-CeleryWorker }
        "4" { Start-FastAPIBackend }
        "5" { Start-RedisConsumer }
        "6" { Start-VisionPipeline }
        "7" { Check-ServiceStatus }
        "8" { Install-Dependencies }
        "9" { Setup-Database }
        "0" { 
            Write-Host "Goodbye!" -ForegroundColor Cyan
            exit 
        }
        default {
            Write-Host "Invalid choice. Please try again." -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
    }
}
