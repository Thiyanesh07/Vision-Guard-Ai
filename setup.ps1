# Smart City AI - Complete Setup Script
# Run this script to set up the entire system

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Smart City AI - Complete Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectPath = "c:\Users\Thiya\OneDrive\Documents\Smart city AI"
Set-Location $projectPath

# Function to check if command exists
function Test-CommandExists {
    param($command)
    $null = Get-Command $command -ErrorAction SilentlyContinue
    return $?
}

# Step 1: Check Prerequisites
Write-Host "[1/10] Checking Prerequisites..." -ForegroundColor Yellow
Write-Host ""

# Check Python
if (Test-CommandExists python) {
    $pythonVersion = python --version
    Write-Host "  ✓ Python: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "  ✗ Python not found! Install Python 3.10 from python.org" -ForegroundColor Red
    exit
}

# Check PostgreSQL
if (Test-CommandExists psql) {
    Write-Host "  ✓ PostgreSQL installed" -ForegroundColor Green
} else {
    Write-Host "  ✗ PostgreSQL not found! Install from postgresql.org" -ForegroundColor Red
    Write-Host "    Download: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    exit
}

# Check Redis (check if running on WSL or native)
Write-Host "  ? Redis - checking..." -ForegroundColor Yellow
try {
    $redisTest = redis-cli ping 2>$null
    if ($redisTest -eq "PONG") {
        Write-Host "  ✓ Redis is running" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Redis not running. Will provide setup instructions." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ Redis not installed. Will provide setup instructions." -ForegroundColor Yellow
}

# Check CUDA
if (Test-CommandExists nvcc) {
    $cudaVersion = nvcc --version | Select-String "release"
    Write-Host "  ✓ CUDA: $cudaVersion" -ForegroundColor Green
} else {
    Write-Host "  ⚠ CUDA not found in PATH. Make sure CUDA 12.6 is installed." -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to continue with setup"

# Step 2: Create Virtual Environment
Write-Host ""
Write-Host "[2/10] Creating Virtual Environment..." -ForegroundColor Yellow

if (Test-Path "venv") {
    Write-Host "  Virtual environment already exists." -ForegroundColor Yellow
    $recreate = Read-Host "  Recreate it? (y/n)"
    if ($recreate -eq "y") {
        Remove-Item -Recurse -Force venv
        python -m venv venv
        Write-Host "  ✓ Virtual environment recreated" -ForegroundColor Green
    }
} else {
    python -m venv venv
    Write-Host "  ✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "  Activating virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

# Step 3: Upgrade pip
Write-Host ""
Write-Host "[3/10] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel
Write-Host "  ✓ pip upgraded" -ForegroundColor Green

# Step 4: Install Python Dependencies
Write-Host ""
Write-Host "[4/10] Installing Python Dependencies..." -ForegroundColor Yellow
Write-Host "  This may take 5-10 minutes..." -ForegroundColor Cyan

pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "  ✗ Error installing dependencies" -ForegroundColor Red
    Read-Host "Press Enter to continue anyway or Ctrl+C to exit"
}

# Step 5: Verify GPU Setup
Write-Host ""
Write-Host "[5/10] Verifying GPU Setup..." -ForegroundColor Yellow

$gpuTest = python -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU only')" 2>&1

if ($gpuTest -match "True") {
    Write-Host "  ✓ GPU detected and working" -ForegroundColor Green
    Write-Host "  $gpuTest" -ForegroundColor Cyan
} else {
    Write-Host "  ⚠ GPU not detected. Will run on CPU (slower)" -ForegroundColor Yellow
}

# Step 6: Setup Environment File
Write-Host ""
Write-Host "[6/10] Setting up Environment Configuration..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  ✓ Created .env file from .env.example" -ForegroundColor Green
    Write-Host "  ⚠ IMPORTANT: Edit .env file with your configuration!" -ForegroundColor Yellow
    Write-Host "    - Database credentials" -ForegroundColor Yellow
    Write-Host "    - MinIO credentials" -ForegroundColor Yellow
    Write-Host "    - RTSP stream URL" -ForegroundColor Yellow
    Write-Host "    - Model path" -ForegroundColor Yellow
    Write-Host ""
    $editNow = Read-Host "  Open .env for editing now? (y/n)"
    if ($editNow -eq "y") {
        notepad .env
        Read-Host "Press Enter after saving .env"
    }
} else {
    Write-Host "  .env file already exists" -ForegroundColor Yellow
}

# Step 7: Setup PostgreSQL Database
Write-Host ""
Write-Host "[7/10] Setting up PostgreSQL Database..." -ForegroundColor Yellow

Write-Host ""
Write-Host "  PostgreSQL Setup Instructions:" -ForegroundColor Cyan
Write-Host "  1. Open Command Prompt or PowerShell as Administrator" -ForegroundColor White
Write-Host "  2. Run these commands:" -ForegroundColor White
Write-Host ""
Write-Host "     psql -U postgres" -ForegroundColor Yellow
Write-Host "     CREATE DATABASE smart_city_ai;" -ForegroundColor Yellow
Write-Host "     \c smart_city_ai" -ForegroundColor Yellow
Write-Host "     CREATE EXTENSION postgis;" -ForegroundColor Yellow
Write-Host "     \q" -ForegroundColor Yellow
Write-Host ""

$dbSetup = Read-Host "  Have you created the database? (y/n)"

if ($dbSetup -eq "y") {
    Write-Host "  Running database migrations..." -ForegroundColor Cyan
    
    try {
        alembic upgrade head
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Database migrations completed" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ Migration had issues. Check your .env DATABASE_URL" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ⚠ Could not run migrations. Make sure .env is configured correctly" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠ Skipping database setup. Run 'alembic upgrade head' later" -ForegroundColor Yellow
}

# Step 8: Setup Redis
Write-Host ""
Write-Host "[8/10] Redis Setup..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Redis Setup Options:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Option A - WSL (Recommended):" -ForegroundColor White
Write-Host "    wsl --install" -ForegroundColor Yellow
Write-Host "    wsl" -ForegroundColor Yellow
Write-Host "    sudo apt-get update" -ForegroundColor Yellow
Write-Host "    sudo apt-get install redis-server -y" -ForegroundColor Yellow
Write-Host "    sudo service redis-server start" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Option B - Memurai (Native Windows):" -ForegroundColor White
Write-Host "    Download from: https://www.memurai.com/" -ForegroundColor Yellow
Write-Host ""

try {
    $redisCheck = redis-cli ping 2>$null
    if ($redisCheck -eq "PONG") {
        Write-Host "  ✓ Redis is running" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Redis not responding. Start it before running the system" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ Redis not available. Install and start it before running" -ForegroundColor Yellow
}

# Step 9: Setup MinIO
Write-Host ""
Write-Host "[9/10] MinIO Setup..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  MinIO Setup Instructions:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Download MinIO:" -ForegroundColor White
Write-Host "    Invoke-WebRequest -Uri 'https://dl.min.io/server/minio/release/windows-amd64/minio.exe' -OutFile 'C:\Program Files\minio.exe'" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Create data directory:" -ForegroundColor White
Write-Host "    New-Item -Path 'C:\minio-data' -ItemType Directory" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Start MinIO (in a separate terminal):" -ForegroundColor White
Write-Host "    & 'C:\Program Files\minio.exe' server C:\minio-data --console-address ':9001'" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Access MinIO Console: http://localhost:9001" -ForegroundColor Cyan
Write-Host "  Default credentials: minioadmin / minioadmin" -ForegroundColor Cyan
Write-Host ""

try {
    $minioCheck = Invoke-WebRequest -Uri "http://localhost:9000/minio/health/live" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($minioCheck.StatusCode -eq 200) {
        Write-Host "  ✓ MinIO is running" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ MinIO not running. Start it before running the system" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ MinIO not available. Install and start it before running" -ForegroundColor Yellow
}

# Step 10: Create models directory
Write-Host ""
Write-Host "[10/10] Creating Models Directory..." -ForegroundColor Yellow

if (-not (Test-Path "models")) {
    New-Item -Path "models" -ItemType Directory
    Write-Host "  ✓ Models directory created" -ForegroundColor Green
} else {
    Write-Host "  Models directory already exists" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  ⚠ IMPORTANT: Place your YOLOv11-nano.onnx model in the 'models' folder" -ForegroundColor Yellow
Write-Host ""
Write-Host "  To export YOLOv11 to ONNX:" -ForegroundColor Cyan
Write-Host "    python -c 'from ultralytics import YOLO; YOLO(\"yolov11n.pt\").export(format=\"onnx\")'" -ForegroundColor Yellow
Write-Host ""

# Setup Complete
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. ✓ Edit .env file with your configuration" -ForegroundColor White
Write-Host "2. ✓ Ensure PostgreSQL database is created" -ForegroundColor White
Write-Host "3. ✓ Ensure Redis is running" -ForegroundColor White
Write-Host "4. ✓ Ensure MinIO is running" -ForegroundColor White
Write-Host "5. ✓ Place YOLOv11 model in models/yolov11-nano.onnx" -ForegroundColor White
Write-Host ""
Write-Host "To start the system:" -ForegroundColor Yellow
Write-Host "  .\start-services.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "To test the system:" -ForegroundColor Yellow
Write-Host "  python test_system.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "For detailed documentation, see:" -ForegroundColor Yellow
Write-Host "  - README.md" -ForegroundColor Cyan
Write-Host "  - SETUP.md" -ForegroundColor Cyan
Write-Host "  - GPU_SETUP.md" -ForegroundColor Cyan
Write-Host ""
