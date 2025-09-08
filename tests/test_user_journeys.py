"""
Complete user journey integration tests.
Tests end-to-end workflows that users actually experience.
"""
import pytest
from models import db, User, Goal, Task, Habit, HabitLog, Value
from datetime import date, timedelta


class TestNewUserOnboarding:
    """Test complete new user onboarding experience."""
    
    def test_new_user_avatar_selection_to_first_goal(self, client, app):
        """New user can select avatar and create first goal."""
        with app.app_context():
            # Create new user
            user = User(username='newuser')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            # Login
            response = client.post('/auth/login', data={
                'username': 'newuser',
                'password': 'password123'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Should be able to access avatar selection
            response = client.get('/avatar/select')
            assert response.status_code == 200
            assert b'Choose Your AI Coach' in response.data
            
            # Select a personality
            response = client.post('/avatar/select', data={
                'personality': 'friend'
            }, follow_redirects=True)
            
            # Should redirect to dashboard
            assert b'Welcome back!' in response.data
            
            # Create first goal
            response = client.get('/goals/create')
            assert response.status_code == 200
            
            response = client.post('/goals/create', data={
                'title': 'My First Goal',
                'description': 'Learning to use Elara',
                'target_date': '2025-12-31',
                'status': 'active'
            }, follow_redirects=True)
            
            # Should be back on goals list with new goal
            assert b'My First Goal' in response.data
    
    def test_new_user_creates_first_habit_with_loop_structure(self, client, app):
        """New user creates first habit using Cue-Routine-Reward."""
        with app.app_context():
            user = User(username='habituser')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            # Login
            client.post('/auth/login', data={
                'username': 'habituser', 
                'password': 'password123'
            })
            
            # Create habit with full loop structure
            response = client.post('/habits/create', data={
                'name': 'Morning Meditation',
                'description': 'Daily mindfulness practice',
                'cue': 'After I wake up',
                'routine': 'I will meditate for 5 minutes',
                'reward': 'I will feel calm and centered',
                'frequency': 'daily'
            }, follow_redirects=True)
            
            # Should see habit in list or be redirected to habit view
            assert response.status_code == 200
            
            # Verify habit was created with proper structure
            habit = Habit.query.filter_by(name='Morning Meditation').first()
            assert habit is not None
            assert habit.cue == 'After I wake up'
            assert habit.routine == 'I will meditate for 5 minutes' 
            assert habit.reward == 'I will feel calm and centered'


class TestDailyWorkflow:
    """Test typical daily user workflow."""
    
    def test_morning_routine_checkin_tasks_journal(self, client, logged_in_user, test_goal, test_habit):
        """User morning routine: check habits, add tasks, write journal."""
        
        # Check in habit for today
        response = client.post(f'/api/habit-checkin/{test_habit.id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Add a quick task
        response = client.post('/api/quick-task', json={
            'title': 'Review project proposal',
            'energy': 'high'
        })
        assert response.status_code == 200
        
        # Write journal entry
        response = client.post('/journal', data={
            'content': 'Starting the day with meditation felt great. Ready to tackle my goals!',
            'mood_score': 8,
            'energy_level': 'high'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Starting the day' in response.data
    
    def test_task_completion_updates_goal_progress(self, client, logged_in_user, app):
        """Completing tasks updates goal progress automatically."""
        with app.app_context():
            # Create goal with tasks
            goal = Goal(user_id=logged_in_user.id, title='Complete Project')
            db.session.add(goal)
            db.session.commit()
            
            task1 = Task(user_id=logged_in_user.id, goal_id=goal.id, title='Task 1')
            task2 = Task(user_id=logged_in_user.id, goal_id=goal.id, title='Task 2')
            db.session.add_all([task1, task2])
            db.session.commit()
            
            # Initially 0% progress
            assert goal.calculate_progress() == 0
            
            # Complete first task
            response = client.post(f'/api/complete-task/{task1.id}')
            assert response.status_code == 200
            
            # Progress should update to 50%
            assert goal.calculate_progress() == 50
            
            # Complete second task  
            response = client.post(f'/api/complete-task/{task2.id}')
            assert response.status_code == 200
            
            # Progress should be 100%
            assert goal.calculate_progress() == 100


class TestWeeklyReviewWorkflow:
    """Test weekly review and reflection workflow."""
    
    def test_weekly_progress_data_accuracy(self, client, logged_in_user, app):
        """Weekly review shows accurate progress summaries."""
        with app.app_context():
            # Create some activity over past week
            goal = Goal(user_id=logged_in_user.id, title='Weekly Goal')
            db.session.add(goal)
            db.session.commit()
            
            # Add completed and pending tasks
            completed_task = Task(
                user_id=logged_in_user.id, 
                goal_id=goal.id,
                title='Completed Task',
                completed=True,
                completed_at=date.today() - timedelta(days=2)
            )
            pending_task = Task(
                user_id=logged_in_user.id,
                goal_id=goal.id, 
                title='Pending Task'
            )
            db.session.add_all([completed_task, pending_task])
            db.session.commit()
            
            # Get dashboard stats
            response = client.get('/api/dashboard-stats')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'tasks' in data
            assert data['tasks']['completed'] >= 1
            assert data['tasks']['total'] >= 2
    
    def test_habit_streak_milestone_recognition(self, client, logged_in_user, app, test_habit):
        """System recognizes and celebrates habit streak milestones."""
        with app.app_context():
            habit = test_habit
            
            # Simulate 7-day streak
            for i in range(7):
                past_date = date.today() - timedelta(days=i)
                log = HabitLog(habit_id=habit.id, completed_date=past_date)
                db.session.add(log)
            
            habit.streak_count = 7
            db.session.commit()
            
            # Check in for today (should be milestone)
            response = client.post(f'/api/habit-checkin/{habit.id}')
            data = response.get_json()
            
            # Should include streak information
            assert 'streak_count' in data
            assert data['streak_count'] >= 7


class TestGoalCompletionCelebration:
    """Test goal completion celebration flow."""
    
    def test_goal_completion_triggers_celebration(self, client, logged_in_user, app):
        """Completing final task of goal triggers celebration."""
        with app.app_context():
            # Create goal with one task
            goal = Goal(user_id=logged_in_user.id, title='Almost Complete Goal')
            db.session.add(goal)
            db.session.commit()
            
            final_task = Task(user_id=logged_in_user.id, goal_id=goal.id, title='Final Task')
            db.session.add(final_task)
            db.session.commit()
            
            # Complete the final task
            response = client.post(f'/api/complete-task/{final_task.id}')
            assert response.status_code == 200
            
            # Goal should now be 100% complete
            assert goal.calculate_progress() == 100
            
            # View goal details should show completion
            response = client.get(f'/goals/{goal.id}')
            assert response.status_code == 200
            assert b'100%' in response.data


class TestDataConsistencyAcrossSessions:
    """Test data consistency across multiple user sessions."""
    
    def test_habit_streaks_persist_across_logins(self, client, app):
        """Habit streaks are maintained across user sessions."""
        with app.app_context():
            # Create user and habit
            user = User(username='streakuser')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            habit = Habit(
                user_id=user.id,
                name='Persistent Habit',
                frequency='daily'
            )
            db.session.add(habit)
            db.session.commit()
            
            # First session: build streak
            client.post('/auth/login', data={
                'username': 'streakuser',
                'password': 'password123'
            })
            
            # Create streak logs
            for i in range(3):
                past_date = date.today() - timedelta(days=i)
                log = HabitLog(habit_id=habit.id, completed_date=past_date)
                db.session.add(log)
            
            habit.streak_count = 3
            db.session.commit()
            
            # Logout
            client.get('/auth/logout')
            
            # Second session: verify streak persists
            client.post('/auth/login', data={
                'username': 'streakuser',
                'password': 'password123'
            })
            
            response = client.get('/habits')
            assert response.status_code == 200
            assert b'3' in response.data  # Streak count should be visible
    
    def test_goal_progress_accuracy_after_task_modifications(self, client, logged_in_user, app):
        """Goal progress remains accurate after task additions/deletions."""
        with app.app_context():
            goal = Goal(user_id=logged_in_user.id, title='Dynamic Goal')
            db.session.add(goal)
            db.session.commit()
            
            # Add first task and complete it
            task1 = Task(user_id=logged_in_user.id, goal_id=goal.id, title='Task 1')
            db.session.add(task1)
            db.session.commit()
            
            task1.mark_complete()
            db.session.commit()
            
            # Should be 100% with 1 task
            assert goal.calculate_progress() == 100
            
            # Add second task
            task2 = Task(user_id=logged_in_user.id, goal_id=goal.id, title='Task 2')
            db.session.add(task2)
            db.session.commit()
            
            # Should now be 50% (1 of 2 completed)
            assert goal.calculate_progress() == 50
            
            # Complete second task
            task2.mark_complete()
            db.session.commit()
            
            # Should be back to 100%
            assert goal.calculate_progress() == 100


class TestErrorRecoveryScenarios:
    """Test system behavior in error scenarios."""
    
    def test_system_handles_corrupted_streak_data(self, client, logged_in_user, app, test_habit):
        """System recovers gracefully from corrupted habit streak data."""
        with app.app_context():
            habit = test_habit
            
            # Simulate corrupted data: streak count higher than logs
            habit.streak_count = 100
            db.session.commit()
            
            # System should handle this gracefully
            response = client.get('/habits')
            assert response.status_code == 200
            
            # Recalculating streak should fix corruption
            habit.update_streak(date.today())
            db.session.commit()
            
            # Streak should be corrected
            assert habit.streak_count <= 1  # Should be realistic now
    
    def test_system_handles_orphaned_tasks_gracefully(self, client, logged_in_user, app):
        """System handles tasks orphaned by deleted goals."""
        with app.app_context():
            goal = Goal(user_id=logged_in_user.id, title='To Be Deleted')
            db.session.add(goal)
            db.session.commit()
            
            task = Task(user_id=logged_in_user.id, goal_id=goal.id, title='Orphan Task')
            db.session.add(task)
            db.session.commit()
            
            # Delete goal
            db.session.delete(goal)
            db.session.commit()
            
            # Task should still exist but unlinked
            orphaned_task = Task.query.filter_by(title='Orphan Task').first()
            assert orphaned_task is not None
            assert orphaned_task.goal_id is None
            
            # Dashboard should still work
            response = client.get('/dashboard')
            assert response.status_code == 200


# Test fixtures  
@pytest.fixture
def test_goal(app, logged_in_user):
    """Create a test goal."""
    with app.app_context():
        goal = Goal(
            user_id=logged_in_user.id,
            title="Test Goal",
            description="A test goal for journey testing"
        )
        db.session.add(goal)
        db.session.commit()
        return goal


@pytest.fixture  
def test_habit(app, logged_in_user):
    """Create a test habit."""
    with app.app_context():
        habit = Habit(
            user_id=logged_in_user.id,
            name="Test Habit",
            description="A test habit for journey testing",
            cue="Test cue",
            routine="Test routine",
            reward="Test reward", 
            frequency="daily"
        )
        db.session.add(habit)
        db.session.commit()
        return habit


@pytest.fixture
def logged_in_user(client, test_user):
    """Log in the test user."""
    client.post('/auth/login', data={
        'username': test_user.username,
        'password': 'elara2024'
    })
    return test_user