"""
Critical route tests for Project Elara's API endpoints.
These tests ensure the web interface works correctly with the psychological models.
"""

import pytest
import json
from datetime import date, datetime, timedelta
from models import db, User, Goal, Task, Habit, HabitLog

class TestDashboardRoutes:
    """Test dashboard functionality and personality integration."""
    
    def test_dashboard_redirects_without_personality(self, client, app):
        """Dashboard redirects to avatar selection if no personality set."""
        with app.app_context():
            # Create user without personality
            user = User(username="no_avatar")
            user.set_password("test")
            # Don't set avatar_personality
            db.session.add(user)
            db.session.commit()
            
            # Login
            client.post('/auth/login', data={
                'username': 'no_avatar',
                'password': 'test'
            })
            
            # Dashboard should redirect
            response = client.get('/dashboard')
            assert response.status_code == 302
            assert '/avatar/select' in response.location
    
    def test_dashboard_loads_with_personality(self, client, app, test_user):
        """Dashboard loads successfully when user has personality."""
        with app.app_context():
            # Login as test user (has personality = 'friend')
            client.post('/auth/login', data={
                'username': 'testuser', 
                'password': 'testpass'
            })
            
            response = client.get('/dashboard')
            assert response.status_code == 200
            assert b'Welcome back' in response.data  # Check for welcome message

class TestGoalAPI:
    """Test goal management API endpoints."""
    
    def test_goal_progress_api_returns_accurate_data(self, client, app, test_user, test_goal):
        """Goal progress API returns correct calculation."""
        with app.app_context():
            # Login
            client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            })
            
            # Create tasks for the goal
            task1 = Task(user_id=test_user.id, goal_id=test_goal.id, title="Task 1")
            task2 = Task(user_id=test_user.id, goal_id=test_goal.id, title="Task 2", completed=True)
            db.session.add_all([task1, task2])
            db.session.commit()
            
            # Call API
            response = client.get(f'/goals/api/goals/{test_goal.id}/progress')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['progress'] == 50  # 1 out of 2 tasks completed
            assert data['total_tasks'] == 2
            assert data['completed_tasks'] == 1
    
    def test_quick_goal_creation_api(self, client, app, test_user):
        """Quick goal creation API works correctly."""
        with app.app_context():
            # Login
            client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'  
            })
            
            # Create goal via API
            response = client.post('/goals/api/goals/quick-create', 
                json={
                    'title': 'API Test Goal',
                    'description': 'Created via API',
                    'target_date': (date.today() + timedelta(days=30)).isoformat()
                },
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'API Test Goal' in data['message']
            
            # Verify goal was created
            goal = Goal.query.filter_by(title='API Test Goal').first()
            assert goal is not None
            assert goal.user_id == test_user.id

class TestHabitAPI:
    """Test habit tracking API endpoints."""
    
    def test_habit_checkin_api_updates_streak(self, client, app, test_user, test_habit):
        """Habit check-in API correctly updates streak count."""
        with app.app_context():
            # Login
            client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            })
            
            # Initial streak should be 0
            assert test_habit.streak_count == 0
            
            # Check in via API
            response = client.post(f'/habits/api/habits/{test_habit.id}/checkin')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['streak_count'] == 1
            assert 'streak_emoji' in data
            
            # Verify database was updated
            db.session.refresh(test_habit)
            assert test_habit.streak_count == 1
    
    def test_habit_checkin_prevents_duplicates(self, client, app, test_user, test_habit):
        """Habit check-in API prevents duplicate completions."""
        with app.app_context():
            # Login
            client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            })
            
            # First check-in should succeed
            response1 = client.post(f'/habits/api/habits/{test_habit.id}/checkin')
            assert response1.status_code == 200
            data1 = json.loads(response1.data)
            assert data1['success'] is True
            
            # Second check-in should fail
            response2 = client.post(f'/habits/api/habits/{test_habit.id}/checkin')
            assert response2.status_code == 200
            data2 = json.loads(response2.data)
            assert data2['success'] is False
            assert 'already completed' in data2['message']
    
    def test_habit_template_creation(self, client, app, test_user):
        """Habit creation from template works correctly."""
        with app.app_context():
            # Login
            client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            })
            
            template_data = {
                'name': 'Morning Exercise',
                'cue': 'After I wake up at 7 AM',
                'routine': 'I will do 20 minutes of exercise',
                'reward': 'I will feel energized for the day'
            }
            
            response = client.post('/habits/api/habits/create-from-template',
                json={'template': template_data},
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify habit was created with proper structure
            habit = Habit.query.filter_by(name='Morning Exercise').first()
            assert habit is not None
            assert habit.cue == template_data['cue']
            assert habit.routine == template_data['routine'] 
            assert habit.reward == template_data['reward']

class TestTaskAPI:
    """Test task management API endpoints."""
    
    def test_task_completion_updates_goal(self, client, app, test_user, test_goal):
        """Task completion API updates linked goal progress."""
        with app.app_context():
            # Login
            client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            })
            
            # Create task linked to goal
            task = Task(user_id=test_user.id, goal_id=test_goal.id, title="API Test Task")
            db.session.add(task)
            db.session.commit()
            
            # Goal should start at 0% progress
            assert test_goal.progress == 0
            
            # Complete task via API
            response = client.post(f'/api/complete-task/{task.id}')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify goal progress was updated
            db.session.refresh(test_goal)
            assert test_goal.progress == 100  # 1 out of 1 task completed
    
    def test_quick_task_creation(self, client, app, test_user):
        """Quick task creation from dashboard works."""
        with app.app_context():
            # Login
            client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            })
            
            response = client.post('/api/quick-task',
                json={
                    'title': 'Quick API Task',
                    'energy': 'high'
                },
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'Quick API Task' in data['message']
            
            # Verify task was created
            task = Task.query.filter_by(title='Quick API Task').first()
            assert task is not None
            assert task.energy_required == 'high'

class TestCalendarAPI:
    """Test calendar functionality."""
    
    def test_calendar_task_creation(self, client, app, test_user):
        """Calendar task creation API works correctly."""
        with app.app_context():
            # Login
            client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            })
            
            target_date = (date.today() + timedelta(days=5)).isoformat()
            
            response = client.post('/calendar/api/calendar/task/create',
                json={
                    'title': 'Calendar Task',
                    'due_date': target_date,
                    'energy_level': 'low'
                },
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify task was created with correct date
            task = Task.query.filter_by(title='Calendar Task').first()
            assert task is not None
            assert task.due_date.isoformat() == target_date
            assert task.energy_required == 'low'
    
    def test_task_date_moving(self, client, app, test_user):
        """Task date moving API works correctly."""
        with app.app_context():
            # Login
            client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            })
            
            # Create task
            original_date = date.today()
            task = Task(user_id=test_user.id, title="Movable Task", due_date=original_date)
            db.session.add(task)
            db.session.commit()
            
            # Move to new date
            new_date = (date.today() + timedelta(days=3)).isoformat()
            response = client.post(f'/calendar/api/calendar/task/{task.id}/move',
                json={'new_date': new_date},
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['new_date'] == new_date
            
            # Verify task date was updated
            db.session.refresh(task)
            assert task.due_date.isoformat() == new_date

class TestAvatarAPI:
    """Test avatar personality system."""
    
    def test_personality_message_api(self, client, app, test_user):
        """Personality message API returns context-appropriate messages."""
        with app.app_context():
            # Login 
            client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            })
            
            # Test different contexts
            contexts = ['goal_created', 'habit_streak', 'task_completed', 'encouragement']
            
            for context in contexts:
                response = client.get(f'/avatar/api/avatar/message/{context}')
                assert response.status_code == 200
                
                data = json.loads(response.data)
                assert data['success'] is True
                assert 'message' in data
                assert data['personality'] == 'friend'  # test_user has 'friend' personality
                assert len(data['message']) > 0  # Should have actual message content
    
    def test_personality_preview(self, client, app, test_user):
        """Personality preview API works without changing user's personality."""
        with app.app_context():
            # Login
            client.post('/auth/login', data={
                'username': 'testuser', 
                'password': 'testpass'
            })
            
            # Preview champion personality
            response = client.get('/avatar/preview/champion')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['personality']['name'] == 'The Champion'
            assert 'sample_interaction' in data
            
            # Verify user's personality didn't change
            assert test_user.avatar_personality == 'friend'  # Still original

class TestAuthenticationIntegration:
    """Test authentication integration with new features."""
    
    def test_unauthenticated_api_access_denied(self, client, app):
        """API endpoints require authentication."""
        endpoints_to_test = [
            '/api/complete-task/1',
            '/api/quick-task',
            '/habits/api/habits/1/checkin',
            '/goals/api/goals/1/progress',
            '/avatar/api/avatar/message/test'
        ]
        
        for endpoint in endpoints_to_test:
            response = client.post(endpoint) if 'POST' in ['POST'] else client.get(endpoint)
            # Should redirect to login or return 401/403
            assert response.status_code in [302, 401, 403]
    
    def test_user_data_isolation(self, client, app):
        """Users can only access their own data via API."""
        with app.app_context():
            # Create two users
            user1 = User(username="user1")
            user1.set_password("pass1")
            user1.avatar_personality = "friend"
            
            user2 = User(username="user2") 
            user2.set_password("pass2")
            user2.avatar_personality = "sage"
            
            db.session.add_all([user1, user2])
            db.session.commit()
            
            # Create habit for user2
            habit = Habit(
                user_id=user2.id,
                name="User2's Habit",
                cue="test", routine="test", reward="test"
            )
            db.session.add(habit)
            db.session.commit()
            
            # Login as user1
            client.post('/auth/login', data={
                'username': 'user1',
                'password': 'pass1'
            })
            
            # Try to access user2's habit
            response = client.post(f'/habits/api/habits/{habit.id}/checkin')
            assert response.status_code == 404  # Should not find habit for different user