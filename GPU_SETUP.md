# GPU Setup Guide for CUDA 12.6

## Recommended Configuration
- **Python Version**: 3.10 (3.10.11 recommended)
- **CUDA Version**: 12.6 (you have)
- **PyTorch**: 2.2.0 with cu121 wheels (compatible with CUDA 12.6)

## Installation Steps

### 1. Verify CUDA Installation
```powershell
nvcc --version
nvidia-smi
```

### 2. Create Virtual Environment (Recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify GPU Setup
```powershell
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'CUDA Version: {torch.version.cuda}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'No GPU'}')"
```

Expected output:
```
CUDA Available: True
CUDA Version: 12.1
Device: NVIDIA GeForce RTX 3050
```

### 5. Verify ONNX Runtime GPU
```powershell
python -c "import onnxruntime as ort; print(ort.get_available_providers())"
```

Should include: `['CUDAExecutionProvider', 'CPUExecutionProvider']`

## YOLOv11 Model Export

### Option 1: Using Ultralytics (Recommended)
```python
from ultralytics import YOLO

# Load pretrained model
model = YOLO('yolov11n.pt')  # nano version

# Export to ONNX with GPU optimization
model.export(
    format='onnx',
    dynamic=False,
    simplify=True,
    opset=17
)
```

### Option 2: Export to TensorRT (Maximum Performance)
```python
from ultralytics import YOLO

model = YOLO('yolov11n.pt')

# Export to TensorRT engine (requires TensorRT installation)
model.export(
    format='engine',
    device=0,  # GPU device
    half=True,  # FP16 for faster inference
    workspace=4  # Max workspace size in GB
)
```

## Performance Optimization Tips

### 1. Use FP16 (Half Precision)
For RTX 3050 (6GB), use FP16 to save memory:
```python
# In yolov11_pipeline.py, modify:
providers = [
    ('CUDAExecutionProvider', {
        'device_id': 0,
        'arena_extend_strategy': 'kSameAsRequested',
        'gpu_mem_limit': 4 * 1024 * 1024 * 1024,  # 4GB
        'cudnn_conv_algo_search': 'EXHAUSTIVE',
    }),
    'CPUExecutionProvider'
]
self.session = ort.InferenceSession(model_path, providers=providers)
```

### 2. Batch Processing
Process multiple frames at once for better GPU utilization.

### 3. Async Frame Processing
Use separate threads for frame capture and inference.

## Troubleshooting

### Issue: "CUDAExecutionProvider" not available
```powershell
pip uninstall onnxruntime-gpu
pip install onnxruntime-gpu --extra-index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/
```

### Issue: PyTorch not detecting CUDA
```powershell
# Uninstall existing PyTorch
pip uninstall torch torchvision

# Reinstall with CUDA 12.1
pip install torch==2.2.0+cu121 torchvision==0.17.0+cu121 --extra-index-url https://download.pytorch.org/whl/cu121
```

### Issue: Out of Memory (OOM)
1. Reduce input size: Change `input_size=(640, 640)` to `(416, 416)`
2. Use FP16 precision
3. Reduce batch size
4. Close other GPU applications

### Issue: Slow inference
1. Verify GPU is being used: Check Task Manager → Performance → GPU
2. Use TensorRT instead of ONNX for 2-3x speedup
3. Optimize frame skip rate in pipeline

## Performance Benchmarks (Expected on RTX 3050)

| Format | Precision | FPS (640x640) | Memory Usage |
|--------|-----------|---------------|--------------|
| ONNX   | FP32      | 40-50 FPS     | ~2.5 GB      |
| ONNX   | FP16      | 60-80 FPS     | ~1.5 GB      |
| TensorRT | FP16    | 100-120 FPS   | ~1.2 GB      |

## Testing GPU Performance

Create and run this test script:

```python
# test_gpu.py
import cv2
import numpy as np
import onnxruntime as ort
import time

# Test GPU inference
providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
session = ort.InferenceSession('models/yolov11-nano.onnx', providers=providers)

print(f"Using providers: {session.get_providers()}")

# Create dummy frame
frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

# Warm up
for _ in range(10):
    input_tensor = np.transpose(frame, (2, 0, 1)).astype(np.float32) / 255.0
    input_tensor = np.expand_dims(input_tensor, axis=0)
    session.run(None, {session.get_inputs()[0].name: input_tensor})

# Benchmark
iterations = 100
start = time.time()
for _ in range(iterations):
    input_tensor = np.transpose(frame, (2, 0, 1)).astype(np.float32) / 255.0
    input_tensor = np.expand_dims(input_tensor, axis=0)
    session.run(None, {session.get_inputs()[0].name: input_tensor})
end = time.time()

fps = iterations / (end - start)
print(f"Average FPS: {fps:.2f}")
print(f"Inference time: {1000/fps:.2f} ms")
```

## Recommended Python Versions for CUDA 12.6

✅ **Python 3.10.11** - Best compatibility, stable, recommended
✅ **Python 3.11.8** - Newer features, good compatibility
⚠️ **Python 3.12.x** - Some packages may have issues

## Installation Command Summary

```powershell
# Python 3.10 + CUDA 12.6 + RTX 3050
python --version  # Should be 3.10.x

pip install --upgrade pip setuptools wheel

# Install all dependencies
pip install -r requirements.txt

# Verify installations
python -c "import torch; print(torch.cuda.is_available())"
python -c "import onnxruntime; print(onnxruntime.get_device())"
```
