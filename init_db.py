import os
from app import db, User, Prediction

# Initialize database
with db.session.begin():
    # Create tables
    db.create_all()

    # Check if user exists
    existing_user = User.query.filter_by(email='user@gmail.com').first()
    if not existing_user:
        # Create default user
        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash('password')  # Change this to your desired password
        user = User(username='user', email='user@gmail.com', phone='8317306907', password=hashed_password)
        db.session.add(user)
        print("Default user created: user@gmail.com / password")
    else:
        print("User already exists")

print("Database initialized successfully")
