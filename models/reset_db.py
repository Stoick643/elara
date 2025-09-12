#!/usr/bin/env python3
"""
Database Reset Script
Drops all tables and recreates them with the latest schema.
"""

import os
import sys
from models import db, User
from app import create_app

def reset_database():
    """Reset database by dropping and recreating all tables."""
    app = create_app()
    
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating all tables with new schema...")
        db.create_all()
        
        # Create default user if not exists
        if User.query.count() == 0:
            print("Creating default user...")
            default_user = User(
                username=app.config['DEFAULT_USERNAME'],
                avatar_personality='friend'
            )
            default_user.set_password(app.config['DEFAULT_PASSWORD'])
            db.session.add(default_user)
            db.session.commit()
            print(f"Created default user: {app.config['DEFAULT_USERNAME']}")
        
        print("Database reset complete!")

if __name__ == '__main__':
    reset_database()