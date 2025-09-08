"""
Comprehensive endpoint completeness tests to prevent routing and template errors.
These tests verify that all routes resolve correctly and templates exist.
"""
import pytest
from flask import url_for
from bs4 import BeautifulSoup
import re


class TestEndpointResolution:
    """Test that all endpoints resolve correctly without BuildError."""
    
    def test_all_main_navigation_links_resolve(self, app):
        """Every navigation link builds valid URL without BuildError."""
        with app.app_context():
            # Test main navigation endpoints
            navigation_endpoints = [
                'dashboard.dashboard',
                'journal.journal', 
                'goals.goals_list',
                'habits.habits_dashboard',
                'calendar.calendar_view',
                'avatar.select_personality',
                'auth.logout'
            ]
            
            for endpoint in navigation_endpoints:
                try:
                    url = url_for(endpoint)
                    assert url is not None
                    assert url.startswith('/')
                except Exception as e:
                    pytest.fail(f"Navigation endpoint '{endpoint}' failed to resolve: {e}")
    
    def test_all_form_action_urls_resolve(self, app, test_user):
        """Every form action URL resolves correctly."""
        with app.app_context():
            form_endpoints = [
                ('goals.create_goal', {}),
                ('habits.create_habit_wizard', {}),
                ('journal.journal', {}),
                ('avatar.select_personality', {}),
                ('goals.edit_goal', {'goal_id': 1}),
                ('habits.edit_habit', {'habit_id': 1}),
                ('goals.view_goal', {'goal_id': 1}),
                ('habits.view_habit', {'habit_id': 1})
            ]
            
            for endpoint, kwargs in form_endpoints:
                try:
                    url = url_for(endpoint, **kwargs)
                    assert url is not None
                    assert url.startswith('/')
                except Exception as e:
                    pytest.fail(f"Form endpoint '{endpoint}' with args {kwargs} failed: {e}")
    
    def test_all_api_endpoints_resolve(self, app):
        """Every AJAX call target endpoint resolves."""
        with app.app_context():
            api_endpoints = [
                ('dashboard.quick_add_task', {}),
                ('dashboard.quick_mood', {}),
                ('dashboard.complete_task', {'task_id': 1}),
                ('dashboard.habit_checkin_dashboard', {'habit_id': 1}),
                ('dashboard.get_dashboard_stats', {}),
                ('goals.get_goal_progress', {'goal_id': 1}),
                ('goals.link_task_to_goal', {'task_id': 1}),
                ('habits.check_in_habit', {'habit_id': 1}),
                ('habits.get_habits_stats', {}),
            ]
            
            for endpoint, kwargs in api_endpoints:
                try:
                    url = url_for(endpoint, **kwargs)
                    assert url is not None 
                    assert url.startswith('/')
                except Exception as e:
                    pytest.fail(f"API endpoint '{endpoint}' with args {kwargs} failed: {e}")


class TestTemplateExistence:
    """Test that all templates exist and can be rendered without TemplateNotFound."""
    
    def test_all_main_page_templates_exist(self, client, logged_in_user):
        """All main page templates render without TemplateNotFound error."""
        main_pages = [
            '/dashboard',
            '/journal',
            '/goals',
            '/habits',
            '/calendar',
            '/avatar/select'
        ]
        
        for page in main_pages:
            response = client.get(page)
            # Should not be 500 (TemplateNotFound would cause 500)
            assert response.status_code != 500, f"Template error on page {page}"
            # Should be either 200 (success) or redirect (302)
            assert response.status_code in [200, 302], f"Unexpected status {response.status_code} on {page}"
    
    def test_all_form_templates_exist(self, client, logged_in_user):
        """All form templates render correctly."""
        form_pages = [
            '/goals/create',
            '/habits/create',
            '/journal',
        ]
        
        for page in form_pages:
            response = client.get(page)
            assert response.status_code in [200, 302], f"Form template error on {page}"
            if response.status_code == 200:
                # Should contain form element
                assert b'<form' in response.data, f"No form found in {page}"
    
    def test_template_inheritance_works(self, client, logged_in_user):
        """All templates properly extend base template."""
        response = client.get('/dashboard')
        assert response.status_code == 200
        html = response.data.decode()
        
        # Check base template elements exist
        assert '<nav class="navbar' in html, "Navigation from base template missing"
        assert 'bootstrap' in html.lower(), "Bootstrap CSS/JS from base template missing"
        assert '</html>' in html, "Complete HTML structure from base template missing"


class TestLinkIntegrity:
    """Test that all links in rendered HTML are valid."""
    
    def test_dashboard_widget_links_valid(self, client, logged_in_user):
        """Dashboard widget navigation buttons link to valid endpoints."""
        response = client.get('/dashboard')
        assert response.status_code == 200
        
        html = response.data.decode()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all links in dashboard widgets
        widget_links = soup.find_all('a', class_='btn')
        
        for link in widget_links:
            href = link.get('href')
            if href and not href.startswith('#') and not href.startswith('javascript:'):
                # Test that href is a valid URL pattern
                assert href.startswith('/') or href.startswith('http'), f"Invalid href: {href}"
    
    def test_menu_links_point_to_existing_routes(self, client, logged_in_user):
        """All navigation menu links point to routes that exist."""
        response = client.get('/dashboard')
        assert response.status_code == 200
        
        html = response.data.decode()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find navigation links
        nav_links = soup.select('.navbar-nav .nav-link')
        
        for link in nav_links:
            href = link.get('href')
            if href and not href.startswith('#') and href != 'javascript:void(0)':
                # Test the link by following it
                response = client.get(href)
                assert response.status_code in [200, 302], f"Broken nav link: {href} (status: {response.status_code})"


class TestFormIntegrity:
    """Test that all forms have valid action URLs and required fields."""
    
    def test_goal_creation_form_structure(self, client, logged_in_user):
        """Goal creation form has proper structure and validation."""
        response = client.get('/goals/create')
        assert response.status_code == 200
        
        html = response.data.decode()
        soup = BeautifulSoup(html, 'html.parser')
        
        form = soup.find('form')
        assert form is not None, "No form found on goal creation page"
        
        # Check required form fields exist
        required_fields = ['title', 'description', 'target_date']
        for field in required_fields:
            field_input = soup.find(['input', 'textarea', 'select'], {'name': field})
            assert field_input is not None, f"Required field '{field}' missing from goal form"
    
    def test_habit_creation_form_structure(self, client, logged_in_user):
        """Habit creation form has proper Cue-Routine-Reward structure."""
        response = client.get('/habits/create')
        assert response.status_code == 200
        
        html = response.data.decode()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for habit loop fields
        habit_fields = ['name', 'cue', 'routine', 'reward', 'frequency']
        for field in habit_fields:
            field_input = soup.find(['input', 'textarea', 'select'], {'name': field})
            assert field_input is not None, f"Habit field '{field}' missing from form"
    
    def test_javascript_function_references_valid(self, client, logged_in_user):
        """JavaScript function references in HTML are valid."""
        pages_to_check = ['/dashboard', '/habits', '/calendar']
        
        for page in pages_to_check:
            response = client.get(page)
            assert response.status_code == 200
            html = response.data.decode()
            
            # Find onclick handlers
            onclick_functions = re.findall(r'onclick="([^"]*)"', html)
            
            for onclick in onclick_functions:
                # Extract function name (before opening parenthesis)
                func_name = onclick.split('(')[0].strip()
                if func_name:
                    # Check that function is defined somewhere in the HTML
                    assert f'function {func_name}' in html or f'{func_name} = ' in html, \
                        f"Function '{func_name}' referenced but not defined on {page}"


class TestErrorHandling:
    """Test proper error handling for edge cases."""
    
    def test_nonexistent_resource_404s(self, client, logged_in_user):
        """Non-existent resources return proper 404."""
        nonexistent_resources = [
            '/goals/99999',
            '/habits/99999',
            '/journal/entries/99999'
        ]
        
        for resource in nonexistent_resources:
            response = client.get(resource)
            assert response.status_code == 404, f"Expected 404 for {resource}, got {response.status_code}"
    
    def test_unauthorized_access_handling(self, client):
        """Unauthenticated access properly redirects."""
        protected_pages = ['/dashboard', '/goals', '/habits', '/journal']
        
        for page in protected_pages:
            response = client.get(page)
            # Should redirect to login or return 302/401
            assert response.status_code in [302, 401], f"Protected page {page} not properly secured"


# Test fixtures
@pytest.fixture
def logged_in_user(client, test_user):
    """Log in the test user."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
    return test_user