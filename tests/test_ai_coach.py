"""Unit tests for AI Coach service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys

# Mock external dependencies before importing AICoach
sys.modules['google.generativeai'] = MagicMock()
sys.modules['openai'] = MagicMock()

from services.ai_coach import AICoach
from models import User, Task, Goal, Habit, JournalEntry, db


@pytest.fixture
def mock_ai_coach(app):
    """Create a mocked AICoach instance."""
    with app.app_context():
        with patch('services.ai_coach.AICoach._init_moonshot'):
            coach = AICoach()
            return coach


def test_generate_daily_dashboard_message_basic(app, test_user, mock_ai_coach):
    """Test basic dashboard message generation."""
    with app.app_context():
        # Mock the generate_response method
        with patch.object(mock_ai_coach, 'generate_response') as mock_generate:
            mock_generate.return_value = ("Good morning! Let's make today great!", 50)

            result = mock_ai_coach.generate_daily_dashboard_message(test_user.id)

            assert result is not None
            assert 'message' in result
            assert 'timestamp' in result
            assert 'personality' in result
            assert 'tokens_used' in result
            assert result['personality'] == 'friend'
            assert isinstance(result['timestamp'], datetime)


def test_generate_daily_dashboard_message_with_tasks(app, test_user, test_goal, mock_ai_coach):
    """Test dashboard message generation with tasks."""
    with app.app_context():
        # Create some tasks for today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        task1 = Task(
            user_id=test_user.id,
            goal_id=test_goal.id,
            title="Complete project",
            due_date=today
        )
        task2 = Task(
            user_id=test_user.id,
            goal_id=test_goal.id,
            title="Review docs",
            due_date=today,
            completed=True
        )
        db.session.add_all([task1, task2])
        db.session.commit()

        with patch.object(mock_ai_coach, 'generate_response') as mock_generate:
            mock_generate.return_value = ("You have 1 task pending today!", 45)

            result = mock_ai_coach.generate_daily_dashboard_message(test_user.id)

            assert result is not None
            assert 'message' in result
            # Check that generate_response was called with context about tasks
            call_args = mock_generate.call_args
            assert 'task' in call_args[0][1].lower()


def test_generate_daily_dashboard_message_fallback(app, test_user, mock_ai_coach):
    """Test fallback when AI generation fails."""
    with app.app_context():
        with patch.object(mock_ai_coach, 'generate_response') as mock_generate:
            # Simulate API failure
            mock_generate.side_effect = Exception("API Error")

            result = mock_ai_coach.generate_daily_dashboard_message(test_user.id)

            assert result is not None
            assert 'message' in result
            assert len(result['message']) > 0
            assert result['tokens_used'] == 0


def test_generate_daily_dashboard_message_nonexistent_user(app, mock_ai_coach):
    """Test with nonexistent user."""
    with app.app_context():
        result = mock_ai_coach.generate_daily_dashboard_message(99999)

        assert result is not None
        assert result['message'] == "Welcome back! Let's make today count."
        assert result['personality'] == 'friend'


def test_generate_daily_dashboard_message_response_length(app, test_user, mock_ai_coach):
    """Test that response is reasonably short."""
    with app.app_context():
        with patch.object(mock_ai_coach, 'generate_response') as mock_generate:
            # Return a realistic message
            mock_generate.return_value = (
                "Good morning! You have 3 tasks today. Your meditation habit is at 5 days. "
                "Ready to keep that streak going?",
                60
            )

            result = mock_ai_coach.generate_daily_dashboard_message(test_user.id)

            # Message should be less than 200 words
            word_count = len(result['message'].split())
            assert word_count < 200


def test_generate_daily_dashboard_message_with_habits(app, test_user, test_habit, mock_ai_coach):
    """Test dashboard message with habit streaks."""
    with app.app_context():
        # Update habit streak
        habit = Habit.query.get(test_habit.id)
        habit.streak_count = 7
        db.session.commit()

        with patch.object(mock_ai_coach, 'generate_response') as mock_generate:
            mock_generate.return_value = ("Your Morning Meditation habit has a 7-day streak!", 40)

            result = mock_ai_coach.generate_daily_dashboard_message(test_user.id)

            assert result is not None
            call_args = mock_generate.call_args
            prompt = call_args[0][1]
            # Check that streak info is in the context
            assert '7-day' in prompt or 'streak' in prompt.lower()


def test_generate_daily_dashboard_message_time_of_day(app, test_user, mock_ai_coach):
    """Test that time of day affects greeting."""
    with app.app_context():
        with patch.object(mock_ai_coach, 'generate_response') as mock_generate:
            with patch('services.ai_coach.datetime') as mock_datetime:
                # Mock morning time (10 AM)
                mock_datetime.now.return_value = datetime(2024, 1, 1, 10, 0)
                mock_datetime.utcnow = datetime.utcnow
                mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

                mock_generate.return_value = ("Good morning!", 20)

                result = mock_ai_coach.generate_daily_dashboard_message(test_user.id)

                call_args = mock_generate.call_args
                prompt = call_args[0][1]
                assert 'Good morning' in prompt


def test_generate_daily_dashboard_message_with_journal(app, test_user, mock_ai_coach):
    """Test dashboard message with recent journal activity."""
    with app.app_context():
        # Create a recent journal entry
        entry = JournalEntry(
            user_id=test_user.id,
            content="Feeling great today!",
            mood_score=8,
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        db.session.add(entry)
        db.session.commit()

        with patch.object(mock_ai_coach, 'generate_response') as mock_generate:
            mock_generate.return_value = ("You journaled yesterday - great habit!", 35)

            result = mock_ai_coach.generate_daily_dashboard_message(test_user.id)

            assert result is not None
            call_args = mock_generate.call_args
            prompt = call_args[0][1]
            assert 'journal' in prompt.lower()
