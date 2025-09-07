"""
Migrate existing database to Phase 2 schema while preserving data.
This adds new columns without losing existing journal entries and tasks.
"""
import sqlite3
from app import create_app
from models import db, User

def migrate_database():
    app = create_app()
    
    # Direct SQLite connection for schema changes
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    try:
        print("🔄 Starting database migration to Phase 2...")
        
        # Add new columns to existing tables
        
        # 1. Add goal_id to tasks table
        try:
            cursor.execute('ALTER TABLE tasks ADD COLUMN goal_id INTEGER REFERENCES goals(id)')
            print("✅ Added goal_id to tasks table")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("⚠️  goal_id column already exists in tasks")
            else:
                print(f"❌ Error adding goal_id to tasks: {e}")
        
        # 2. Create new Phase 2 tables
        with app.app_context():
            # This will create new tables without affecting existing ones
            db.create_all()
            print("✅ Created new Phase 2 tables (values, goals, habits, habit_logs)")
            
            # Update existing user with personality if needed
            user = User.query.filter_by(username='me').first()
            if user and not user.avatar_personality:
                user.avatar_personality = 'friend'
                db.session.commit()
                print("✅ Updated existing user with Friend personality")
            elif user:
                print(f"✅ User personality already set: {user.avatar_personality}")
        
        conn.commit()
        print("🎉 Database migration completed successfully!")
        print("🚀 Your existing journal entries and tasks are preserved!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        print("💡 Try using reset_database.py instead")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()