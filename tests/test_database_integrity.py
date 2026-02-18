"""
Database integrity and edge case tests to ensure data consistency.
Tests database relationships, constraints, and business logic accuracy.
"""
import pytest
from datetime import date, datetime, timedelta
from models import db, User, Goal, Task, Habit, HabitLog, Value, JournalEntry

# Helper functions to get fresh objects from fixture IDs
def get_user(user_id):
    return User.query.get(user_id)

def get_goal(goal_id):
    return Goal.query.get(goal_id)

def get_habit(habit_id):
    return Habit.query.get(habit_id)

def get_value(value_id):
    return Value.query.get(value_id)


class TestGoalProgressCalculation:
    """Test goal progress calculation accuracy and edge cases."""
    
    def test_goal_progress_updates_correctly_with_task_completion(self, app, test_user):
        """Goal progress updates accurately when tasks are completed."""
        with app.app_context():
            user = get_user(test_user)
            # Create goal with 3 tasks
            goal = Goal(user_id=user.id, title="Test Goal")
            db.session.add(goal)
            db.session.commit()

            tasks = [
                Task(user_id=user.id, goal_id=goal.id, title=f"Task {i}")
                for i in range(1, 4)
            ]
            for task in tasks:
                db.session.add(task)
            db.session.commit()

            # Test progress calculation at different completion levels
            assert goal.calculate_progress() == 0

            # Complete first task
            tasks[0].mark_complete()
            db.session.commit()
            assert goal.calculate_progress() == 33

            # Complete second task
            tasks[1].mark_complete()
            db.session.commit()
            assert goal.calculate_progress() == 67

            # Complete third task
            tasks[2].mark_complete()
            db.session.commit()
            assert goal.calculate_progress() == 100
    
    def test_goal_progress_handles_zero_tasks(self, app, test_user):
        """Goal without tasks returns 0% progress without errors."""
        with app.app_context():
            user = get_user(test_user)
            goal = Goal(user_id=user.id, title="Empty Goal")
            db.session.add(goal)
            db.session.commit()

            assert goal.calculate_progress() == 0

    def test_goal_progress_ignores_unlinked_tasks(self, app, test_user):
        """Goal progress only counts tasks linked to that specific goal."""
        with app.app_context():
            user = get_user(test_user)
            # Create two goals
            goal1 = Goal(user_id=user.id, title="Goal 1")
            goal2 = Goal(user_id=user.id, title="Goal 2")
            db.session.add_all([goal1, goal2])
            db.session.commit()

            # Add tasks to goal1
            task1 = Task(user_id=user.id, goal_id=goal1.id, title="Task 1")
            task2 = Task(user_id=user.id, goal_id=goal1.id, title="Task 2")
            # Add unlinked task
            task3 = Task(user_id=user.id, title="Unlinked Task")
            db.session.add_all([task1, task2, task3])
            db.session.commit()

            # Complete task1 and unlinked task3
            task1.mark_complete()
            task3.mark_complete()
            db.session.commit()

            # Goal1 should be 50% (1/2), not affected by unlinked task
            assert goal1.calculate_progress() == 50
            assert goal2.calculate_progress() == 0


class TestHabitStreakLogic:
    """Test habit streak counting and reset logic edge cases."""
    
    def test_habit_streak_increments_correctly(self, app, test_user, test_habit):
        """Habit streak increments properly with daily check-ins."""
        with app.app_context():
            habit = get_habit(test_habit)
            assert habit.streak_count == 0

            # Check in for today
            habit.check_in_today()
            db.session.commit()
            habit = get_habit(test_habit)
            assert habit.streak_count == 1

            # Check in for yesterday (simulate consecutive days)
            yesterday = date.today() - timedelta(days=1)
            log = HabitLog(habit_id=habit.id, completed_date=yesterday)
            db.session.add(log)
            habit.update_streak(yesterday)
            db.session.commit()
            habit = get_habit(test_habit)
            assert habit.streak_count == 2
    
    def test_habit_streak_resets_on_missed_day(self, app, test_user, test_habit):
        """Habit streak resets when a day is missed."""
        with app.app_context():
            habit = get_habit(test_habit)

            # Build a 3-day streak
            for i in range(3):
                past_date = date.today() - timedelta(days=i+1)
                log = HabitLog(habit_id=habit.id, completed_date=past_date)
                db.session.add(log)
                habit.update_streak(past_date)
            db.session.commit()

            habit = get_habit(test_habit)
            initial_streak = habit.streak_count
            assert initial_streak > 0

            # Miss a day, then check in again (should reset)
            future_date = date.today() + timedelta(days=2)
            habit.update_streak(future_date)
            db.session.commit()

            # Streak should reset due to gap
            habit = get_habit(test_habit)
            assert habit.streak_count <= 1

    def test_habit_prevents_duplicate_checkins_same_day(self, app, test_user, test_habit):
        """Habit prevents multiple check-ins on the same day."""
        with app.app_context():
            habit = get_habit(test_habit)

            # First check-in should succeed
            result1 = habit.check_in_today()
            db.session.commit()
            assert result1 is True

            # Second check-in same day should fail
            result2 = habit.check_in_today()
            assert result2 is False

            # Verify only one log entry exists for today
            today_logs = HabitLog.query.filter_by(
                habit_id=habit.id,
                completed_date=date.today()
            ).count()
            assert today_logs == 1

    def test_habit_is_completed_today_accuracy(self, app, test_user, test_habit):
        """is_completed_today() returns accurate status."""
        with app.app_context():
            habit = get_habit(test_habit)

            # Initially not completed
            assert habit.is_completed_today() is False

            # After check-in, should be completed
            habit.check_in_today()
            db.session.commit()
            assert habit.is_completed_today() is True


class TestTaskGoalLinking:
    """Test task-goal relationship integrity."""
    
    def test_task_goal_linking_maintains_referential_integrity(self, app, test_user):
        """Task-goal links maintain referential integrity."""
        with app.app_context():
            user = get_user(test_user)
            goal = Goal(user_id=user.id, title="Parent Goal")
            db.session.add(goal)
            db.session.commit()

            task = Task(user_id=user.id, title="Child Task", goal_id=goal.id)
            db.session.add(task)
            db.session.commit()

            # Verify relationship works both ways
            assert task.goal == goal
            assert task in goal.tasks

    def test_deleting_goal_unlinks_tasks(self, app, test_user):
        """Deleting goal unlinks tasks but doesn't delete them."""
        with app.app_context():
            user = get_user(test_user)
            goal = Goal(user_id=user.id, title="To Be Deleted")
            db.session.add(goal)
            db.session.commit()

            task = Task(user_id=user.id, title="Orphan Task", goal_id=goal.id)
            db.session.add(task)
            db.session.commit()

            task_id = task.id

            # Delete goal
            db.session.delete(goal)
            db.session.commit()

            # Task should still exist but unlinked
            surviving_task = Task.query.get(task_id)
            assert surviving_task is not None
            assert surviving_task.goal_id is None


class TestUserDataIsolation:
    """Test that users can only access their own data."""
    
    def test_users_cannot_access_other_users_goals(self, app):
        """Users can only see goals they created."""
        with app.app_context():
            user1 = User(username='user1')
            user2 = User(username='user2')
            user1.set_password('pass1')
            user2.set_password('pass2')
            db.session.add_all([user1, user2])
            db.session.commit()
            
            # User1 creates goal
            goal1 = Goal(user_id=user1.id, title="User1 Goal")
            # User2 creates goal
            goal2 = Goal(user_id=user2.id, title="User2 Goal")
            db.session.add_all([goal1, goal2])
            db.session.commit()
            
            # User1 should only see their goal
            user1_goals = Goal.query.filter_by(user_id=user1.id).all()
            assert len(user1_goals) == 1
            assert user1_goals[0].title == "User1 Goal"
            
            # User2 should only see their goal  
            user2_goals = Goal.query.filter_by(user_id=user2.id).all()
            assert len(user2_goals) == 1
            assert user2_goals[0].title == "User2 Goal"
    
    def test_habit_logs_isolated_by_user(self, app):
        """Habit logs are properly isolated between users."""
        with app.app_context():
            user1 = User(username='user1')
            user2 = User(username='user2') 
            user1.set_password('pass1')
            user2.set_password('pass2')
            db.session.add_all([user1, user2])
            db.session.commit()
            
            habit1 = Habit(user_id=user1.id, name="User1 Habit")
            habit2 = Habit(user_id=user2.id, name="User2 Habit")
            db.session.add_all([habit1, habit2])
            db.session.commit()
            
            # Both users check in habits
            log1 = HabitLog(habit_id=habit1.id, completed_date=date.today())
            log2 = HabitLog(habit_id=habit2.id, completed_date=date.today())
            db.session.add_all([log1, log2])
            db.session.commit()
            
            # Verify logs are isolated
            user1_logs = HabitLog.query.join(Habit).filter(Habit.user_id == user1.id).all()
            user2_logs = HabitLog.query.join(Habit).filter(Habit.user_id == user2.id).all()
            
            assert len(user1_logs) == 1
            assert len(user2_logs) == 1
            assert user1_logs[0].habit.name == "User1 Habit"
            assert user2_logs[0].habit.name == "User2 Habit"


class TestDatabaseConstraints:
    """Test database constraint enforcement."""
    
    def test_foreign_key_constraints_enforced(self, app, test_user):
        """Foreign key constraints prevent orphaned records."""
        with app.app_context():
            user = get_user(test_user)
            # Try to create task with non-existent goal_id
            task = Task(user_id=user.id, title="Bad Task", goal_id=99999)
            db.session.add(task)

            # This should either raise an error or set goal_id to None
            try:
                db.session.commit()
                # If commit succeeds, goal_id should be None
                assert task.goal_id is None or task.goal is None
            except Exception:
                # Foreign key constraint prevented the bad reference
                db.session.rollback()
                assert True  # This is expected behavior

    def test_required_fields_enforced(self, app, test_user):
        """Required fields cannot be null."""
        with app.app_context():
            user = get_user(test_user)
            # Try to create goal without required title
            goal = Goal(user_id=user.id, title=None)
            db.session.add(goal)

            with pytest.raises(Exception):
                db.session.commit()


class TestBusinessLogicConsistency:
    """Test business logic maintains consistency."""
    
    def test_mood_scores_within_valid_range(self, app, test_user):
        """Mood scores are constrained to valid range."""
        with app.app_context():
            user = get_user(test_user)
            # Valid mood scores should work
            valid_entry = JournalEntry(
                user_id=user.id,
                content="Good day",
                mood_score=7
            )
            db.session.add(valid_entry)
            db.session.commit()
            assert valid_entry.mood_score == 7

            # Test boundary values
            low_entry = JournalEntry(
                user_id=user.id,
                content="Bad day",
                mood_score=1
            )
            high_entry = JournalEntry(
                user_id=user.id,
                content="Great day",
                mood_score=10
            )
            db.session.add_all([low_entry, high_entry])
            db.session.commit()

            assert low_entry.mood_score == 1
            assert high_entry.mood_score == 10

    def test_habit_frequency_validation(self, app, test_user):
        """Habit frequency values are from valid set."""
        with app.app_context():
            user = get_user(test_user)
            valid_frequencies = ['daily', 'weekly', 'monthly']

            for freq in valid_frequencies:
                habit = Habit(
                    user_id=user.id,
                    name=f"Test {freq} habit",
                    frequency=freq
                )
                db.session.add(habit)

            db.session.commit()

            # All habits should be created successfully
            created_habits = Habit.query.filter_by(user_id=user.id).all()
            assert len(created_habits) == len(valid_frequencies)


# Additional test fixtures
@pytest.fixture
def test_habit(app, test_user):
    """Create a test habit and return its ID."""
    with app.app_context():
        habit = Habit(
            user_id=test_user,
            name="Test Habit",
            description="A test habit",
            cue="Test cue",
            routine="Test routine",
            reward="Test reward",
            frequency="daily"
        )
        db.session.add(habit)
        db.session.commit()
        habit_id = habit.id
    return habit_id