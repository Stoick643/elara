"""
Reset database with new Phase 2 schema.
This will delete existing data and create fresh tables.
"""
import os
from app import create_app
from models import db, User

def reset_database():
    app = create_app()
    
    with app.app_context():
        # Delete existing database files
        db_paths = ['database.db', 'instance/database.db']
        for db_path in db_paths:
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                    print(f"Deleted old database: {db_path}")
                except PermissionError:
                    print(f"Warning: Could not delete {db_path} (file may be locked by running application)")
                    print("Please stop the Flask application and run this script again.")
        
        # Create all tables with new schema
        db.create_all()
        print("Created new database with Phase 2 schema")
        
        # Create default user with personality (if not exists)
        existing_user = User.query.filter_by(username='me').first()
        if not existing_user:
            default_user = User(
                username='me',
                avatar_personality='friend'
            )
            default_user.set_password('elara2024')
            
            db.session.add(default_user)
            db.session.commit()
            print("Created default user: me/elara2024 with Friend personality")
        else:
            # Update existing user with personality
            if not existing_user.avatar_personality:
                existing_user.avatar_personality = 'friend'
                db.session.commit()
            print(f"Updated existing user: {existing_user.username} with {existing_user.avatar_personality} personality")
        print("Database ready for Phase 2 features!")

if __name__ == '__main__':
    reset_database()