"""
Quick script to fix existing user's personality for testing.
Run this if your database already exists without personality.
"""
from app import create_app
from models import db, User

def fix_user_personality():
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username='me').first()
        if user and not user.avatar_personality:
            user.avatar_personality = 'friend'
            db.session.commit()
            print(f"✅ Updated user '{user.username}' with Friend personality")
        elif user:
            print(f"✅ User '{user.username}' already has personality: {user.avatar_personality}")
        else:
            print("❌ User 'me' not found")

if __name__ == '__main__':
    fix_user_personality()