# 🌿 Medicinal Plant Recognition

A deep learning–based medicinal plant recognition system that identifies
plant species from leaf images using a Convolutional Neural Network (CNN).
The project demonstrates the use of computer vision in healthcare and
botanical applications.

---

##Features
- Leaf image–based plant classification
- CNN model(MobileNetV2)) using TensorFlow / Keras
- Flask-based web application
- SQLite database for medicinal information

---

##Tech Stack
- Python
- TensorFlow / Keras
- Flask
- OpenCV
- SQLite
- HTML, CSS

---

## Project Structure
```
Medicinal_plant_recognition/
├── app.py
├── create_db.py
├── plants.db
├── class_labels_1.txt
├── templates/
├── static/
│   └── images/
│       └── plants/
└── README.md
```
---

##Dataset
- ~20,000 medicinal plant leaf images  
- Covers **27 medicinal plant species**, with approximately **700–800 images per species**
- Dataset not included due to GitHub size limits
- 📌 Note: Currently the model is trained to recognize **27 medicinal plant species**


🔗 **Dataset (Google Drive):**  
https://drive.google.com/drive/folders/1Cf4xjChTd12JvJgrFmzGvCxBFq17s5lU?usp=sharing

---

##Trained Model
- CNN trained on medicinal plant leaf images  
- Model files not included due to size constraints

🔗 **Trained model (Google Drive):**  
https://drive.google.com/uc?id=1HoTd4IcXIf-IhjXMBSOMUJkutuxcFSz3

---

##**plant images (Google Drive):**
https://drive.google.com/drive/folders/1LXpKgfwSkOLPQM1Jnh04qQMQchielhTP

After downloading, place the plant folder in:
static/images/plants/

## 🚀 Live Demo
🔗 https://medicinal-plant-recognition-1.onrender.com

⚠️ Note: First request may take ~30–60 seconds due to free-tier cold start.












