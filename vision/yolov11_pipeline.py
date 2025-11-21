import cv2
import numpy as np
import onnxruntime as ort
from datetime import datetime
import redis
import json
from collections import deque
import io
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
from storage.minio_client import upload_frame, create_bucket_if_not_exists

# COCO class names (YOLOv8 uses COCO dataset with 80 classes)
COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
    'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
    'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
    'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
    'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
    'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator',
    'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]

# Map COCO classes to incident types (for demo purposes)
COCO_TO_INCIDENT = {
    0: "person_detected",  # person - will trigger incident
    2: "traffic_congestion",  # car
    5: "traffic_congestion",  # bus
    7: "traffic_congestion",  # truck
    39: "bottle_detected",  # bottle (for testing)
    63: "laptop_detected",  # laptop (for testing)
    67: "cell_phone_detected",  # cell phone (for testing)
}

# Load YOLOv11-Nano model
class YOLOv11Nano:
    def __init__(self, model_path, input_size=(640, 640), confidence_threshold=0.5):
        self.session = ort.InferenceSession(model_path, providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        self.input_size = input_size
        self.confidence_threshold = confidence_threshold

    def preprocess(self, frame):
        resized = cv2.resize(frame, self.input_size)
        normalized = resized / 255.0
        transposed = np.transpose(normalized, (2, 0, 1))
        return np.expand_dims(transposed, axis=0).astype(np.float32)

    def postprocess(self, outputs):
        detections = []
        # Assuming YOLOv11 output format: [batch, num_detections, 85]
        # [x, y, w, h, confidence, class_scores...]
        for output in outputs[0][0]:
            confidence = output[4]
            if confidence > self.confidence_threshold:
                class_scores = output[5:]
                class_id = np.argmax(class_scores)
                class_confidence = class_scores[class_id]
                
                if class_confidence > self.confidence_threshold:
                    detections.append({
                        'class_id': int(class_id),
                        'confidence': float(confidence * class_confidence),
                        'bbox': output[:4].tolist()
                    })
        return detections

    def infer(self, frame):
        input_tensor = self.preprocess(frame)
        outputs = self.session.run(None, {self.input_name: input_tensor})
        return self.postprocess(outputs)

class FrameBuffer:
    def __init__(self, max_size=16):
        self.buffer = deque(maxlen=max_size)
        self.timestamps = deque(maxlen=max_size)
    
    def add_frame(self, frame, timestamp):
        self.buffer.append(frame.copy())
        self.timestamps.append(timestamp)
    
    def get_spaced_frames(self, num_frames=4, spacing_ms=200):
        """Extract frames spaced by approximately spacing_ms milliseconds"""
        if len(self.buffer) < num_frames:
            return list(self.buffer), list(self.timestamps)
        
        # Calculate indices for evenly spaced frames
        total_frames = len(self.buffer)
        indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
        
        selected_frames = [self.buffer[i] for i in indices]
        selected_timestamps = [self.timestamps[i] for i in indices]
        
        return selected_frames, selected_timestamps

# Initialize Redis client
redis_client = redis.StrictRedis(
    host=settings.redis_host, 
    port=settings.redis_port, 
    db=settings.redis_db
)

def upload_frames_to_minio(frames, incident_id):
    """Upload frames to MinIO and return URLs"""
    frame_urls = []
    
    for idx, frame in enumerate(frames):
        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = io.BytesIO(buffer.tobytes())
        
        # Upload to MinIO
        file_name = f"{incident_id}_f{idx+1}.jpg"
        url = upload_frame(settings.minio_bucket, file_name, frame_bytes)
        
        if url:
            frame_urls.append(url)
    
    return frame_urls

# Process video stream
def process_stream(stream_url, model):
    # Convert string to int for webcam device ID
    if isinstance(stream_url, str) and stream_url.isdigit():
        stream_url = int(stream_url)
    
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        print("Error: Unable to open video stream")
        return
    
    # Initialize frame buffer
    frame_buffer = FrameBuffer(max_size=settings.frame_buffer_size)
    
    # Ensure MinIO bucket exists
    create_bucket_if_not_exists(settings.minio_bucket)
    
    print(f"Processing stream: {stream_url}")
    print(f"Confidence threshold: {settings.confidence_threshold}")
    
    frame_count = 0
    last_detection_time = 0
    detection_cooldown = 5000  # 5 seconds cooldown between detections
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("End of stream or error reading frame")
            break
        
        current_time = cv2.getTickCount()
        timestamp = datetime.now()
        
        # Add frame to buffer
        frame_buffer.add_frame(frame, timestamp)
        
        # Run inference
        detections = model.infer(frame)
        
        # Draw detections on frame for visualization
        for det in detections:
            bbox = det['bbox']
            x, y, width, height = bbox
            h, w = frame.shape[:2]
            # Convert from YOLO format to pixel coordinates
            x1 = int((x - width/2) * w / 640)
            y1 = int((y - height/2) * h / 640)
            x2 = int((x + width/2) * w / 640)
            y2 = int((y + height/2) * h / 640)
            
            class_id = det['class_id']
            confidence = det['confidence']
            class_name = COCO_CLASSES[class_id] if class_id < len(COCO_CLASSES) else f"class_{class_id}"
            
            # Draw rectangle and label
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Add info overlay
        cv2.putText(frame, f"Detections: {len(detections)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f"Frame: {frame_count}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Process detections for incidents (only certain classes)
        if detections and (current_time - last_detection_time) > detection_cooldown * cv2.getTickFrequency() / 1000:
            for detection in detections:
                class_id = detection['class_id']
                
                # Only process if it's in our incident mapping
                if class_id in COCO_TO_INCIDENT:
                    incident_type = COCO_TO_INCIDENT[class_id]
                    class_name = COCO_CLASSES[class_id] if class_id < len(COCO_CLASSES) else f"class_{class_id}"
                    confidence = detection['confidence']
                    
                    print(f"\n🚨 INCIDENT DETECTED: {class_name} -> {incident_type} (confidence: {confidence:.2f})")
                    
                    incident_id = f"incident_{timestamp.strftime('%Y%m%d%H%M%S%f')}"
                    
                    # Extract spaced frames from buffer
                    selected_frames, _ = frame_buffer.get_spaced_frames(
                        num_frames=settings.frames_to_extract,
                        spacing_ms=200
                    )
                    
                    # Upload frames to MinIO
                    print(f"Uploading {len(selected_frames)} frames to MinIO...")
                    frame_urls = upload_frames_to_minio(selected_frames, incident_id)
                    
                    if frame_urls:
                        # Create event payload
                        event = {
                            "id": incident_id,
                            "incident": incident_type,
                            "confidence": confidence,
                            "frames": frame_urls,
                            "timestamp": timestamp.isoformat(),
                            "location": {
                                "lat": settings.default_lat,
                                "lon": settings.default_lon
                            }
                        }
                        
                        # Publish to Redis
                        redis_client.publish('events', json.dumps(event))
                        print(f"Event published to Redis: {incident_id}")
                        
                        last_detection_time = current_time
                        break  # Process only first incident per cooldown period
        
        frame_count += 1
        
        # Display frame with detections
        cv2.imshow('Smart City AI - Detection Stream', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    model = YOLOv11Nano(
        model_path=settings.yolo_model_path,
        confidence_threshold=settings.confidence_threshold
    )
    process_stream(settings.stream_url, model)