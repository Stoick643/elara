import pytest
import tempfile
import os
import sys
from unittest.mock import MagicMock
from datetime import date, datetime, timedelta
from sqlalchemy.orm import make_transient

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
    """Create a test user."""
    with app.app_context():
        user = User(username="testuser")
        user.set_password("testpass")
        user.avatar_personality = "friend"
        db.session.add(user)
        db.session.commit()
        # Make transient so tests can reattach to their sessions
        user_id = user.id
        db.session.expunge(user)
        make_transient(user)
        user.id = user_id  # Restore ID after making transient
        return user

@pytest.fixture
def test_value(app, test_user):
    """Create a test life area value."""
    with app.app_context():
        value = Value(
            user_id=test_user.id,
            name="Health",
            description="Physical and mental wellbeing",
            priority=8
        )
        db.session.add(value)
        db.session.commit()
        # Make transient so tests can reattach to their sessions
        value_id = value.id
        db.session.expunge(value)
        make_transient(value)
        value.id = value_id  # Restore ID after making transient
        return value

@pytest.fixture
def test_goal(app, test_user, test_value):
    """Create a test goal linked to a value."""
    with app.app_context():
        goal = Goal(
            user_id=test_user.id,
            value_id=test_value.id,
            title="Exercise 3x per week",
            description="Build consistent exercise habit",
            target_date=date.today() + timedelta(days=30),
            status='active'
        )
        db.session.add(goal)
        db.session.commit()
        # Make transient so tests can reattach to their sessions
        goal_id = goal.id
        db.session.expunge(goal)
        make_transient(goal)
        goal.id = goal_id  # Restore ID after making transient
        return goal

@pytest.fixture
def test_habit(app, test_user):
    """Create a test habit with proper cue-routine-reward structure."""
    with app.app_context():
        habit = Habit(
            user_id=test_user.id,
            name="Morning Meditation",
            description="10 minutes of mindfulness",
            cue="After I wake up and brush my teeth",
            routine="I will meditate for 10 minutes using a meditation app",
            reward="I will feel calmer and more centered for the day",
            frequency="daily"
        )
        db.session.add(habit)
        db.session.commit()
        # Make transient so tests can reattach to their sessions
        habit_id = habit.id
        db.session.expunge(habit)
        make_transient(habit)
        habit.id = habit_id  # Restore ID after making transient
        return habit