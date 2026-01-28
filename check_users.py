from app import db, User, app

with app.app_context():
    users = User.query.all()
    print(f"Total users in database: {len(users)}")
    for user in users:
        print(f"ID: {user.id}, Email: {user.email}, Username: {user.username}")
    if not users:
        print("No users found in database. You need to register first.")
