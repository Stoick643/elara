"""
Database Migration Script
Wrapper around the unified database manager.
"""
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.db_manager import DatabaseManager

def migrate_database():
    """Migrate database using the unified database manager."""
    print("[INFO] Using unified database manager for migration...")
    
    db_manager = DatabaseManager()
    
    # Create backup before migration
    backup_first = '--no-backup' not in sys.argv
    
    if db_manager.migrate_database(backup_first=backup_first):
        print("Database migration complete!")
        print("Your existing data has been preserved!")
        return True
    else:
        print("Database migration failed!")
        print("Try using: python -m models.db_manager reset")
        return False

if __name__ == '__main__':
    success = migrate_database()
    sys.exit(0 if success else 1)