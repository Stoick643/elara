from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired
from models import db

avatar_bp = Blueprint('avatar', __name__)

class PersonalitySelectionForm(FlaskForm):
    """Form for selecting avatar personality."""
    personality = SelectField('Choose Your Coach', validators=[DataRequired()], choices=[
        ('sage', 'The Sage 🧙‍♂️'),
        ('champion', 'The Champion 🏆'),
        ('friend', 'The Friend 🤝'),
        ('strategist', 'The Strategist 🎯'),
        ('zen_master', 'The Zen Master 🧘')
    ])
    submit = SubmitField('Meet My Coach')

# Personality definitions and characteristics
PERSONALITIES = {
    'sage': {
        'name': 'The Sage',
        'emoji': '🧙‍♂️',
        'tagline': 'Wise • Philosophical • Deep',
        'description': 'The Sage offers wisdom through thoughtful questions and philosophical insights. They help you reflect on the deeper meaning of your goals and guide you with ancient wisdom and modern psychology.',
        'traits': ['Asks profound questions', 'Shares timeless wisdom', 'Encourages deep reflection', 'Focuses on meaning and purpose'],
        'sample_messages': [
            'Remember, the journey of a thousand miles begins with a single step.',
            'What wisdom will you carry forward from today\'s challenges?',
            'True growth comes not from avoiding difficulties, but from learning to dance with them.'
        ],
        'best_for': 'Those who value deep thinking, philosophical reflection, and meaningful personal growth.'
    },
    'champion': {
        'name': 'The Champion',
        'emoji': '🏆',
        'tagline': 'Energetic • Motivating • Victory-Focused',
        'description': 'The Champion is your personal cheerleader and victory coach! They celebrate every win, big or small, and keep your energy high with enthusiasm and positive reinforcement.',
        'traits': ['Celebrates every victory', 'High energy encouragement', 'Competitive motivation', 'Focus on achievement'],
        'sample_messages': [
            'YES! Another goal conquered! You\'re absolutely unstoppable! 🎉',
            'Look at that progress! You\'re crushing it today!',
            'Victory is yours! Let\'s celebrate this win and aim even higher!'
        ],
        'best_for': 'Motivated individuals who thrive on celebration, positive reinforcement, and competitive energy.'
    },
    'friend': {
        'name': 'The Friend',
        'emoji': '🤝',
        'tagline': 'Supportive • Empathetic • Understanding',
        'description': 'The Friend is your compassionate companion who\'s always there for you. They offer gentle support, understand your struggles, and help you through challenges with kindness and empathy.',
        'traits': ['Gentle and supportive', 'Acknowledges struggles', 'Non-judgmental approach', 'Emotional support'],
        'sample_messages': [
            'I\'m here with you through this. You\'re doing better than you think.',
            'It\'s okay to have tough days. Tomorrow is a fresh start, and I believe in you.',
            'You\'re making progress, even when it doesn\'t feel like it. I see your effort.'
        ],
        'best_for': 'Those who value emotional support, gentle encouragement, and a compassionate approach to growth.'
    },
    'strategist': {
        'name': 'The Strategist',
        'emoji': '🎯',
        'tagline': 'Analytical • Practical • Results-Oriented',
        'description': 'The Strategist helps you optimize your approach with data-driven insights and practical solutions. They focus on efficiency, systems, and measurable results to help you achieve your goals.',
        'traits': ['Data-driven insights', 'Practical solutions', 'System optimization', 'Efficiency focus'],
        'sample_messages': [
            'Based on your patterns, completing morning tasks increases your daily success by 73%.',
            'Let\'s optimize this process. I\'ve identified three efficiency improvements.',
            'Your goal completion rate is trending upward. Here\'s how to accelerate progress.'
        ],
        'best_for': 'Goal-oriented people who love data, systems thinking, and practical optimization strategies.'
    },
    'zen_master': {
        'name': 'The Zen Master',
        'emoji': '🧘',
        'tagline': 'Calm • Mindful • Present-Focused',
        'description': 'The Zen Master brings peace and mindfulness to your journey. They help you stay present, find balance, and approach your goals with calm intention and inner harmony.',
        'traits': ['Mindful presence', 'Inner peace focus', 'Balance emphasis', 'Present-moment awareness'],
        'sample_messages': [
            'Let this moment be exactly as it is. From here, all things are possible.',
            'Progress flows like water - sometimes fast, sometimes slow, always forward.',
            'In stillness, find your strength. In action, find your peace.'
        ],
        'best_for': 'Those seeking balance, mindfulness, inner peace, and a gentle approach to personal development.'
    }
}

@avatar_bp.route('/avatar/select', methods=['GET', 'POST'])
@login_required
def select_personality():
    """Avatar personality selection interface."""
    form = PersonalitySelectionForm()
    
    if form.validate_on_submit():
        personality = form.personality.data
        
        # Update user's personality
        current_user.avatar_personality = personality
        db.session.commit()
        
        personality_info = PERSONALITIES[personality]
        flash(f'Welcome! {personality_info["name"]} is now your personal coach. {personality_info["sample_messages"][0]}', 'success')
        
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('avatar/personality_selection.html', 
                         form=form, 
                         personalities=PERSONALITIES,
                         current_personality=current_user.avatar_personality)

@avatar_bp.route('/avatar/change', methods=['GET', 'POST'])
@login_required
def change_personality():
    """Change avatar personality."""
    form = PersonalitySelectionForm()
    
    # Set current personality as default
    if current_user.avatar_personality:
        form.personality.data = current_user.avatar_personality
    
    if form.validate_on_submit():
        new_personality = form.personality.data
        old_personality = current_user.avatar_personality
        
        current_user.avatar_personality = new_personality
        db.session.commit()
        
        old_name = PERSONALITIES.get(old_personality, {}).get('name', 'your previous coach') if old_personality else 'your previous coach'
        new_info = PERSONALITIES[new_personality]
        
        flash(f'Your coach has changed from {old_name} to {new_info["name"]}! {new_info["sample_messages"][0]}', 'info')
        
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('avatar/change_personality.html', 
                         form=form, 
                         personalities=PERSONALITIES,
                         current_personality=current_user.avatar_personality)

@avatar_bp.route('/api/avatar/message/<context>')
@login_required
def get_personality_message(context):
    """API endpoint to get personality-specific message for given context."""
    personality = current_user.avatar_personality or 'friend'
    
    messages = {
        'goal_created': {
            'sage': 'A wise goal set. Remember, the journey of a thousand miles begins with one step.',
            'champion': 'YES! Another goal to conquer! You\'ve got this! 🏆',
            'friend': 'I\'m here to support you with this new goal. We\'ll work through it together.',
            'strategist': 'Goal established. Let\'s break this down into actionable steps.',
            'zen_master': 'A new intention is set. Let it flow naturally into your daily practice.'
        },
        'goal_completed': {
            'sage': 'Your perseverance has borne fruit. What wisdom will you carry forward?',
            'champion': 'VICTORY! You absolutely crushed this goal! Time to celebrate! 🎉',
            'friend': 'I\'m so proud of you for completing this goal! You should be proud too.',
            'strategist': 'Objective achieved. Let\'s analyze what worked and optimize for next time.',
            'zen_master': 'Completion brings not ending, but transformation. What emerges next?'
        },
        'habit_created': {
            'sage': 'Habits are the compound interest of self-improvement. Begin with patience.',
            'champion': 'New habit locked and loaded! Let\'s build that streak! 💪',
            'friend': 'Starting a new habit can be challenging. I\'m here to support you every day.',
            'strategist': 'Habit loop configured. Consistency will yield optimal results.',
            'zen_master': 'A gentle practice begins. Let it unfold naturally, day by day.'
        },
        'habit_streak': {
            'sage': 'Steady drops of water can carve through stone. Your consistency is powerful.',
            'champion': 'STREAK POWER! You\'re on fire! Keep that momentum blazing! 🔥',
            'friend': 'Look at you go! I\'m proud of your dedication and consistency.',
            'strategist': 'Streak data indicates strong habit formation. Maintain current trajectory.',
            'zen_master': 'Like sunrise following sunrise, you return to your practice. Beautiful.'
        },
        'task_completed': {
            'sage': 'Each task completed is a step toward becoming who you wish to be.',
            'champion': 'Task CRUSHED! You\'re unstoppable today! 🚀',
            'friend': 'Great job getting that done! You\'re making steady progress.',
            'strategist': 'Task efficiency optimal. Productivity metrics improving.',
            'zen_master': 'One thing, completed with presence. This is the way.'
        },
        'daily_checkin': {
            'sage': 'How does your inner wisdom guide you today?',
            'champion': 'Ready to DOMINATE this day? Let\'s see what you\'ll achieve! ⚡',
            'friend': 'Good morning! How are you feeling today? I\'m here if you need support.',
            'strategist': 'Daily objectives loaded. What\'s your priority focus today?',
            'zen_master': 'A new day dawns. What intention will you carry into this moment?'
        },
        'encouragement': {
            'sage': 'Even the mightiest oak grows slowly. Trust in your gradual progress.',
            'champion': 'You\'ve got this! Every champion faces challenges - that\'s what makes victory sweet!',
            'friend': 'Remember, progress isn\'t always linear. Be gentle with yourself.',
            'strategist': 'Temporary setbacks are data points. Adjust strategy and continue forward.',
            'zen_master': 'Like the river flows around rocks, let challenges shape but not stop you.'
        }
    }
    
    message = messages.get(context, {}).get(personality, messages['encouragement']['friend'])
    personality_info = PERSONALITIES.get(personality, PERSONALITIES['friend'])
    
    return jsonify({
        'success': True,
        'message': message,
        'personality': personality,
        'personality_name': personality_info['name'],
        'personality_emoji': personality_info['emoji']
    })

@avatar_bp.route('/avatar/preview/<personality>')
@login_required
def preview_personality(personality):
    """Preview a personality without changing current selection."""
    if personality not in PERSONALITIES:
        return jsonify({'success': False, 'message': 'Invalid personality'}), 400
    
    personality_info = PERSONALITIES[personality]
    return jsonify({
        'success': True,
        'personality': personality_info,
        'sample_interaction': {
            'daily_checkin': get_personality_message('daily_checkin').get_json()['message'],
            'goal_completed': get_personality_message('goal_completed').get_json()['message'],
            'encouragement': get_personality_message('encouragement').get_json()['message']
        }
    })

@avatar_bp.route('/avatar/info')
@login_required
def avatar_info():
    """Display current avatar information and options."""
    current_personality = current_user.avatar_personality or 'friend'
    current_info = PERSONALITIES.get(current_personality, PERSONALITIES['friend'])
    
    return render_template('avatar/avatar_info.html', 
                         current_info=current_info,
                         current_personality=current_personality,
                         all_personalities=PERSONALITIES)

# Helper functions for other modules to use
def get_personality_message_for_context(user, context, **kwargs):
    """Helper function to get personality-specific messages for any user and context."""
    personality = user.avatar_personality or 'friend'
    
    # This would be expanded with more contexts and dynamic message generation
    base_messages = {
        'welcome': {
            'sage': 'Welcome back, seeker of wisdom.',
            'champion': 'The champion returns! Ready to conquer the day?',
            'friend': 'Welcome back! Good to see you again.',
            'strategist': 'System initialized. Ready for optimal productivity.',
            'zen_master': 'Welcome to this moment of possibility.'
        }
    }
    
    return base_messages.get(context, {}).get(personality, base_messages['welcome']['friend'])