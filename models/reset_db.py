#!/usr/bin/env python3
"""
Database Reset Script
Wrapper around the unified database manager.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.db_manager import DatabaseManager

def reset_database():
    """Reset database using the unified database manager."""
    print("[INFO] Using unified database manager for reset...")
    
    db_manager = DatabaseManager()
    
    # Check if user wants to preserve admin
    preserve_admin = '--preserve-admin' in sys.argv or input("Preserve admin user? (y/N): ").lower().startswith('y')
    
    if db_manager.reset_database(preserve_admin=preserve_admin):
        print("Database reset complete!")
        return True
    else:
        print("Database reset failed!")
        return False

if __name__ == '__main__':
    success = reset_database()
    sys.exit(0 if success else 1)