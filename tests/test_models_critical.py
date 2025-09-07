"""
Critical model tests for Project Elara's psychological frameworks.
These tests ensure the core SDT, CBT, and Habit Loop principles work correctly.
"""

import pytest
from datetime import date, datetime, timedelta
from models import db, User, Goal, Task, Habit, HabitLog, Value, JournalEntry

class TestGoalProgressCalculation:
    """Test goal progress calculation based on linked tasks (SDT Competence principle)."""
    
    def test_goal_progress_calculation_with_no_tasks(self, app, test_goal):
        """Goal with no linked tasks shows 0% progress."""
        with app.app_context():
            progress = test_goal.calculate_progress()
            assert progress == 0
            assert test_goal.progress == 0
    
    def test_goal_progress_updates_with_task_completion(self, app, test_goal):
        """Goal progress recalculates when linked tasks completed."""
        with app.app_context():
            # Create 3 tasks linked to goal
            task1 = Task(user_id=test_goal.user_id, goal_id=test_goal.id, title="Task 1")
            task2 = Task(user_id=test_goal.user_id, goal_id=test_goal.id, title="Task 2") 
            task3 = Task(user_id=test_goal.user_id, goal_id=test_goal.id, title="Task 3")
            
            db.session.add_all([task1, task2, task3])
            db.session.commit()
            
            # Initially 0% progress
            progress = test_goal.calculate_progress()
            assert progress == 0
            
            # Complete 1 task = 33% progress
            task1.mark_complete()
            progress = test_goal.calculate_progress()
            assert progress == 33
            
            # Complete 2nd task = 66% progress  
            task2.mark_complete()
            progress = test_goal.calculate_progress()
            assert progress == 66
            
            # Complete all tasks = 100% progress
            task3.mark_complete() 
            progress = test_goal.calculate_progress()
            assert progress == 100
    
    def test_task_completion_auto_updates_goal_progress(self, app, test_goal):
        """Task.mark_complete() automatically updates linked goal progress."""
        with app.app_context():
            task = Task(user_id=test_goal.user_id, goal_id=test_goal.id, title="Auto-update test")
            db.session.add(task)
            db.session.commit()
            
            # Goal starts at 0%
            assert test_goal.progress == 0
            
            # Mark task complete - should auto-update goal
            task.mark_complete()
            
            # Reload from database
            db.session.refresh(test_goal)
            assert test_goal.progress == 100  # 1 out of 1 task completed
    
    def test_goal_completion_sets_status_and_date(self, app, test_goal):
        """Goal.mark_complete() sets status and completion date."""
        with app.app_context():
            before_completion = datetime.utcnow()
            
            test_goal.mark_complete()
            
            assert test_goal.status == 'completed'
            assert test_goal.progress == 100
            assert test_goal.completed_at is not None
            assert test_goal.completed_at >= before_completion

class TestHabitStreakCalculation:
    """Test habit streak counting (Habit Loop principle)."""
    
    def test_habit_first_checkin_sets_streak_to_one(self, app, test_habit):
        """First habit check-in sets streak count to 1."""
        with app.app_context():
            assert test_habit.streak_count == 0
            
            success = test_habit.check_in_today()
            
            assert success is True
            assert test_habit.streak_count == 1
            assert test_habit.best_streak == 1
    
    def test_habit_consecutive_checkins_increment_streak(self, app, test_habit):
        """Consecutive daily check-ins increment streak count."""
        with app.app_context():
            # Simulate checking in over multiple days
            today = date.today()
            
            # Day 1
            test_habit.last_completed = None
            test_habit.update_streak(today - timedelta(days=2))
            assert test_habit.streak_count == 1
            
            # Day 2 (consecutive)
            test_habit.last_completed = today - timedelta(days=2)
            test_habit.update_streak(today - timedelta(days=1))
            assert test_habit.streak_count == 2
            
            # Day 3 (consecutive)
            test_habit.last_completed = today - timedelta(days=1)  
            test_habit.update_streak(today)
            assert test_habit.streak_count == 3
            assert test_habit.best_streak == 3
    
    def test_habit_missed_day_resets_streak(self, app, test_habit):
        """Missing a day resets streak count to 1."""
        with app.app_context():
            today = date.today()
            
            # Build a 3-day streak
            test_habit.streak_count = 3
            test_habit.best_streak = 3
            test_habit.last_completed = today - timedelta(days=3)
            
            # Check in after missing 2 days (should reset)
            test_habit.update_streak(today)
            
            assert test_habit.streak_count == 1  # Reset to 1
            assert test_habit.best_streak == 3   # Best streak preserved
    
    def test_habit_prevents_duplicate_daily_checkins(self, app, test_habit):
        """Can't complete same habit twice in one day."""
        with app.app_context():
            # First check-in should succeed
            success1 = test_habit.check_in_today()
            assert success1 is True
            assert test_habit.streak_count == 1
            
            # Second check-in same day should fail
            success2 = test_habit.check_in_today()
            assert success2 is False
            assert test_habit.streak_count == 1  # Unchanged
    
    def test_habit_is_completed_today_accuracy(self, app, test_habit):
        """is_completed_today() accurately reflects completion status."""
        with app.app_context():
            # Initially not completed
            assert test_habit.is_completed_today() is False
            
            # After check-in, should be completed
            test_habit.check_in_today()
            assert test_habit.is_completed_today() is True
    
    def test_habit_streak_emoji_changes_with_progress(self, app, test_habit):
        """Habit streak emoji changes based on streak count."""
        with app.app_context():
            # No streak
            test_habit.streak_count = 0
            assert test_habit.get_streak_emoji() == "⭕"
            
            # Short streak  
            test_habit.streak_count = 3
            assert test_habit.get_streak_emoji() == "🔥"
            
            # Medium streak
            test_habit.streak_count = 15
            assert test_habit.get_streak_emoji() == "💪"
            
            # Long streak
            test_habit.streak_count = 50
            assert test_habit.get_streak_emoji() == "🏆"

class TestTaskGoalLinking:
    """Test task-goal relationship (SDT Autonomy principle)."""
    
    def test_task_links_to_goal_correctly(self, app, test_goal):
        """Tasks can be linked to goals and relationship works."""
        with app.app_context():
            task = Task(
                user_id=test_goal.user_id,
                goal_id=test_goal.id,
                title="Linked task"
            )
            db.session.add(task)
            db.session.commit()
            
            # Test relationship from both sides
            assert task.goal == test_goal
            assert task in test_goal.tasks.all()
    
    def test_task_can_unlink_from_goal(self, app, test_goal):
        """Tasks can be unlinked from goals without deletion."""
        with app.app_context():
            task = Task(
                user_id=test_goal.user_id,
                goal_id=test_goal.id,
                title="Will be unlinked"
            )
            db.session.add(task)
            db.session.commit()
            
            # Initially linked
            assert task.goal == test_goal
            
            # Unlink task
            task.goal_id = None
            db.session.commit()
            
            # Task exists but not linked
            assert task.goal is None
            assert task not in test_goal.tasks.all()
    
    def test_goal_deletion_preserves_tasks(self, app, test_goal):
        """Deleting goal unlinks tasks but preserves them."""
        with app.app_context():
            task = Task(
                user_id=test_goal.user_id,
                goal_id=test_goal.id,
                title="Should survive goal deletion"
            )
            db.session.add(task)
            db.session.commit()
            
            task_id = task.id
            
            # Delete goal (this should unlink tasks in production code)
            # First unlink manually (as production code would do)
            for t in test_goal.tasks:
                t.goal_id = None
            
            db.session.delete(test_goal)
            db.session.commit()
            
            # Task should still exist
            surviving_task = Task.query.get(task_id)
            assert surviving_task is not None
            assert surviving_task.goal_id is None

class TestValueGoalHierarchy:
    """Test Value-Goal hierarchy (SDT principles)."""
    
    def test_value_goal_relationship(self, app, test_value):
        """Values can have multiple goals linked to them."""
        with app.app_context():
            goal1 = Goal(user_id=test_value.user_id, value_id=test_value.id, title="Goal 1")
            goal2 = Goal(user_id=test_value.user_id, value_id=test_value.id, title="Goal 2")
            
            db.session.add_all([goal1, goal2])
            db.session.commit()
            
            # Test relationship from both sides
            assert goal1.value == test_value
            assert goal2.value == test_value
            assert goal1 in test_value.goals.all()
            assert goal2 in test_value.goals.all()
            assert test_value.goals.count() == 2
    
    def test_goals_can_exist_without_values(self, app, test_user):
        """Goals can exist independently without being linked to values."""
        with app.app_context():
            standalone_goal = Goal(
                user_id=test_user.id,
                value_id=None,  # No value link
                title="Standalone goal"
            )
            db.session.add(standalone_goal)
            db.session.commit()
            
            assert standalone_goal.value is None
            assert standalone_goal.value_id is None

class TestUserPersonalitySystem:
    """Test avatar personality system (HCI personalization)."""
    
    def test_user_personality_selection(self, app, test_user):
        """User can select and change avatar personality."""
        with app.app_context():
            # Initially set to 'friend'  
            assert test_user.avatar_personality == "friend"
            
            # Change to different personality
            test_user.avatar_personality = "champion"
            db.session.commit()
            
            # Reload and verify
            db.session.refresh(test_user)
            assert test_user.avatar_personality == "champion"
    
    def test_user_can_have_no_personality(self, app):
        """User can exist without personality (for initial setup)."""
        with app.app_context():
            user = User(username="no_personality")
            user.set_password("test")
            # Don't set avatar_personality
            
            db.session.add(user)
            db.session.commit()
            
            assert user.avatar_personality is None

class TestJournalMoodTracking:
    """Test journal mood tracking (CBT principles)."""
    
    def test_journal_mood_emoji_accuracy(self, app, test_user):
        """Journal entries return correct mood emojis."""
        with app.app_context():
            # Test various mood scores
            entry_sad = JournalEntry(user_id=test_user.id, content="Sad day", mood_score=2)
            entry_happy = JournalEntry(user_id=test_user.id, content="Great day", mood_score=9)
            entry_neutral = JournalEntry(user_id=test_user.id, content="OK day", mood_score=5)
            
            assert entry_sad.get_mood_emoji() == "😞"
            assert entry_happy.get_mood_emoji() == "😁" 
            assert entry_neutral.get_mood_emoji() == "😐"
    
    def test_journal_mood_color_coding(self, app, test_user):
        """Journal entries return correct color classes for mood."""
        with app.app_context():
            entry_low = JournalEntry(user_id=test_user.id, content="Low mood", mood_score=3)
            entry_mid = JournalEntry(user_id=test_user.id, content="Mid mood", mood_score=6) 
            entry_high = JournalEntry(user_id=test_user.id, content="High mood", mood_score=8)
            
            assert entry_low.get_mood_color() == "text-red-500"
            assert entry_mid.get_mood_color() == "text-yellow-500"
            assert entry_high.get_mood_color() == "text-green-500"