"""
Download and export YOLOv11-nano model to ONNX format
"""
from ultralytics import YOLO
import os
import requests
from pathlib import Path

print("Downloading YOLOv11-nano pretrained model...")
print("This may take a few minutes depending on your internet speed...")

# Direct download URL for YOLOv11n
model_url = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt"
model_path = "yolo11n.pt"

try:
    # Download the model file
    print(f"Downloading from {model_url}...")
    response = requests.get(model_url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    block_size = 8192
    downloaded = 0
    
    with open(model_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=block_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\rProgress: {percent:.1f}%", end='', flush=True)
    
    print("\n✓ Model downloaded successfully!")
    
    # Load and export to ONNX
    print("Loading model and exporting to ONNX format...")
    model = YOLO(model_path)
    
    # Export to ONNX
    model.export(format='onnx', simplify=True, opset=17)
    
    print("✓ Export complete!")
    
    # Create models directory and move files
    os.makedirs('models', exist_ok=True)
    
    # Move ONNX file
    onnx_files = ['yolo11n.onnx', 'yolov8n.onnx']
    moved = False
    for onnx_file in onnx_files:
        if os.path.exists(onnx_file):
            if os.path.exists('models/yolov11-nano.onnx'):
                os.remove('models/yolov11-nano.onnx')
            os.rename(onnx_file, 'models/yolov11-nano.onnx')
            print("✓ Model ready at: models/yolov11-nano.onnx")
            moved = True
            break
    
    if not moved:
        print("⚠ ONNX file not found. Check for onnx files in current directory")
    
    # Optionally keep or remove the .pt file
    # os.remove(model_path)  # Uncomment to delete the .pt file
    
    print("\n✅ Setup complete! You can now run the vision pipeline.")
    
except requests.exceptions.RequestException as e:
    print(f"\n❌ Download failed: {e}")
    print("\nAlternative: Download manually from:")
    print(model_url)
    print(f"Save it as: {model_path}")
except Exception as e:
    print(f"\n❌ Error: {e}")
