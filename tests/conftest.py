import pytest
import tempfile
import os
import sys
from unittest.mock import MagicMock
from datetime import date, datetime, timedelta

# Mock external dependencies before importing app
sys.modules['google.generativeai'] = MagicMock()
sys.modules['openai'] = MagicMock()
sys.modules['markdown'] = MagicMock()

from app import create_app
from models import db, User, Goal, Task, Habit, HabitLog, Value


def refresh_object(model_class, object_id):
    """Helper to query a fresh object from the database within current session."""
    return model_class.query.get(object_id)

@pytest.fixture
def app():
    """Create and configure a test app instance."""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()
    
    # Create app with test configuration
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing
        "SECRET_KEY": "test-secret-key"
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Test client for making requests."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Test runner for CLI commands."""
    return app.test_cli_runner()

@pytest.fixture
def test_user(app):
    """Create a test user and return its ID."""
    with app.app_context():
        user = User(username="testuser")
        user.set_password("testpass")
        user.avatar_personality = "friend"
        user.onboarding_completed = True
        user.onboarding_step = 4
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    return user_id

@pytest.fixture
def test_value(app, test_user):
    """Create a test life area value and return its ID."""
    with app.app_context():
        value = Value(
            user_id=test_user,
            name="Health",
            description="Physical and mental wellbeing",
            priority=8
        )
        db.session.add(value)
        db.session.commit()
        value_id = value.id
    return value_id

@pytest.fixture
def test_goal(app, test_user, test_value):
    """Create a test goal linked to a value and return its ID."""
    with app.app_context():
        goal = Goal(
            user_id=test_user,
            value_id=test_value,
            title="Exercise 3x per week",
            description="Build consistent exercise habit",
            target_date=date.today() + timedelta(days=30),
            status='active'
        )
        db.session.add(goal)
        db.session.commit()
        goal_id = goal.id
    return goal_id

@pytest.fixture
def test_habit(app, test_user):
    """Create a test habit with proper cue-routine-reward structure and return its ID."""
    with app.app_context():
        habit = Habit(
            user_id=test_user,
            name="Morning Meditation",
            description="10 minutes of mindfulness",
            cue="After I wake up and brush my teeth",
            routine="I will meditate for 10 minutes using a meditation app",
            reward="I will feel calmer and more centered for the day",
            frequency="daily"
        )
        db.session.add(habit)
        db.session.commit()
        habit_id = habit.id
    return habit_id

@pytest.fixture
def logged_in_client(client, app):
    """Return a client with logged-in test user."""
    with app.app_context():
        # Create or get test user
        user = User.query.filter_by(username='testuser').first()
        if not user:
            user = User(username='testuser')
            user.set_password('testpass')
            user.avatar_personality = 'friend'
            user.onboarding_completed = True
            user.onboarding_step = 4
            db.session.add(user)
            db.session.commit()

        # Actually log in
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass'
        }, follow_redirects=True)

    return client

# Helper functions for tests to get fresh objects from IDs
def get_user(user_id):
    """Get a fresh User object by ID."""
    return User.query.get(user_id)

def get_value(value_id):
    """Get a fresh Value object by ID."""
    return Value.query.get(value_id)

def get_goal(goal_id):
    """Get a fresh Goal object by ID."""
    return Goal.query.get(goal_id)

def get_habit(habit_id):
    """Get a fresh Habit object by ID."""
    return Habit.query.get(habit_id)