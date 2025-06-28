import streamlit as st
from ultralytics import YOLO
import numpy as np
import cv2

@st.cache_resource
def load_model():
    model = YOLO("./models/CBAMYolov12.pt")  # pastikan best.pt di folder yang sama
    return model
    
# Simulate YOLO detection (replace with actual YOLO inference)
def simulate_detection(image):
    """
    Simulasi deteksi - ganti dengan inference YOLO yang sebenarnya
    """
# Convert PIL to numpy array
    img_array = np.array(image)
    
# Simulate detection results
    import random
    diseases = ['healthy', 'black_rot', 'downy_mildew']
    detected_disease = random.choice(diseases)
    confidence = random.uniform(0.7, 0.98)
    
    # Simulate bounding box
    h, w = img_array.shape[:2]
    x1, y1 = random.randint(10, w//4), random.randint(10, h//4)
    x2, y2 = random.randint(3*w//4, w-10), random.randint(3*h//4, h-10)
    
    return {
        'class': detected_disease,
        'confidence': confidence,
        'bbox': [x1, y1, x2, y2]
    }
    
# Function to perform actual YOLO detection
def detect_disease(image, model):
    results = model.predict(image, conf=0.5)[0]  # hasil prediksi tunggal
    detection_info = {
        'results': results,  # simpan object asli YOLO
    }

    if results.boxes:
        box = results.boxes[0]
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        label = model.names[cls]
        
        detection_info.update({
            'prediction': label,
            'confidence': conf * 100,
            'class': label.lower()
        })
    else:
        detection_info.update({
            'prediction': 'Tidak terdeteksi',
            'confidence': 0,
            'class': 'unknown'
        })

    return detection_info