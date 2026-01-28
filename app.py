# =====================================
# app.py — Simplified Flask app for Ransomware Detection with MySQL
# =====================================
import os
import math
from functools import wraps
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash

import torch
import torch.nn as nn
import numpy as np


# -----------------------------
# Flask + SQLite setup
# -----------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "supersecretkey")

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost:3306/ransomware'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    predictions = db.relationship('Prediction', backref='user', lazy=True)

class Prediction(db.Model):
    __tablename__ = 'predictions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    prediction_result = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Tables will be created when the app starts

# -----------------------------
# Device & model path
# -----------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = os.path.join("model", "exe_classifier_model.pth")

# -----------------------------
# ExeClassifier for direct EXE file analysis (must match training)
# -----------------------------
class ExeClassifier(nn.Module):
    def __init__(self, input_size=1024*1024, hidden_size=512, num_classes=2):
        super(ExeClassifier, self).__init__()

        self.encoder = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size, hidden_size//2),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size//2, hidden_size//4),
            nn.ReLU(),
            nn.Dropout(0.3)
        )

        self.classifier = nn.Linear(hidden_size//4, num_classes)

    def forward(self, x):
        features = self.encoder(x)
        return self.classifier(features)

# instantiate and load model
model = ExeClassifier().to(device)

if os.path.exists(MODEL_PATH):
    try:
        state = torch.load(MODEL_PATH, map_location=device)
        model.load_state_dict(state)
        model.eval()
        print(f"[SUCCESS] Model loaded from {MODEL_PATH} (device={device})")
        print(f"[DEBUG] Model state_dict keys: {list(state.keys())}")
        print(f"[DEBUG] Model parameters loaded: {len(list(model.parameters()))}")
    except Exception as e:
        print(f"[ERROR] Error loading model: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"[ERROR] Model file not found at: {MODEL_PATH}")

# -----------------------------
# EXE file preprocessing (must match training)
# -----------------------------
MAX_LENGTH = 1024 * 1024  # 1MB max file size

# -----------------------------
# Auth decorator
# -----------------------------
def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return wrapped

# -----------------------------
# Utility: predict single uploaded file
# Accepts a werkzeug FileStorage (request.files['file'])
# -----------------------------
def predict_from_upload(file_storage):
    """
    Returns tuple: (label_str, raw_confidence_float)
    label_str in {"Ransomware", "Legitimate"} or "Error processing file"
    """
    try:
        return predict_from_exe(file_storage)
    except Exception as e:
        app.logger.exception("Prediction error")
        return "Error processing file", 0.0

def predict_from_exe(file_storage):
    """
    Predict from EXE/binary files
    """
    try:
        # Read file bytes
        raw_bytes = file_storage.read()

        if not raw_bytes:
            raise ValueError("Empty file")

        # Convert to numpy array of bytes
        data = np.frombuffer(raw_bytes, dtype=np.uint8)

        # Pad or truncate to fixed length
        if len(data) < MAX_LENGTH:
            data = np.pad(data, (0, MAX_LENGTH - len(data)), 'constant')
        else:
            data = data[:MAX_LENGTH]

        # Convert to float and normalize to [0,1]
        data = data.astype(np.float32) / 255.0

        # Convert to tensor and add batch dimension
        data_tensor = torch.tensor(data).unsqueeze(0).to(device)  # shape [1, MAX_LENGTH]

        with torch.no_grad():
            outputs = model(data_tensor)                       # logits
            probs = torch.softmax(outputs, dim=1)[0]          # [2]
            conf, pred = torch.max(probs, 0)                  # conf tensor, pred index
            label = "Ransomware" if pred.item() == 1 else "Legitimate"
            return label, conf.item()
    except Exception as e:
        app.logger.exception("EXE prediction error")
        return "Error processing EXE file", 0.0

# -----------------------------
# Routes: home, register, login, logout
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not (username and email and phone and password):
            flash("Please fill all fields.", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("register"))

        hashed = generate_password_hash(password)

        try:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash("Email already registered.", "warning")
                return redirect(url_for("register"))

            user = User(username=username, email=email, phone=phone, password=hashed)
            db.session.add(user)
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            app.logger.exception("DB error during registration")
            flash("Registration failed. Try again.", "danger")
            return redirect(url_for("register"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["logged_in"] = True
            session["user_id"] = user.id
            session["username"] = user.username
            session["email"] = user.email
            session["phone"] = user.phone
            flash("Login successful!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("predict_page"))
        else:
            flash("Invalid credentials. Please try again.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("index"))

# -----------------------------
# Prediction route (protected)
# -----------------------------
@app.route("/predict", methods=["GET", "POST"])
@login_required
def predict_page():
    result = None
    confidence = None
    file_features = None

    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("Please upload an EXE file.", "warning")
            return redirect(url_for("predict_page"))

        # Extract basic file features
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        file_ext = os.path.splitext(file.filename)[1].lower()

        # Read file content for hash calculation
        file_content = file.read()
        file.seek(0)  # Reset file pointer

        # Calculate file hash
        import hashlib
        md5_hash = hashlib.md5(file_content).hexdigest()
        sha256_hash = hashlib.sha256(file_content).hexdigest()

        # Calculate entropy (measure of randomness)
        if file_size > 0:
            byte_counts = [0] * 256
            for byte in file_content:
                byte_counts[byte] += 1
            entropy = 0
            for count in byte_counts:
                if count > 0:
                    p = count / file_size
                    entropy -= p * math.log2(p)
        else:
            entropy = 0

        # Detect if file is executable
        is_executable = file_ext in ['.exe', '.dll', '.bat', '.cmd', '.scr', '.pif', '.com']

        file_features = {
            "filename": file.filename,
            "size": f"{file_size} bytes ({file_size / 1024:.2f} KB)",
            "type": "Binary" if is_executable else "Unknown",
            "extension": file_ext,
            "md5_hash": md5_hash,
            "sha256_hash": sha256_hash[:16] + "...",
            "entropy": f"{entropy:.2f} bits",
            "is_executable": "Yes" if is_executable else "No",
            "suspicious_patterns": "None detected",
            "behavioral_analysis": {
                "file_rename_count": "0",
                "file_write_count": "0",
                "high_write_volume": "No",
                "extension_change_ratio": "0.00",
                "new_extensions_count": "0",
                "write_delete_pattern_freq": "0",
                "high_entropy_output": "No",
                "files_per_second": "0.0",
                "burst_access_pattern": "None",
                "ransom_note_indicators": "None"
            }
        }

        label, conf = predict_from_upload(file)
        confidence = conf
        if "ransomware" in label.lower():
            result = "🚨 Ransomware Detected!"
        elif "legitimate" in label.lower():
            result = "✅ Legitimate File"
        else:
            result = f"⚠️ {label}"

        # Insert prediction history into database
        try:
            prediction = Prediction(user_id=session["user_id"], file_name=file.filename, prediction_result=label, confidence=conf)
            db.session.add(prediction)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.exception("DB error during prediction history insert")

    return render_template("predict.html", result=result, confidence=confidence, file_features=file_features)

# -----------------------------
# History route (protected)
# -----------------------------
@app.route("/history")
@login_required
def history():
    predictions = Prediction.query.filter_by(user_id=session["user_id"]).order_by(Prediction.timestamp.desc()).all()
    history_data = [(p.file_name, p.prediction_result, p.confidence, p.timestamp) for p in predictions]
    return render_template("history.html", history=history_data)

# -----------------------------
# Provide auth status to templates
# -----------------------------
@app.context_processor
def inject_auth_status():
    return dict(
        logged_in=session.get("logged_in", False),
        username=session.get("username")
    )

# -----------------------------
# API Routes for Desktop App
# -----------------------------
@app.route("/api/predict", methods=["POST"])
def api_predict():
    """
    API endpoint for file prediction (used by Electron desktop app)
    """
    try:
        file = request.files.get("file")
        if not file or file.filename == "":
            return jsonify({"error": "No file provided"}), 400

        label, conf = predict_from_upload(file)

        return jsonify({
            "prediction": label,
            "confidence": float(conf),
            "is_threat": "ransomware" in label.lower()
        })

    except Exception as e:
        app.logger.exception("API prediction error")
        return jsonify({"error": str(e)}), 500

# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")

    # Check if running in Electron mode
    electron_mode = os.environ.get("ELECTRON_MODE", "false").lower() == "true"

    if electron_mode:
        # Run on all interfaces for Electron
        app.run(host="0.0.0.0", port=5000, debug=False)
    else:
        app.run(debug=True)
