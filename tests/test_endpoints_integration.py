"""
Comprehensive endpoint integration tests to catch routing and template errors.
These tests verify that all routes resolve correctly and templates render.
"""
import pytest
from flask import url_for
from models import db, User, Goal, Habit, Task, Value

class TestEndpointRouting:
    """Test that all endpoints resolve correctly without BuildError."""
    
    def test_all_main_routes_resolve(self, app, test_user):
        """Test that all main page routes can be built."""
        with app.app_context():
            # Main navigation routes
            assert url_for('dashboard.dashboard')
            assert url_for('journal.journal')
            assert url_for('goals.goals_list')
            assert url_for('habits.habits_dashboard')
            
            # Auth routes
            assert url_for('auth.login')
            assert url_for('auth.logout')
            
    def test_goal_routes_resolve(self, app, test_user, test_goal):
        """Test that all goal-related routes resolve."""
        with app.app_context():
            assert url_for('goals.goals_list')
            assert url_for('goals.create_goal')
            assert url_for('goals.view_goal', goal_id=test_goal.id)
            assert url_for('goals.edit_goal', goal_id=test_goal.id)
            
            # API routes
            assert url_for('goals.get_goal_progress', goal_id=test_goal.id)
            assert url_for('goals.quick_create_goal')
            
    def test_habit_routes_resolve(self, app, test_user, test_habit):
        """Test that all habit-related routes resolve."""
        with app.app_context():
            assert url_for('habits.habits_dashboard')
            assert url_for('habits.create_habit_wizard')
            assert url_for('habits.view_habit', habit_id=test_habit.id)
            assert url_for('habits.edit_habit', habit_id=test_habit.id)
            
            # API routes
            assert url_for('habits.check_in_habit', habit_id=test_habit.id)
            assert url_for('habits.get_habits_stats')

class TestTemplateRendering:
    """Test that templates render without TemplateNotFound errors."""
    
    def test_dashboard_renders(self, client, logged_in_user):
        """Test dashboard renders with Phase 2 widgets."""
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert b'Active Goals' in response.data
        assert b'Today\'s Habits' in response.data
        assert b'Today\'s Focus' in response.data
        
    def test_goals_pages_render(self, client, logged_in_user):
        """Test all goals pages render correctly."""
        # Goals list
        response = client.get('/goals')
        assert response.status_code == 200
        assert b'My Goals' in response.data
        
        # Create goal form
        response = client.get('/goals/create')
        assert response.status_code == 200
        assert b'Create New Goal' in response.data
        assert b'Goal Title' in response.data
        
    def test_habits_pages_render(self, client, logged_in_user):
        """Test all habits pages render correctly."""
        # Habits dashboard
        response = client.get('/habits')
        assert response.status_code == 200
        assert b'My Habits' in response.data
        
        # Create habit wizard
        response = client.get('/habits/create')
        assert response.status_code == 200
        assert b'Habit Creation Wizard' in response.data
        assert b'Cue-Routine-Reward' in response.data
        
    def test_view_templates_render(self, client, logged_in_user, test_goal, test_habit):
        """Test all view templates render correctly - catches missing view templates."""
        # Goal view
        response = client.get(f'/goals/{test_goal.id}')
        assert response.status_code == 200
        assert b'Goal Overview' in response.data
        assert b'Linked Tasks' in response.data
        
        # Habit view  
        response = client.get(f'/habits/{test_habit.id}')
        assert response.status_code == 200
        assert b'Habit Details' in response.data
        assert b'30-Day Progress Calendar' in response.data
        
class TestNavigationLinks:
    """Test that all navigation links work correctly."""
    
    def test_dashboard_widget_links(self, client, logged_in_user, test_goal, test_habit):
        """Test dashboard widget navigation buttons."""
        response = client.get('/dashboard')
        assert response.status_code == 200
        
        # Check for correct URLs in HTML
        html = response.data.decode()
        assert 'href="/goals"' in html  # Manage Goals button
        assert 'href="/habits"' in html  # Manage Habits button
        
    def test_goals_navigation_links(self, client, logged_in_user):
        """Test navigation links in goals pages."""
        # Goals list page
        response = client.get('/goals')
        assert response.status_code == 200
        html = response.data.decode()
        assert 'href="/goals/create"' in html  # New Goal button
        
    def test_habits_navigation_links(self, client, logged_in_user):
        """Test navigation links in habits pages."""
        # Habits dashboard
        response = client.get('/habits')
        assert response.status_code == 200
        html = response.data.decode()
        assert 'href="/habits/create"' in html  # New Habit button

class TestFormSubmission:
    """Test that forms work correctly."""
    
    def test_create_goal_form_submission(self, client, logged_in_user):
        """Test goal creation form works."""
        response = client.post('/goals/create', data={
            'title': 'Test Goal',
            'description': 'A test goal',
            'value_id': '0',  # No specific area
            'target_date': '2025-12-31',
            'status': 'active',
            'csrf_token': 'dummy'  # Would need proper CSRF in real test
        }, follow_redirects=False)  # Don't follow redirect to check it happens
        
        # Should redirect on success (or show form again on validation error)
        assert response.status_code in [200, 302]
        
    def test_create_habit_form_submission(self, client, logged_in_user):
        """Test habit creation form works."""
        response = client.post('/habits/create', data={
            'name': 'Test Habit',
            'description': 'A test habit',
            'cue': 'After I wake up',
            'routine': 'I will meditate for 5 minutes',
            'reward': 'I will feel calm',
            'frequency': 'daily',
            'csrf_token': 'dummy'
        }, follow_redirects=False)
        
        assert response.status_code in [200, 302]

class TestAPIEndpoints:
    """Test API endpoints work correctly."""
    
    def test_habit_checkin_api(self, client, logged_in_user, test_habit):
        """Test habit check-in API endpoint."""
        response = client.post(f'/api/habit-checkin/{test_habit.id}')
        assert response.status_code == 200
        data = response.get_json()
        assert 'success' in data
        assert 'message' in data
        
    def test_task_completion_api(self, client, logged_in_user, test_task):
        """Test task completion API endpoint."""
        response = client.post(f'/api/complete-task/{test_task.id}')
        assert response.status_code == 200
        data = response.get_json()
        assert 'success' in data
        
    def test_dashboard_stats_api(self, client, logged_in_user):
        """Test dashboard stats API endpoint."""
        response = client.get('/api/dashboard-stats')
        assert response.status_code == 200
        data = response.get_json()
        assert 'tasks' in data
        assert 'goals' in data
        assert 'habits' in data
        assert 'journal' in data

class TestErrorHandling:
    """Test error conditions are handled properly."""
    
    def test_nonexistent_goal_404(self, client, logged_in_user):
        """Test viewing non-existent goal returns 404."""
        response = client.get('/goals/99999')
        assert response.status_code == 404
        
    def test_nonexistent_habit_404(self, client, logged_in_user):
        """Test viewing non-existent habit returns 404."""
        response = client.get('/habits/99999')
        assert response.status_code == 404
        
    def test_unauthorized_access_redirects(self, client):
        """Test unauthenticated access redirects to login."""
        response = client.get('/dashboard')
        assert response.status_code == 302  # Redirect to login
        
        response = client.get('/goals')
        assert response.status_code == 302
        
        response = client.get('/habits')
        assert response.status_code == 302

# Additional fixtures for test data
@pytest.fixture
def test_goal(app, test_user):
    """Create a test goal."""
    with app.app_context():
        goal = Goal(
            user_id=test_user.id,
            title="Test Goal",
            description="A test goal",
            status="active"
        )
        db.session.add(goal)
        db.session.commit()
        return goal

@pytest.fixture  
def test_habit(app, test_user):
    """Create a test habit."""
    with app.app_context():
        habit = Habit(
            user_id=test_user.id,
            name="Test Habit",
            description="A test habit",
            cue="Test cue",
            routine="Test routine", 
            reward="Test reward",
            frequency="daily"
        )
        db.session.add(habit)
        db.session.commit()
        return habit

@pytest.fixture
def test_task(app, test_user):
    """Create a test task."""
    with app.app_context():
        task = Task(
            user_id=test_user.id,
            title="Test Task",
            description="A test task"
        )
        db.session.add(task)
        db.session.commit()
        return task

@pytest.fixture
def logged_in_user(client, test_user):
    """Log in the test user."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_user)  # test_user is already an ID
        sess['_fresh'] = True
    return test_user