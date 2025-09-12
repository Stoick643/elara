"""
Emergency migration script to add missing columns to existing database.
This fixes the error: no such column: users.onboarding_completed
"""
import sqlite3
import os

def add_missing_columns():
    """Add the new onboarding and pro mode columns to existing database."""
    
    # Try both possible database locations
    db_paths = ['instance/database.db', 'data/elara.db', 'database.db']
    db_path = None
    
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            print(f"Found database at: {path}")
            break
    
    if not db_path:
        print("[ERROR] No database found! Run the app first to create one.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check which columns already exist
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        print(f"Existing columns: {existing_columns}")
        
        # Add missing columns one by one
        columns_to_add = [
            ('onboarding_completed', 'BOOLEAN DEFAULT 0'),
            ('onboarding_step', 'INTEGER DEFAULT 0'),
            ('is_pro_mode', 'BOOLEAN DEFAULT 0')
        ]
        
        for column_name, column_def in columns_to_add:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_def}')
                    print(f"[OK] Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"[WARNING] Could not add {column_name}: {e}")
            else:
                print(f"[INFO] Column {column_name} already exists")
        
        conn.commit()
        print("\n[SUCCESS] Database schema updated successfully!")
        print("You can now run the application without errors.")
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Error updating database: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_missing_columns()