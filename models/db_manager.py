"""
Unified Database Manager for Elara
Centralizes all database operations with configuration-driven approach.
"""
import os
import sys
import shutil
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from app import create_app


class DatabaseManager:
    """Central manager for all database operations."""
    
    def __init__(self):
        self.app = create_app()
        self.config = self.app.config
    
    def get_database_path(self) -> str:
        """Returns the configured database path from config."""
        # Extract path from SQLAlchemy URI
        db_uri = self.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            return db_uri.replace('sqlite:///', '')
        elif db_uri.startswith('sqlite://'):
            return db_uri.replace('sqlite://', '')
        else:
            # For non-SQLite databases, return None or raise error
            raise ValueError(f"Database manager only supports SQLite. Got: {db_uri}")
    
    def database_exists(self) -> bool:
        """Check if database file exists."""
        try:
            db_path = self.get_database_path()
            return os.path.exists(db_path)
        except ValueError:
            # For non-SQLite databases, assume it exists if we can connect
            return True
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """Creates timestamped backup of database."""
        if not self.database_exists():
            raise FileNotFoundError("No database found to backup")
        
        # Create backup directory
        backup_dir = os.path.join(os.path.dirname(self.get_database_path()), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename
        if not backup_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f'elara_backup_{timestamp}.db'
        
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Copy database file
        shutil.copy2(self.get_database_path(), backup_path)
        print(f"[OK] Database backed up to: {backup_path}")
        
        return backup_path
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restores database from backup file."""
        if not os.path.exists(backup_path):
            print(f"[ERROR] Backup file not found: {backup_path}")
            return False
        
        db_path = self.get_database_path()
        
        # Create backup of current database before restore
        if self.database_exists():
            current_backup = self.create_backup('pre_restore_backup.db')
            print(f"[INFO] Current database backed up to: {current_backup}")
        
        # Restore from backup
        try:
            shutil.copy2(backup_path, db_path)
            print(f"[OK] Database restored from: {backup_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to restore backup: {e}")
            return False
    
    def reset_database(self, preserve_admin: bool = False) -> bool:
        """Drops all tables and recreates schema."""
        try:
            with self.app.app_context():
                from models import db, User
                
                # Backup admin user if requested
                admin_data = None
                if preserve_admin:
                    admin_user = User.query.filter_by(username=self.config.get('DEFAULT_USERNAME', 'me')).first()
                    if admin_user:
                        admin_data = {
                            'username': admin_user.username,
                            'password_hash': admin_user.password_hash,
                            'avatar_personality': admin_user.avatar_personality
                        }
                
                print("[INFO] Dropping all tables...")
                db.drop_all()
                
                print("[INFO] Creating all tables with latest schema...")
                db.create_all()
                
                # Restore admin user if preserved
                if preserve_admin and admin_data:
                    admin_user = User(
                        username=admin_data['username'],
                        avatar_personality=admin_data['avatar_personality']
                    )
                    admin_user.password_hash = admin_data['password_hash']
                    db.session.add(admin_user)
                    db.session.commit()
                    print(f"[OK] Preserved admin user: {admin_data['username']}")
                elif not preserve_admin:
                    # Create default user
                    default_user = User(
                        username=self.config.get('DEFAULT_USERNAME', 'me'),
                        avatar_personality='friend'
                    )
                    default_user.set_password(self.config.get('DEFAULT_PASSWORD', 'elara2024'))
                    db.session.add(default_user)
                    db.session.commit()
                    print(f"[OK] Created default user: {default_user.username}")
                
                print("[SUCCESS] Database reset complete!")
                return True
                
        except Exception as e:
            print(f"[ERROR] Database reset failed: {e}")
            return False
    
    def migrate_database(self, backup_first: bool = True) -> bool:
        """Applies pending schema changes while preserving data."""
        try:
            if backup_first and self.database_exists():
                self.create_backup()
            
            with self.app.app_context():
                from models import db
                
                print("[INFO] Applying database migrations...")
                
                # Create any missing tables
                db.create_all()
                
                # Check for missing columns and add them
                missing_columns = self._check_missing_columns()
                if missing_columns:
                    self._add_missing_columns(missing_columns)
                
                print("[SUCCESS] Database migration complete!")
                return True
                
        except Exception as e:
            print(f"[ERROR] Database migration failed: {e}")
            return False
    
    def check_database_status(self) -> Dict:
        """Returns dictionary with database health information."""
        status = {
            'database_exists': False,
            'database_path': None,
            'tables': [],
            'row_counts': {},
            'schema_issues': []
        }
        
        try:
            status['database_path'] = self.get_database_path()
            status['database_exists'] = self.database_exists()
            
            if status['database_exists']:
                with self.app.app_context():
                    from models import db, User
                    
                    # Get table names
                    inspector = db.inspect(db.engine)
                    status['tables'] = inspector.get_table_names()
                    
                    # Get row counts for main tables
                    try:
                        status['row_counts']['users'] = User.query.count()
                    except:
                        status['row_counts']['users'] = 'Error'
                    
                    # Check for schema issues
                    missing_columns = self._check_missing_columns()
                    if missing_columns:
                        status['schema_issues'] = missing_columns
        
        except Exception as e:
            status['error'] = str(e)
        
        return status
    
    def _check_missing_columns(self) -> List[Dict]:
        """Check for columns that exist in models but not in database."""
        missing_columns = []
        
        try:
            db_path = self.get_database_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check users table for our new columns
            cursor.execute("PRAGMA table_info(users)")
            existing_columns = [column[1] for column in cursor.fetchall()]
            
            required_columns = [
                'onboarding_completed',
                'onboarding_step', 
                'is_pro_mode'
            ]
            
            for column in required_columns:
                if column not in existing_columns:
                    missing_columns.append({
                        'table': 'users',
                        'column': column,
                        'type': 'BOOLEAN DEFAULT 0' if 'completed' in column or 'mode' in column else 'INTEGER DEFAULT 0'
                    })
            
            conn.close()
            
        except Exception as e:
            print(f"[WARNING] Could not check for missing columns: {e}")
        
        return missing_columns
    
    def _add_missing_columns(self, missing_columns: List[Dict]) -> None:
        """Add missing columns to database."""
        db_path = self.get_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            for column_info in missing_columns:
                table = column_info['table']
                column = column_info['column']
                col_type = column_info['type']
                
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {col_type}')
                print(f"[OK] Added column {table}.{column}")
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Failed to add missing columns: {e}")
            raise
        finally:
            conn.close()
    
    def create_sample_data(self) -> bool:
        """Generates demo data for development and testing."""
        try:
            with self.app.app_context():
                from models import db, User, Value, Goal, Habit
                
                # Check if sample data already exists
                if User.query.count() > 1:  # More than just the default user
                    print("[INFO] Sample data appears to already exist")
                    return True
                
                print("[INFO] Creating sample data...")
                
                # Create sample user
                sample_user = User.query.filter_by(username='demo').first()
                if not sample_user:
                    sample_user = User(
                        username='demo',
                        avatar_personality='champion'
                    )
                    sample_user.set_password('demo123')
                    sample_user.onboarding_completed = True
                    sample_user.is_pro_mode = True
                    db.session.add(sample_user)
                    db.session.commit()
                
                # Add sample values
                sample_values = [
                    ('Growth', 'Continuous learning and self-improvement'),
                    ('Health', 'Physical and mental wellbeing'),
                    ('Connection', 'Meaningful relationships with others')
                ]
                
                for i, (name, desc) in enumerate(sample_values, 1):
                    if not Value.query.filter_by(user_id=sample_user.id, name=name).first():
                        value = Value(user_id=sample_user.id, name=name, description=desc, priority=i)
                        db.session.add(value)
                
                db.session.commit()
                
                # Add sample goal
                first_value = Value.query.filter_by(user_id=sample_user.id).first()
                if first_value and not Goal.query.filter_by(user_id=sample_user.id).first():
                    goal = Goal(
                        user_id=sample_user.id,
                        title="Read 12 books this year",
                        description="Expand knowledge and perspective through regular reading",
                        value_id=first_value.id,
                        status='active',
                        progress=25
                    )
                    db.session.add(goal)
                
                # Add sample habit
                if not Habit.query.filter_by(user_id=sample_user.id).first():
                    habit = Habit(
                        user_id=sample_user.id,
                        name="Daily reading",
                        cue_type='time',
                        cue_time='20:00',
                        routine='Read for 30 minutes before bed',
                        reward='Feel accomplished and learn something new',
                        frequency='daily',
                        active=True,
                        streak_count=7
                    )
                    db.session.add(habit)
                
                db.session.commit()
                print("[OK] Sample data created successfully!")
                return True
                
        except Exception as e:
            print(f"[ERROR] Failed to create sample data: {e}")
            return False


# CLI Interface
def main():
    """Command line interface for database management."""
    if len(sys.argv) < 2:
        print("""
Database Manager Commands:
  reset     - Reset database (fresh start)
  migrate   - Apply pending migrations
  backup    - Create database backup
  restore   - Restore from backup file
  status    - Show database status
  sample    - Create sample data
  
Usage: python -m models.db_manager [command] [options]
        """)
        return
    
    command = sys.argv[1].lower()
    db_manager = DatabaseManager()
    
    if command == 'reset':
        preserve = '--preserve-admin' in sys.argv
        if db_manager.reset_database(preserve_admin=preserve):
            print("Database reset successful!")
        else:
            print("Database reset failed!")
            sys.exit(1)
    
    elif command == 'migrate':
        if db_manager.migrate_database():
            print("Migration successful!")
        else:
            print("Migration failed!")
            sys.exit(1)
    
    elif command == 'backup':
        try:
            backup_path = db_manager.create_backup()
            print(f"Backup created: {backup_path}")
        except Exception as e:
            print(f"Backup failed: {e}")
            sys.exit(1)
    
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("Usage: python -m models.db_manager restore <backup_path>")
            sys.exit(1)
        backup_path = sys.argv[2]
        if db_manager.restore_backup(backup_path):
            print("Restore successful!")
        else:
            print("Restore failed!")
            sys.exit(1)
    
    elif command == 'status':
        status = db_manager.check_database_status()
        print(f"Database Path: {status.get('database_path', 'Unknown')}")
        print(f"Database Exists: {status.get('database_exists', False)}")
        if status.get('tables'):
            print(f"Tables: {', '.join(status['tables'])}")
        if status.get('row_counts'):
            print("Row Counts:")
            for table, count in status['row_counts'].items():
                print(f"  {table}: {count}")
        if status.get('schema_issues'):
            print("Schema Issues:")
            for issue in status['schema_issues']:
                print(f"  Missing: {issue['table']}.{issue['column']}")
        if status.get('error'):
            print(f"Error: {status['error']}")
    
    elif command == 'sample':
        if db_manager.create_sample_data():
            print("Sample data created!")
        else:
            print("Sample data creation failed!")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()