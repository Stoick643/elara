"""
DEPRECATED: This script has been replaced by the unified database manager.

This script was used to fix missing columns in the database schema.
Please use the new unified database management system instead.

For database migrations, use:
    python -m models.db_manager migrate

For a complete database reset with schema updates:
    python -m models.db_manager reset

For more options:
    python -m models.db_manager
"""

import sys
import os

def show_deprecation_notice():
    """Show deprecation notice and redirect to new system."""
    print("[DEPRECATED] This script has been replaced!")
    print("")
    print("Please use the unified database manager instead:")
    print("  python -m models.db_manager migrate     # Apply schema updates")
    print("  python -m models.db_manager reset       # Complete reset")
    print("  python -m models.db_manager status      # Check database status")
    print("")
    print("For more options, run:")
    print("  python -m models.db_manager")
    print("")
    
    # Offer to run migration automatically
    response = input("Would you like me to run the migration now? (y/N): ")
    if response.lower().startswith('y'):
        print("\nRunning migration with unified database manager...")
        # Add parent directory to path for imports
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        try:
            from models.db_manager import DatabaseManager
            db_manager = DatabaseManager()
            if db_manager.migrate_database():
                print("Migration completed successfully!")
            else:
                print("Migration failed. Please check the error messages above.")
        except Exception as e:
            print(f"Error running migration: {e}")
            print("Please run: python -m models.db_manager migrate")

if __name__ == '__main__':
    show_deprecation_notice()