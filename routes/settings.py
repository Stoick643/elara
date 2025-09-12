from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired
from models import db, User

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

class UserPreferencesForm(FlaskForm):
    """Form for user preference settings."""
    is_pro_mode = BooleanField('Enable Pro Mode', description='Access advanced features and detailed analytics')
    avatar_personality = SelectField('AI Coach Personality', choices=[
        ('sage', '🧙‍♂️ The Sage - Wise and philosophical'),
        ('champion', '🏆 The Champion - Energetic and motivating'),
        ('friend', '🤝 The Friend - Warm and supportive'),
        ('strategist', '🎯 The Strategist - Analytical and strategic'),
        ('zen_master', '🧘 The Zen Master - Calm and mindful')
    ])
    submit = SubmitField('Save Preferences')

@settings_bp.route('/')
@login_required
def settings_home():
    """Main settings page."""
    form = UserPreferencesForm()
    
    # Pre-populate form with current user settings
    form.is_pro_mode.data = current_user.is_pro_mode
    form.avatar_personality.data = current_user.avatar_personality or 'friend'
    
    return render_template('settings/preferences.html', form=form)

@settings_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def update_preferences():
    """Update user preferences."""
    form = UserPreferencesForm()
    
    if form.validate_on_submit():
        # Update user preferences
        old_mode = current_user.is_pro_mode
        current_user.is_pro_mode = form.is_pro_mode.data
        current_user.avatar_personality = form.avatar_personality.data
        
        db.session.commit()
        
        # Flash appropriate message
        if old_mode != form.is_pro_mode.data:
            if form.is_pro_mode.data:
                flash('Pro Mode enabled! You now have access to advanced features and detailed analytics.', 'success')
            else:
                flash('Simple Mode enabled! Your interface has been simplified for a cleaner experience.', 'info')
        else:
            flash('Your preferences have been updated successfully!', 'success')
        
        return redirect(url_for('settings.settings_home'))
    
    # Pre-populate form with current settings
    form.is_pro_mode.data = current_user.is_pro_mode
    form.avatar_personality.data = current_user.avatar_personality or 'friend'
    
    return render_template('settings/preferences.html', form=form)

@settings_bp.route('/toggle-mode', methods=['POST'])
@login_required
def toggle_mode():
    """AJAX endpoint to quickly toggle between simple/pro mode."""
    try:
        current_user.is_pro_mode = not current_user.is_pro_mode
        db.session.commit()
        
        mode_name = "Pro Mode" if current_user.is_pro_mode else "Simple Mode"
        
        return jsonify({
            'success': True,
            'new_mode': 'pro' if current_user.is_pro_mode else 'simple',
            'message': f'{mode_name} enabled successfully!',
            'is_pro_mode': current_user.is_pro_mode
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to toggle mode. Please try again.'
        }), 500

@settings_bp.route('/onboarding/restart')
@login_required
def restart_onboarding():
    """Allow user to restart the onboarding process."""
    current_user.onboarding_completed = False
    current_user.onboarding_step = 0
    db.session.commit()
    
    flash('Onboarding reset! You can now go through the setup process again.', 'info')
    return redirect(url_for('onboarding.welcome'))

# Helper functions for templates
@settings_bp.app_template_global()
def is_pro_mode():
    """Template function to check if current user is in pro mode."""
    from flask_login import current_user
    return current_user.is_authenticated and current_user.is_pro_mode

@settings_bp.app_template_global()
def get_user_mode():
    """Template function to get current user mode."""
    from flask_login import current_user
    if not current_user.is_authenticated:
        return 'simple'
    return 'pro' if current_user.is_pro_mode else 'simple'

@settings_bp.app_template_filter()
def feature_available(feature_name):
    """Template filter to check if a feature is available in current mode."""
    from flask_login import current_user
    
    if not current_user.is_authenticated:
        return False
    
    # Simple mode features (always available)
    simple_features = [
        'basic_dashboard',
        'simple_goals',
        'basic_habits',
        'basic_journal',
        'basic_chat'
    ]
    
    # Pro mode only features
    pro_features = [
        'advanced_analytics',
        'detailed_progress',
        'cbt_tools',
        'wheel_of_life',
        'advanced_goal_planning',
        'habit_analytics',
        'weekly_reviews',
        'values_alignment',
        'advanced_insights'
    ]
    
    if feature_name in simple_features:
        return True
    elif feature_name in pro_features:
        return current_user.is_pro_mode
    else:
        # Unknown feature - default to pro mode requirement
        return current_user.is_pro_mode