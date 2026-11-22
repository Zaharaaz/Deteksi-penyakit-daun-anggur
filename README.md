# Grape Leaf Disease Detection: Web App

Streamlit web app for interactive grape leaf disease detection,
powered by a YOLOv12 model trained on a custom + public dataset.

Model training, dataset, and experiments (YOLOv12 vs YOLOv12 + CBAM):
[Grape-Leaf-Disease-Detection](https://github.com/Zaharaaz/Grape-Leaf-Disease-Detection)

## Features
- Upload a grape leaf image and get the detected disease class,
  bounding box, and confidence score
- [Pilih model: YOLOv12 baseline / YOLOv12 + CBAM, hapus jika tidak ada]
- [Tampilan perbandingan gambar asli vs hasil deteksi, jika ada]

## Model
- Architecture: YOLOv12 (Ultralytics), PyTorch
- Detected classes: downy mildew, black rot [+ healthy, sesuaikan]
- Performance: 81.9% mAP@0.5 (baseline YOLOv12) [pastikan jenis mAP]
- Final model: baseline YOLOv12 (higher mAP than YOLOv12 + CBAM, 67.9%)

## Tech
Python, PyTorch, Ultralytics YOLOv12, Streamlit

## How to run
```bash
git clone https://github.com/Zaharaaz/Deteksi-penyakit-daun-anggur
cd Deteksi-penyakit-daun-anggur
pip install -r requirements.txt
streamlit run app.py
```

## Demo
![app screenshot](demo.png)

[Live demo: link Streamlit Cloud, jika sudah di-deploy]

## Notes
This app is for educational and portfolio purposes and is not a
substitute for expert plant pathology diagnosis.
