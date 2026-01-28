from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ransomware.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    predictions = db.relationship('Prediction', backref='user', lazy=True)

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    prediction_result = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()
    print("Database tables created.")

    # Check if tables exist
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("Tables:", tables)

    # Try to add a test user
    try:
        hashed = generate_password_hash("testpass")
        test_user = User(username="testuser", email="test@example.com", phone="1234567890", password=hashed)
        db.session.add(test_user)
        db.session.commit()
        print("Test user added.")
    except Exception as e:
        print("Error adding test user:", e)
        db.session.rollback()

    # Query the user
    user = User.query.filter_by(email="test@example.com").first()
    if user:
        print("User found:", user.username, user.email)
        if check_password_hash(user.password, "testpass"):
            print("Password check passed.")
        else:
            print("Password check failed.")
    else:
        print("User not found.")
