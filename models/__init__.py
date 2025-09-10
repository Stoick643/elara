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
    
    # Level A: Vision and Values Discovery
    vision_statements = db.relationship('VisionStatement', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    value_assessments = db.relationship('CoreValueAssessment', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    life_assessments = db.relationship('LifeAssessment', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    def get_current_vision(self):
        """Get user's current active vision statement."""
        return self.vision_statements.filter_by(is_current=True).first()
    
    def get_current_values_assessment(self):
        """Get user's current values assessment."""
        return self.value_assessments.filter_by(is_current=True).first()
    
    def has_completed_discovery(self):
        """Check if user has completed both values and vision discovery."""
        has_values = self.get_current_values_assessment() is not None
        has_vision = self.get_current_vision() is not None
        return has_values and has_vision
    
    def get_discovery_progress(self):
        """Return discovery completion status for onboarding."""
        return {
            'values_assessment': self.get_current_values_assessment() is not None,
            'vision_statement': self.get_current_vision() is not None,
            'goals_aligned': self.goals.filter(Goal.value_id.isnot(None)).count() > 0,
            'overall_complete': self.has_completed_discovery()
        }
    
    def get_orphaned_tasks(self):
        """Get tasks not connected to any goal."""
        return self.tasks.filter_by(goal_id=None, completed=False).all()
    
    def get_orphaned_tasks_count(self):
        """Count of tasks not connected to goals."""
        return self.tasks.filter_by(goal_id=None, completed=False).count()
    
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


class ChatHistory(db.Model):
    """Store conversation history with AI coach."""
    __tablename__ = 'chat_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    personality_used = db.Column(db.String(20), nullable=True)  # Avatar personality at time of message
    tokens_used = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'personality': self.personality_used,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    def __repr__(self):
        return f'<ChatHistory {self.role} - {self.timestamp}>'


class WeeklyReview(db.Model):
    """Store weekly review reflections and insights."""
    __tablename__ = 'weekly_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    week_start_date = db.Column(db.Date, nullable=False)
    week_end_date = db.Column(db.Date, nullable=False)
    
    # Reflection responses
    goals_reflection = db.Column(db.Text, nullable=True)  # What goals did you work on?
    wins_celebration = db.Column(db.Text, nullable=True)  # What went well?
    challenges_faced = db.Column(db.Text, nullable=True)  # What was challenging?
    lessons_learned = db.Column(db.Text, nullable=True)  # What did you learn?
    next_week_focus = db.Column(db.Text, nullable=True)  # What's the focus for next week?
    
    # Metrics (stored as JSON)
    performance_metrics = db.Column(db.JSON, nullable=True)  # task_completion_rate, mood_average, etc.
    
    # AI-generated insights
    ai_insights = db.Column(db.Text, nullable=True)
    ai_recommendations = db.Column(db.JSON, nullable=True)  # List of recommendations
    
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<WeeklyReview {self.week_start_date} - {self.week_end_date}>'


class LifeAssessment(db.Model):
    """Life Balance Assessment model - Wheel of Life functionality."""
    __tablename__ = 'life_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Life area scores (1-10 scale)
    career_score = db.Column(db.Integer, nullable=False)
    health_score = db.Column(db.Integer, nullable=False)
    relationships_score = db.Column(db.Integer, nullable=False)
    finance_score = db.Column(db.Integer, nullable=False)
    personal_growth_score = db.Column(db.Integer, nullable=False)
    fun_recreation_score = db.Column(db.Integer, nullable=False)
    environment_score = db.Column(db.Integer, nullable=False)
    purpose_score = db.Column(db.Integer, nullable=False)
    
    # Calculated fields
    overall_balance = db.Column(db.Float, nullable=True)
    
    # Metadata
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def calculate_balance(self):
        """Calculate overall balance score and identify key areas."""
        scores = [
            self.career_score,
            self.health_score,
            self.relationships_score,
            self.finance_score,
            self.personal_growth_score,
            self.fun_recreation_score,
            self.environment_score,
            self.purpose_score
        ]
        
        # Calculate average
        self.overall_balance = sum(scores) / len(scores)
        
        # Get area names and scores for analysis
        areas = [
            ('Career & Work', self.career_score),
            ('Health & Fitness', self.health_score),
            ('Relationships', self.relationships_score),
            ('Money & Finance', self.finance_score),
            ('Personal Growth', self.personal_growth_score),
            ('Fun & Recreation', self.fun_recreation_score),
            ('Home Environment', self.environment_score),
            ('Purpose & Meaning', self.purpose_score)
        ]
        
        # Sort areas by score
        areas_sorted = sorted(areas, key=lambda x: x[1])
        
        return {
            'overall_balance': round(self.overall_balance, 1),
            'lowest_areas': areas_sorted[:3],  # Bottom 3 areas
            'highest_areas': areas_sorted[-3:],  # Top 3 areas
            'all_scores': dict(areas)
        }
    
    def get_improvement_areas(self):
        """Get list of areas needing attention (score < 5)."""
        areas = [
            ('Career & Work', self.career_score),
            ('Health & Fitness', self.health_score),
            ('Relationships', self.relationships_score),
            ('Money & Finance', self.finance_score),
            ('Personal Growth', self.personal_growth_score),
            ('Fun & Recreation', self.fun_recreation_score),
            ('Home Environment', self.environment_score),
            ('Purpose & Meaning', self.purpose_score)
        ]
        
        # Filter areas that need attention
        improvement_areas = [area for area in areas if area[1] < 5]
        
        # Sort by lowest score first (most critical)
        improvement_areas.sort(key=lambda x: x[1])
        
        # Add priority levels
        result = []
        for area_name, score in improvement_areas:
            if score <= 2:
                priority = 'critical'
            elif score <= 3:
                priority = 'high'
            else:
                priority = 'moderate'
            
            result.append({
                'area': area_name,
                'score': score,
                'priority': priority
            })
        
        return result
    
    def get_scores_dict(self):
        """Return all scores as a dictionary for easy template access."""
        return {
            'Career & Work': self.career_score,
            'Health & Fitness': self.health_score,
            'Relationships': self.relationships_score,
            'Money & Finance': self.finance_score,
            'Personal Growth': self.personal_growth_score,
            'Fun & Recreation': self.fun_recreation_score,
            'Home Environment': self.environment_score,
            'Purpose & Meaning': self.purpose_score
        }
    
    def __repr__(self):
        return f'<LifeAssessment User {self.user_id} - Balance: {self.overall_balance or "Not calculated"}>'


class Insight(db.Model):
    """Store AI-generated insights and patterns."""
    __tablename__ = 'insights'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    insight_type = db.Column(db.String(50), nullable=False)  # 'correlation', 'pattern', 'trend', 'recommendation'
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Statistical confidence (0.0 to 1.0)
    confidence_score = db.Column(db.Float, nullable=True)
    
    # Supporting data (stored as JSON)
    supporting_data = db.Column(db.JSON, nullable=True)  # Charts data, statistics, examples
    
    # Status tracking
    status = db.Column(db.String(20), default='new')  # 'new', 'viewed', 'acted_on', 'dismissed'
    viewed_at = db.Column(db.DateTime, nullable=True)
    
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # Some insights may become stale
    
    def mark_as_viewed(self):
        """Mark insight as viewed."""
        if self.status == 'new':
            self.status = 'viewed'
            self.viewed_at = datetime.utcnow()
            db.session.commit()
    
    def __repr__(self):
        return f'<Insight {self.insight_type} - {self.title}>'


class VisionStatement(db.Model):
    """User's life vision and mission statement."""
    __tablename__ = 'vision_statements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Vision components
    vision_statement = db.Column(db.Text, nullable=False)  # "I see myself as..."
    mission_statement = db.Column(db.Text, nullable=True)  # "My purpose is to..."
    core_purpose = db.Column(db.Text, nullable=True)  # Why do you exist?
    legacy_intention = db.Column(db.Text, nullable=True)  # What do you want to be remembered for?
    
    # Reflection prompts responses
    life_themes = db.Column(db.JSON, nullable=True)  # Key themes that matter
    peak_experiences = db.Column(db.Text, nullable=True)  # When did you feel most alive?
    future_self_visualization = db.Column(db.Text, nullable=True)  # 10-year vision
    
    # Status and versioning
    version = db.Column(db.Integer, default=1)  # Allow vision evolution
    is_current = db.Column(db.Boolean, default=True)  # Current active vision
    confidence_level = db.Column(db.Integer, nullable=True)  # 1-10 how sure are you
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_reviewed = db.Column(db.DateTime, nullable=True)
    
    def mark_for_review(self):
        """Schedule vision for review (recommended every 6-12 months)."""
        from datetime import timedelta
        self.last_reviewed = datetime.utcnow()
        # Could set next_review_date = last_reviewed + 6 months
    
    def create_new_version(self):
        """Create a new version of the vision, archiving the current one."""
        self.is_current = False
        db.session.commit()
        # Caller should create new VisionStatement with version += 1
    
    def __repr__(self):
        return f'<VisionStatement v{self.version} - User {self.user_id}>'


class CoreValueAssessment(db.Model):
    """Values discovery assessment results and rankings."""
    __tablename__ = 'core_value_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Assessment methodology
    assessment_type = db.Column(db.String(50), default='card_sort')  # 'card_sort', 'ranking', 'story_based'
    
    # Core values (top 5-7 most important)
    top_values = db.Column(db.JSON, nullable=False)  # [{"value": "Freedom", "rank": 1, "definition": "..."}, ...]
    
    # Values exploration responses
    values_definition = db.Column(db.JSON, nullable=True)  # User's definition of each value
    values_stories = db.Column(db.JSON, nullable=True)  # Stories of when values were honored/violated
    conflicting_values = db.Column(db.JSON, nullable=True)  # Values that sometimes conflict
    
    # Values in action
    daily_expressions = db.Column(db.JSON, nullable=True)  # How values show up daily
    decision_framework = db.Column(db.Text, nullable=True)  # How to use values for decisions
    
    # Meta-reflection
    insights_gained = db.Column(db.Text, nullable=True)  # What did you learn?
    surprises = db.Column(db.Text, nullable=True)  # What was unexpected?
    alignment_assessment = db.Column(db.Integer, nullable=True)  # 1-10 how aligned is current life
    
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_current = db.Column(db.Boolean, default=True)
    
    def get_top_value_names(self):
        """Return list of top value names in rank order."""
        if not self.top_values:
            return []
        sorted_values = sorted(self.top_values, key=lambda x: x.get('rank', 999))
        return [v['value'] for v in sorted_values]
    
    def get_value_definition(self, value_name):
        """Get user's definition of a specific value."""
        if not self.top_values:
            return None
        for value_data in self.top_values:
            if value_data['value'] == value_name:
                return value_data.get('definition', '')
        return None
    
    def create_values_records(self):
        """Create/update Value records based on assessment results."""
        if not self.top_values:
            return
        
        # Create or update Value records for top values
        for i, value_data in enumerate(self.top_values, 1):
            # Check if Value record exists
            existing_value = Value.query.filter_by(
                user_id=self.user_id,
                name=value_data['value']
            ).first()
            
            if existing_value:
                # Update priority based on assessment rank
                existing_value.priority = value_data.get('rank', i)
                existing_value.description = value_data.get('definition', existing_value.description)
            else:
                # Create new Value record
                new_value = Value(
                    user_id=self.user_id,
                    name=value_data['value'],
                    description=value_data.get('definition', ''),
                    priority=value_data.get('rank', i)
                )
                db.session.add(new_value)
        
        db.session.commit()
    
    def __repr__(self):
        return f'<CoreValueAssessment User {self.user_id} - {len(self.top_values or [])} values>'