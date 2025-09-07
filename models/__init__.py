from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and personalization."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar_personality = db.Column(db.String(20), nullable=True)  # sage, champion, friend, strategist, zen_master
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    journal_entries = db.relationship('JournalEntry', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class JournalEntry(db.Model):
    """Journal entries with mood and energy tracking."""
    __tablename__ = 'journal_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    mood_score = db.Column(db.Integer, nullable=True)  # 1-10 scale
    energy_level = db.Column(db.Integer, nullable=True)  # 1-10 scale
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_mood_emoji(self):
        """Return emoji based on mood score."""
        if not self.mood_score:
            return "😐"
        mood_emojis = {
            1: "😢", 2: "😞", 3: "😔", 4: "😕", 5: "😐",
            6: "🙂", 7: "😊", 8: "😄", 9: "😁", 10: "🤩"
        }
        return mood_emojis.get(self.mood_score, "😐")
    
    def get_mood_color(self):
        """Return color class based on mood score."""
        if not self.mood_score:
            return "text-gray-500"
        if self.mood_score <= 3:
            return "text-red-500"
        elif self.mood_score <= 5:
            return "text-orange-500"
        elif self.mood_score <= 7:
            return "text-yellow-500"
        else:
            return "text-green-500"
    
    def __repr__(self):
        return f'<JournalEntry {self.id} - Mood: {self.mood_score}>'


class Task(db.Model):
    """Simple task management."""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.Date, nullable=True)
    energy_required = db.Column(db.String(10), default='medium')  # low, medium, high
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def mark_complete(self):
        """Mark task as completed with timestamp."""
        self.completed = True
        self.completed_at = datetime.utcnow()
    
    def get_energy_icon(self):
        """Return icon based on energy required."""
        energy_icons = {
            'low': '🟢',
            'medium': '🟡', 
            'high': '🔴'
        }
        return energy_icons.get(self.energy_required, '🟡')
    
    def __repr__(self):
        return f'<Task {self.title} - {"✓" if self.completed else "○"}>'