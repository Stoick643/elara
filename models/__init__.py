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
    values = db.relationship('Value', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    goals = db.relationship('Goal', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    habits = db.relationship('Habit', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
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
    """Task management with goal linking."""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=True)  # Link to goal
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.Date, nullable=True)
    energy_required = db.Column(db.String(10), default='medium')  # low, medium, high
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def mark_complete(self):
        """Mark task as completed with timestamp and update goal progress."""
        self.completed = True
        self.completed_at = datetime.utcnow()
        
        # Update goal progress if task is linked to a goal
        if self.goal:
            self.goal.calculate_progress()
            db.session.commit()
    
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


class Value(db.Model):
    """Life area values for goal categorization."""
    __tablename__ = 'values'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # Career, Health, Relationships, etc.
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.Integer, default=1)  # 1-10 importance scale
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    goals = db.relationship('Goal', backref='value', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Value {self.name}>'


class Goal(db.Model):
    """Goals linked to values with progress tracking."""
    __tablename__ = 'goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    value_id = db.Column(db.Integer, db.ForeignKey('values.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    target_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='active')  # active, completed, paused
    progress = db.Column(db.Integer, default=0)  # 0-100 percentage
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    tasks = db.relationship('Task', backref='goal', lazy='dynamic')
    
    def calculate_progress(self):
        """Calculate progress based on linked tasks."""
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0
        
        completed_tasks = self.tasks.filter_by(completed=True).count()
        progress = int((completed_tasks / total_tasks) * 100)
        self.progress = progress
        return progress
    
    def mark_complete(self):
        """Mark goal as completed."""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.progress = 100
    
    def get_status_color(self):
        """Return color class based on status."""
        status_colors = {
            'active': 'text-primary',
            'completed': 'text-success',
            'paused': 'text-warning'
        }
        return status_colors.get(self.status, 'text-secondary')
    
    def __repr__(self):
        return f'<Goal {self.title} - {self.progress}%>'


class Habit(db.Model):
    """Habit tracking with cue-routine-reward structure."""
    __tablename__ = 'habits'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Habit Loop components
    cue = db.Column(db.String(500), nullable=False)  # Trigger/reminder
    routine = db.Column(db.String(500), nullable=False)  # The behavior
    reward = db.Column(db.String(500), nullable=False)  # The benefit
    
    # Tracking
    frequency = db.Column(db.String(20), default='daily')  # daily, weekly
    streak_count = db.Column(db.Integer, default=0)
    best_streak = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_completed = db.Column(db.Date, nullable=True)
    
    # Relationships
    habit_logs = db.relationship('HabitLog', backref='habit', lazy='dynamic', cascade='all, delete-orphan')
    
    def check_in_today(self):
        """Mark habit as completed for today."""
        today = datetime.utcnow().date()
        
        # Check if already completed today
        existing_log = self.habit_logs.filter_by(completed_date=today).first()
        if existing_log:
            return False  # Already completed today
        
        # Create new log entry
        log = HabitLog(habit_id=self.id, completed_date=today)
        db.session.add(log)
        
        # Update streak
        self.update_streak(today)
        self.last_completed = today
        
        return True
    
    def update_streak(self, completion_date):
        """Update streak count based on completion date."""
        if not self.last_completed:
            self.streak_count = 1
        else:
            # Check if completion is consecutive
            days_diff = (completion_date - self.last_completed).days
            if days_diff == 1:  # Consecutive day
                self.streak_count += 1
            elif days_diff > 1:  # Missed days, reset streak
                self.streak_count = 1
        
        # Update best streak
        if self.streak_count > self.best_streak:
            self.best_streak = self.streak_count
    
    def is_completed_today(self):
        """Check if habit was completed today."""
        today = datetime.utcnow().date()
        return self.habit_logs.filter_by(completed_date=today).first() is not None
    
    def get_streak_emoji(self):
        """Return emoji based on streak count."""
        if self.streak_count == 0:
            return "⭕"
        elif self.streak_count < 7:
            return "🔥"
        elif self.streak_count < 30:
            return "💪"
        else:
            return "🏆"
    
    def __repr__(self):
        return f'<Habit {self.name} - {self.streak_count} days>'


class HabitLog(db.Model):
    """Daily habit completion tracking."""
    __tablename__ = 'habit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=False)
    completed_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<HabitLog {self.habit_id} - {self.completed_date}>'