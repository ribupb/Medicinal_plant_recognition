import os
import random
import numpy as np
from datetime import datetime
import sqlite3
import gdown


# Flask imports
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

from tensorflow import keras
from tensorflow.keras.preprocessing import image
from PIL import Image

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Paths
CLASS_LABELS_PATH = os.path.join(os.getcwd(), "class_labels_1.txt")
MODEL_PATH = os.path.join(os.getcwd(), "medicinal_model_1.keras")
DB_PATH = os.path.join(os.getcwd(), "plants.db")

# Globals
model = None
class_labels = []
history = []

# ----------------- DB CONNECTION -----------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ----------------- LOAD MODEL -----------------
MODEL_PATH = "medicinal_model_1.keras"
DRIVE_URL = "https://drive.google.com/uc?id=1HoTd4lCXIf-hjXMBSOMUJukutuxcFSz3"

try:
    if not os.path.exists(MODEL_PATH):
        print("Downloading model from Google Drive...")
        gdown.download(DRIVE_URL, MODEL_PATH, quiet=False)

    model = keras.models.load_model(MODEL_PATH)
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# ----------------- LOAD CLASS LABELS -----------------
try:
    with open(CLASS_LABELS_PATH, "r") as f:
        class_labels = [line.strip() for line in f]
    print(f"Class labels loaded: {class_labels}")
except FileNotFoundError:
    print(f"Error: '{CLASS_LABELS_PATH}' not found.")
    class_labels = []

# ----------------- IMAGE PREPROCESSING -----------------
def preprocess_image(img_path, target_size=(224, 224)):
    try:
        img = Image.open(img_path).convert("RGB")
        img = img.resize(target_size)
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        return img_array
    except Exception as e:
        print(f"Error in preprocess_image: {e}")
        return None

def predict_image(img_path, model_to_use, labels, target_size=(224, 224), threshold=0.70):
    if model_to_use is None:
        return "Error: Model Not Loaded", 0.0
    if not labels:
        return "Error: Class Labels Missing", 0.0
    try:
        img_array = preprocess_image(img_path, target_size)
        if img_array is None:
            return "Error in preprocessing", 0.0

        prediction_array = model_to_use.predict(img_array)[0]
        confidence = np.max(prediction_array)
        predicted_index = np.argmax(prediction_array)
        if confidence < threshold:
            return "Unknown", confidence
        return labels[predicted_index], confidence
    except Exception as e:
        print(f"Error during prediction: {e}")
        return "Error during prediction", 0.0

# ----------------- ROUTES -----------------
@app.route("/", methods=["GET", "POST"])
def index():
    search_result = None
    if request.method == "POST" and "search" in request.form:
        query = request.form["search"].strip().lower()
        conn = get_db_connection()
        results = conn.execute("""
            SELECT * FROM plants
            WHERE LOWER(name) LIKE ?
            OR LOWER(scientific_name) LIKE ?
            OR LOWER(description) LIKE ?
            OR LOWER(region) LIKE ?
            OR LOWER(medicinal_uses) LIKE ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()
        conn.close()
        search_result = [dict(row) for row in results] if results else [{"name": "No Plant Found", "description": "No match found."}]

    # Pick plant of the day
    plant_of_day = random.choice(class_labels) if class_labels else "Unknown Plant"
    conn = get_db_connection()
    potd_info = conn.execute("SELECT * FROM plants WHERE LOWER(name) = ?", (plant_of_day.lower(),)).fetchone()
    conn.close()
    potd_info = dict(potd_info) if potd_info else {"name": plant_of_day, "description": "Details not available."}

    return render_template("index.html", history=history[-5:], potd_info=potd_info, search_result=search_result)

@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "").lower()
    conn = get_db_connection()
    results = conn.execute("""
        SELECT * FROM plants
        WHERE LOWER(name) LIKE ?
        OR LOWER(scientific_name) LIKE ?
        OR LOWER(description) LIKE ?
        OR LOWER(region) LIKE ?
        OR LOWER(medicinal_uses) LIKE ?
    """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()
    conn.close()
    return jsonify([dict(row) for row in results])

@app.route("/predict_api", methods=["POST"])
def predict_api():
    if model is None:
        return jsonify({'error': 'Model not loaded.'}), 500
    if not class_labels:
        return jsonify({'error': 'Class labels not loaded.'}), 500
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)

        pred_label_raw, conf = predict_image(filepath, model, class_labels)
        os.remove(filepath)

        pred_label_formatted = pred_label_raw.title() if pred_label_raw != "Unknown" else "Unknown"

        plant_details = {}
        if pred_label_formatted != "Unknown":
            conn = get_db_connection()
            plant = conn.execute("SELECT * FROM plants WHERE LOWER(name) = ?", (pred_label_formatted.lower(),)).fetchone()
            conn.close()
            if plant:
                plant_details = dict(plant)
                plant_details["uses"] = plant_details.get("uses", "N/A").split(", ")
        if not plant_details:
            if pred_label_formatted == "Unknown":
                plant_details = {
                    "name": "Unknown Plant",
                    "scientific_name": "N/A",
                    "uses": ["We could not confidently identify this plant. Please try another image."],
                    "region": "N/A",
                    "description": "N/A"
                }
            else:
                plant_details = {
                    "name": pred_label_formatted,
                    "scientific_name": "N/A",
                    "uses": ["Details for this plant are not yet available."],
                    "region": "N/A",
                    "description": "N/A"
                }

        history.append({
            "filename": file.filename,
            "label": pred_label_raw,
            "confidence": round(conf, 2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        if len(history) > 50:
            history.pop(0)

        return jsonify({'prediction': pred_label_raw, 'confidence': float(conf), 'plant_details': plant_details})
    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': f'Prediction error: {str(e)}'}), 500

@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    data = request.json
    conn = get_db_connection()
    conn.execute("INSERT INTO feedback (user_name, email, message) VALUES (?, ?, ?)",
                 (data.get("user_name"), data.get("email"), data.get("message")))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Feedback submitted"})





@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "").strip().lower()

    if not user_message:
        return jsonify({"reply": "Please ask something about medicinal plants."})

    conn = get_db_connection()
    plant = conn.execute(
        "SELECT * FROM plants WHERE LOWER(name) LIKE ?",
        (f"%{user_message}%",)
    ).fetchone()
    conn.close()

    if plant:
        reply = f"🌿 {plant['name']}\nUses: {plant['uses']}"
    else:
        reply = "Sorry, I couldn't find that plant in my database."

    return jsonify({"reply": reply})








@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "File not found", 404

@app.route("/all-plants")
def show_all_plants():
    conn = get_db_connection()
    plants = conn.execute("SELECT * FROM plants ORDER BY name ASC").fetchall()
    conn.close()
    return render_template("all_plants.html", plants=[dict(p) for p in plants])

# Run App
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

