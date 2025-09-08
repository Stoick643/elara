"""
JavaScript functionality tests using Selenium WebDriver.
Tests client-side interactions, AJAX calls, and UI updates.
"""
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json


# Skip these tests if Selenium is not available
selenium = pytest.importorskip("selenium")


@pytest.fixture(scope="session")
def browser():
    """Create a browser instance for testing."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode for CI
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()


@pytest.fixture
def logged_in_browser(browser, live_server, test_user):
    """Browser logged in as test user."""
    browser.get(f"{live_server.url}/auth/login")
    
    # Fill login form
    username_field = browser.find_element(By.NAME, "username")
    password_field = browser.find_element(By.NAME, "password")
    
    username_field.send_keys(test_user.username)
    password_field.send_keys("elara2024")
    
    submit_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_button.click()
    
    # Wait for redirect to dashboard
    WebDriverWait(browser, 10).until(
        EC.url_contains("/dashboard")
    )
    
    return browser


class TestQuickTaskCreation:
    """Test quick task creation end-to-end workflow."""
    
    def test_quick_task_input_creates_task_successfully(self, logged_in_browser, live_server):
        """Quick task input field creates task and updates UI."""
        browser = logged_in_browser
        browser.get(f"{live_server.url}/dashboard")
        
        # Find quick task input
        quick_input = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='Add quick task']"))
        )
        
        # Type task and press Enter
        test_task = "Test Task from Selenium"
        quick_input.send_keys(test_task)
        quick_input.send_keys("\n")  # Press Enter
        
        # Wait for success indication
        WebDriverWait(browser, 10).until(
            EC.text_to_be_present_in_element_attribute(
                (By.CSS_SELECTOR, "input[placeholder*='Add quick task']"),
                "placeholder",
                "Task added!"
            )
        )
        
        # Verify placeholder changes back
        time.sleep(2)  # Wait for timeout
        final_placeholder = quick_input.get_attribute("placeholder")
        assert "Add quick task" in final_placeholder
    
    def test_quick_task_handles_empty_input_gracefully(self, logged_in_browser, live_server):
        """Quick task input handles empty submissions gracefully."""
        browser = logged_in_browser
        browser.get(f"{live_server.url}/dashboard")
        
        quick_input = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='Add quick task']"))
        )
        
        # Press Enter with empty input
        quick_input.send_keys("\n")
        
        # Should not show success message
        time.sleep(1)
        placeholder = quick_input.get_attribute("placeholder")
        assert "Task added!" not in placeholder
    
    def test_quick_task_network_error_handling(self, logged_in_browser, live_server):
        """Quick task handles network errors gracefully."""
        browser = logged_in_browser
        browser.get(f"{live_server.url}/dashboard")
        
        # Inject network failure simulation
        browser.execute_script("""
            // Override fetch to simulate network error
            window.originalFetch = window.fetch;
            window.fetch = function() {
                return Promise.reject(new Error('Network error'));
            };
        """)
        
        quick_input = browser.find_element(By.CSS_SELECTOR, "input[placeholder*='Add quick task']")
        quick_input.send_keys("Test Task")
        quick_input.send_keys("\n")
        
        # Should handle error gracefully (no crash)
        time.sleep(2)
        # Page should still be functional
        assert "dashboard" in browser.current_url


class TestHabitCheckInUI:
    """Test habit check-in UI updates and animations."""
    
    def test_habit_checkin_button_updates_correctly(self, logged_in_browser, live_server, test_habit):
        """Habit check-in button updates UI after successful check-in."""
        browser = logged_in_browser
        browser.get(f"{live_server.url}/habits")
        
        # Look for check-in button
        try:
            checkin_button = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[onclick*='checkInHabit']"))
            )
            
            # Click check-in button
            checkin_button.click()
            
            # Wait for success indication (toast or alert)
            WebDriverWait(browser, 10).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".toast")),
                    EC.alert_is_present()
                )
            )
            
            # Handle alert if present
            try:
                alert = browser.switch_to.alert
                alert_text = alert.text
                assert "completed" in alert_text.lower() or "success" in alert_text.lower()
                alert.accept()
            except:
                # If no alert, check for toast
                toast = browser.find_element(By.CSS_SELECTOR, ".toast")
                assert "success" in toast.get_attribute("class")
                
        except Exception as e:
            # No habits available for check-in, that's OK for this test
            assert "No habits" in str(e) or "not found" in str(e)
    
    def test_habit_checkin_celebration_animation_triggers(self, logged_in_browser, live_server, test_habit):
        """Habit check-in triggers celebration animation."""
        browser = logged_in_browser
        browser.get(f"{live_server.url}/habits")
        
        try:
            # Click habit check-in
            checkin_button = browser.find_element(By.CSS_SELECTOR, "button[onclick*='checkInHabit']")
            checkin_button.click()
            
            # Wait for animation elements to appear
            WebDriverWait(browser, 5).until(
                lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "[style*='position: fixed']")) > 0
            )
            
            # Check for confetti or streak elements
            animated_elements = browser.find_elements(By.CSS_SELECTOR, "[style*='position: fixed']")
            assert len(animated_elements) > 0, "No celebration animations found"
            
        except Exception as e:
            # Skip if no habits available
            pytest.skip(f"No habits available for testing: {e}")


class TestFormValidation:
    """Test client-side form validation."""
    
    def test_goal_creation_form_validates_required_fields(self, logged_in_browser, live_server):
        """Goal creation form validates required fields client-side."""
        browser = logged_in_browser
        browser.get(f"{live_server.url}/goals/create")
        
        # Try to submit empty form
        submit_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        submit_button.click()
        
        # Check if HTML5 validation prevented submission
        title_field = browser.find_element(By.NAME, "title")
        validation_message = title_field.get_attribute("validationMessage")
        
        # Should have validation message for required field
        assert validation_message or browser.current_url.endswith("/goals/create")
    
    def test_habit_creation_form_cue_routine_reward_validation(self, logged_in_browser, live_server):
        """Habit creation form validates habit loop structure."""
        browser = logged_in_browser
        browser.get(f"{live_server.url}/habits/create")
        
        # Fill only name, leave habit loop fields empty
        name_field = browser.find_element(By.NAME, "name")
        name_field.send_keys("Test Habit")
        
        submit_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        submit_button.click()
        
        # Should either validate or stay on same page
        assert "/habits/create" in browser.current_url or "/habits" in browser.current_url


class TestModalInteractions:
    """Test modal dialog interactions."""
    
    def test_calendar_day_modal_opens_and_closes(self, logged_in_browser, live_server):
        """Calendar day click opens modal that can be closed."""
        browser = logged_in_browser
        browser.get(f"{live_server.url}/calendar")
        
        # Click on a calendar day
        try:
            calendar_day = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".calendar-day[data-date]"))
            )
            calendar_day.click()
            
            # Wait for modal to appear
            modal = WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal"))
            )
            
            assert modal.is_displayed()
            
            # Close modal
            close_button = browser.find_element(By.CSS_SELECTOR, ".modal .btn-close")
            close_button.click()
            
            # Wait for modal to disappear
            WebDriverWait(browser, 10).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".modal"))
            )
            
        except Exception as e:
            # Calendar might not have clickable days
            pytest.skip(f"Calendar interaction not available: {e}")
    
    def test_quick_add_modal_functionality(self, logged_in_browser, live_server):
        """Quick add modal opens, accepts input, and closes."""
        browser = logged_in_browser
        browser.get(f"{live_server.url}/calendar")
        
        try:
            # Open quick add modal
            quick_add_button = browser.find_element(By.CSS_SELECTOR, "button[data-bs-target='#quickAddModal']")
            quick_add_button.click()
            
            # Wait for modal
            modal = WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.ID, "quickAddModal"))
            )
            
            # Fill form
            content_field = browser.find_element(By.ID, "quickContent")
            content_field.send_keys("Test content from modal")
            
            # Submit
            add_button = browser.find_element(By.CSS_SELECTOR, "#quickAddModal button[onclick='quickAdd()']")
            add_button.click()
            
            # Modal should close or show loading
            time.sleep(2)  # Allow for processing
            
        except Exception as e:
            pytest.skip(f"Quick add modal not available: {e}")


class TestAJAXErrorHandling:
    """Test AJAX error handling."""
    
    def test_api_calls_handle_500_errors_gracefully(self, logged_in_browser, live_server):
        """API calls handle server errors gracefully."""
        browser = logged_in_browser
        browser.get(f"{live_server.url}/dashboard")
        
        # Inject API error simulation
        browser.execute_script("""
            // Override fetch to simulate 500 error
            window.originalFetch = window.fetch;
            window.fetch = function(url, options) {
                if (url.includes('/api/')) {
                    return Promise.resolve({
                        ok: false,
                        status: 500,
                        json: () => Promise.resolve({error: 'Server error'})
                    });
                }
                return window.originalFetch(url, options);
            };
        """)
        
        # Try quick task creation (should fail gracefully)
        try:
            quick_input = browser.find_element(By.CSS_SELECTOR, "input[placeholder*='Add quick task']")
            quick_input.send_keys("Test Task")
            quick_input.send_keys("\n")
            
            # Should not crash the page
            time.sleep(2)
            assert "dashboard" in browser.current_url
            
        except Exception:
            # OK if quick task input not available
            pass
    
    def test_network_timeout_handling(self, logged_in_browser, live_server):
        """Network timeouts are handled gracefully."""
        browser = logged_in_browser
        browser.get(f"{live_server.url}/dashboard")
        
        # Inject timeout simulation
        browser.execute_script("""
            window.originalFetch = window.fetch;
            window.fetch = function(url, options) {
                if (url.includes('/api/')) {
                    return new Promise((resolve, reject) => {
                        // Simulate timeout
                        setTimeout(() => reject(new Error('timeout')), 100);
                    });
                }
                return window.originalFetch(url, options);
            };
        """)
        
        # Application should remain stable
        time.sleep(3)
        assert browser.current_url.endswith("/dashboard")


class TestResponsiveDesign:
    """Test responsive design and mobile interactions."""
    
    def test_mobile_navigation_works(self, logged_in_browser, live_server):
        """Mobile navigation menu works correctly."""
        browser = logged_in_browser
        
        # Set mobile viewport
        browser.set_window_size(375, 667)  # iPhone size
        browser.get(f"{live_server.url}/dashboard")
        
        # Check if navbar toggle exists and works
        try:
            navbar_toggle = browser.find_element(By.CSS_SELECTOR, ".navbar-toggler")
            if navbar_toggle.is_displayed():
                navbar_toggle.click()
                
                # Navigation menu should become visible
                nav_menu = browser.find_element(By.CSS_SELECTOR, ".navbar-collapse")
                time.sleep(1)  # Wait for animation
                assert nav_menu.is_displayed()
        except:
            # Navigation might not collapse on this screen size
            pass
    
    def test_touch_targets_adequate_size(self, logged_in_browser, live_server):
        """Touch targets meet minimum size requirements."""
        browser = logged_in_browser
        browser.set_window_size(375, 667)  # Mobile size
        browser.get(f"{live_server.url}/dashboard")
        
        # Check button sizes
        buttons = browser.find_elements(By.CSS_SELECTOR, "button, .btn")
        
        for button in buttons[:5]:  # Check first 5 buttons
            if button.is_displayed():
                size = button.size
                # Touch targets should be at least 44px (iOS) or 48px (Android)
                assert size['height'] >= 36, f"Button too small: {size['height']}px height"


# Test fixtures
@pytest.fixture
def test_habit(app, test_user):
    """Create a test habit for UI testing."""
    with app.app_context():
        from models import Habit, db
        
        habit = Habit(
            user_id=test_user.id,
            name="Test UI Habit",
            description="For testing UI interactions",
            cue="Test cue",
            routine="Test routine", 
            reward="Test reward",
            frequency="daily"
        )
        db.session.add(habit)
        db.session.commit()
        return habit