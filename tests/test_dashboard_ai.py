"""Integration tests for dashboard AI message functionality."""
import pytest
from unittest.mock import patch
from flask import session
from datetime import datetime


def test_dashboard_includes_ai_message(app, client, test_user):
    """Test that dashboard route includes AI message in context."""
    with app.app_context():
        # Mock AICoach to avoid actual API calls
        with patch('routes.dashboard.AICoach') as MockAICoach:
            mock_coach = MockAICoach.return_value
            mock_coach.generate_daily_dashboard_message.return_value = {
                'message': 'Test AI message',
                'timestamp': datetime.utcnow(),
                'personality': 'friend',
                'tokens_used': 50
            }

            # Log in (inside patch context to avoid MagicMock in session)
            client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)

            response = client.get('/dashboard')

            assert response.status_code == 200
            assert b'Test AI message' in response.data
            assert b'ai-welcome-card' in response.data


def test_dashboard_caches_ai_message(app, client, test_user):
    """Test that AI message is cached in session."""
    with app.app_context():
        with patch('routes.dashboard.AICoach') as MockAICoach:
            mock_coach = MockAICoach.return_value
            mock_coach.generate_daily_dashboard_message.return_value = {
                'message': 'Cached message',
                'timestamp': datetime.utcnow(),
                'personality': 'friend',
                'tokens_used': 50
            }

            # Log in (inside patch context to avoid MagicMock in session)
            client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)

            # First request
            response1 = client.get('/dashboard')
            assert response1.status_code == 200

            # Check session has cached message
            with client.session_transaction() as sess:
                assert 'ai_dashboard_message' in sess
                assert sess['ai_dashboard_message'] == 'Cached message'

            # Second request should use cache
            response2 = client.get('/dashboard')
            assert response2.status_code == 200

            # Should only be called once (cached on second call)
            assert mock_coach.generate_daily_dashboard_message.call_count == 1


def test_refresh_daily_message_endpoint(app, client, test_user):
    """Test the refresh endpoint returns new message."""
    with app.app_context():
        with patch('routes.dashboard.AICoach') as MockAICoach:
            mock_coach = MockAICoach.return_value
            mock_coach.generate_daily_dashboard_message.return_value = {
                'message': 'New refreshed message',
                'timestamp': datetime.utcnow(),
                'personality': 'friend',
                'tokens_used': 45
            }

            # Log in (inside patch context to avoid MagicMock in session)
            client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)

            response = client.post('/api/ai/refresh-daily-message',
                                  content_type='application/json')

            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['message'] == 'New refreshed message'
            assert data['personality'] == 'friend'


def test_refresh_endpoint_requires_auth(app, client):
    """Test that refresh endpoint requires authentication."""
    with app.app_context():
        response = client.post('/api/ai/refresh-daily-message',
                              content_type='application/json')

        assert response.status_code == 401 or response.status_code == 302


def test_refresh_endpoint_rate_limiting(app, client, test_user):
    """Test that refresh endpoint enforces rate limiting."""
    with app.app_context():
        with patch('routes.dashboard.AICoach') as MockAICoach:
            mock_coach = MockAICoach.return_value
            mock_coach.generate_daily_dashboard_message.return_value = {
                'message': 'Test message',
                'timestamp': datetime.utcnow(),
                'personality': 'friend',
                'tokens_used': 40
            }

            # Log in (inside patch context to avoid MagicMock in session)
            client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)

            # First refresh should succeed
            response1 = client.post('/api/ai/refresh-daily-message',
                                   content_type='application/json')
            assert response1.status_code == 200

            # Immediate second refresh should be rate limited
            response2 = client.post('/api/ai/refresh-daily-message',
                                   content_type='application/json')
            assert response2.status_code == 429  # Too Many Requests
            data = response2.get_json()
            assert data['success'] is False
            assert 'wait' in data['message'].lower()


def test_dashboard_handles_ai_error_gracefully(app, client, test_user):
    """Test that dashboard works even if AI generation fails."""
    with app.app_context():
        with patch('routes.dashboard.AICoach') as MockAICoach:
            # Simulate AI coach initialization failure
            MockAICoach.side_effect = Exception("API error")

            # Log in (inside patch context to avoid MagicMock in session)
            client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)

            response = client.get('/dashboard')

            # Dashboard should still load
            assert response.status_code == 200
            # Should show fallback message
            assert b'Welcome back' in response.data or b'make today count' in response.data


def test_dashboard_shows_personality_avatar(app, client, test_user):
    """Test that dashboard shows correct personality avatar."""
    with app.app_context():
        with patch('routes.dashboard.AICoach') as MockAICoach:
            mock_coach = MockAICoach.return_value
            mock_coach.generate_daily_dashboard_message.return_value = {
                'message': 'Test message',
                'timestamp': datetime.utcnow(),
                'personality': 'friend',
                'tokens_used': 30
            }

            # Log in (inside patch context to avoid MagicMock in session)
            client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)

            response = client.get('/dashboard')

            assert response.status_code == 200
            # Check for Friend personality icon
            assert b'fa-heart' in response.data
            assert b'The Friend' in response.data


def test_refresh_endpoint_error_handling(app, client, test_user):
    """Test error handling in refresh endpoint."""
    with app.app_context():
        with patch('routes.dashboard.AICoach') as MockAICoach:
            mock_coach = MockAICoach.return_value
            # Simulate API failure
            mock_coach.generate_daily_dashboard_message.side_effect = Exception("API down")

            # Log in (inside patch context to avoid MagicMock in session)
            client.post('/auth/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)

            response = client.post('/api/ai/refresh-daily-message',
                                  content_type='application/json')

            assert response.status_code == 500
            data = response.get_json()
            assert data['success'] is False
            assert 'unable' in data['message'].lower() or 'error' in data['message'].lower()
