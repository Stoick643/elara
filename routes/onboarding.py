from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, TextAreaField, SubmitField, RadioField
from wtforms.validators import DataRequired, Length
from models import db, User

onboarding_bp = Blueprint('onboarding', __name__, url_prefix='/onboarding')

# Common values for quick selection
COMMON_VALUES = [
    ('authenticity', 'Authenticity - Being true to yourself'),
    ('family', 'Family - Close relationships and loved ones'),
    ('growth', 'Personal Growth - Continuous learning and development'),
    ('health', 'Health - Physical and mental wellbeing'),
    ('creativity', 'Creativity - Self-expression and innovation'),
    ('adventure', 'Adventure - New experiences and exploration'),
    ('security', 'Security - Stability and peace of mind'),
    ('contribution', 'Contribution - Making a positive impact'),
    ('freedom', 'Freedom - Independence and autonomy'),
    ('excellence', 'Excellence - High quality and achievement'),
    ('connection', 'Connection - Meaningful relationships'),
    ('spirituality', 'Spirituality - Inner peace and purpose')
]

class ValuesSelectionForm(FlaskForm):
    """Form for selecting core values during onboarding."""
    value1 = SelectField('First Core Value', choices=COMMON_VALUES, validators=[DataRequired()])
    value2 = SelectField('Second Core Value', choices=COMMON_VALUES, validators=[DataRequired()])
    value3 = SelectField('Third Core Value', choices=COMMON_VALUES, validators=[DataRequired()])
    submit = SubmitField('Continue to Goals')

class FirstGoalForm(FlaskForm):
    """Form for creating first goal during onboarding."""
    title = StringField('Goal Title', validators=[
        DataRequired(),
        Length(min=3, max=200, message='Goal title must be between 3 and 200 characters.')
    ])
    description = TextAreaField('Description (Optional)', validators=[
        Length(max=500, message='Description must be less than 500 characters.')
    ])
    submit = SubmitField('Create My First Goal')

class FirstHabitForm(FlaskForm):
    """Form for setting up first habit during onboarding."""
    name = StringField('Habit Name', validators=[
        DataRequired(),
        Length(min=3, max=100, message='Habit name must be between 3 and 100 characters.')
    ])
    frequency = RadioField('How Often?', choices=[
        ('daily', 'Daily'),
        ('weekly', '3-4 times per week'),
        ('custom', 'Custom schedule')
    ], default='daily', validators=[DataRequired()])
    submit = SubmitField('Start Building This Habit')

@onboarding_bp.route('/welcome')
@login_required
def welcome():
    """Welcome screen with AI coach greeting."""
    if current_user.onboarding_completed:
        flash('You have already completed onboarding!', 'info')
        return redirect(url_for('dashboard.dashboard'))
    
    # Get personality-specific welcome message
    personality = current_user.avatar_personality or 'friend'
    welcome_messages = {
        'sage': f"Welcome, {current_user.username}. I am here to guide you on a journey of self-discovery and wisdom. Together, we shall explore the depths of your potential and illuminate the path to your authentic self.",
        'champion': f"Hey {current_user.username}! 🎉 I'm SO excited to be your coach! We're going to achieve AMAZING things together! Are you ready to unlock your full potential and crush those goals?",
        'friend': f"Hi {current_user.username}! I'm really glad you're here. Think of me as your supportive friend who's always in your corner. We'll take this journey one step at a time, and I'll be here to encourage you along the way.",
        'strategist': f"Welcome, {current_user.username}. I'm your strategic advisor, and I'm here to help you create a systematic approach to achieving your objectives. Let's build a data-driven plan for your success.",
        'zen_master': f"Welcome, {current_user.username}. 🧘 In this moment, we begin a journey of mindful growth. Let us cultivate awareness, find balance, and discover the peace that comes from aligned action."
    }
    
    coach_message = welcome_messages.get(personality, welcome_messages['friend'])
    
    return render_template('onboarding/welcome.html', 
                         coach_message=coach_message,
                         personality=personality)

@onboarding_bp.route('/skip')
@login_required
def skip_onboarding():
    """Skip the entire onboarding process."""
    current_user.skip_onboarding()
    flash('Onboarding skipped! You can always access setup options from your settings.', 'info')
    return redirect(url_for('dashboard.dashboard'))

@onboarding_bp.route('/values', methods=['GET', 'POST'])
@login_required
def values_selection():
    """Step 1: Select core values."""
    if current_user.onboarding_completed or current_user.onboarding_step > 1:
        return redirect(url_for('onboarding.goal_creation'))
    
    form = ValuesSelectionForm()
    if form.validate_on_submit():
        # Import here to avoid circular imports
        from models import Value
        
        # Create three core values for the user
        values_data = [
            (form.value1.data, dict(COMMON_VALUES)[form.value1.data]),
            (form.value2.data, dict(COMMON_VALUES)[form.value2.data]),
            (form.value3.data, dict(COMMON_VALUES)[form.value3.data])
        ]
        
        for i, (value_key, value_desc) in enumerate(values_data, 1):
            value = Value(
                user_id=current_user.id,
                name=value_key.title(),
                description=value_desc.split(' - ')[1],  # Remove the key part
                priority=i
            )
            db.session.add(value)
        
        # Advance onboarding step
        current_user.onboarding_step = 1
        db.session.commit()
        
        flash('Great! Your core values have been saved.', 'success')
        return redirect(url_for('onboarding.goal_creation'))
    
    return render_template('onboarding/values_selection.html', form=form)

@onboarding_bp.route('/goal', methods=['GET', 'POST'])
@login_required
def goal_creation():
    """Step 2: Create first goal."""
    if current_user.onboarding_completed or current_user.onboarding_step != 1:
        if current_user.onboarding_step == 0:
            return redirect(url_for('onboarding.values_selection'))
        elif current_user.onboarding_step > 1:
            return redirect(url_for('onboarding.habit_creation'))
    
    form = FirstGoalForm()
    if form.validate_on_submit():
        # Import here to avoid circular imports
        from models import Goal
        
        # Get user's first value to align with
        first_value = current_user.values.first()
        
        goal = Goal(
            user_id=current_user.id,
            title=form.title.data,
            description=form.description.data or f"A meaningful goal aligned with my value of {first_value.name if first_value else 'personal growth'}",
            value_id=first_value.id if first_value else None,
            status='active',
            progress=0
        )
        db.session.add(goal)
        
        # Advance onboarding step
        current_user.onboarding_step = 2
        db.session.commit()
        
        flash(f'Excellent! Your goal "{goal.title}" has been created.', 'success')
        return redirect(url_for('onboarding.habit_creation'))
    
    return render_template('onboarding/goal_creation.html', form=form)

@onboarding_bp.route('/habit', methods=['GET', 'POST'])
@login_required
def habit_creation():
    """Step 3: Set up first habit."""
    if current_user.onboarding_completed or current_user.onboarding_step != 2:
        if current_user.onboarding_step < 2:
            return redirect(url_for('onboarding.values_selection'))
        elif current_user.onboarding_step > 2:
            return redirect(url_for('onboarding.completion'))
    
    form = FirstHabitForm()
    if form.validate_on_submit():
        # Import here to avoid circular imports
        from models import Habit
        
        habit = Habit(
            user_id=current_user.id,
            name=form.name.data,
            cue_type='time',
            cue_time='09:00',  # Default morning time
            routine=form.name.data,
            reward='Feeling accomplished and making progress',
            frequency=form.frequency.data,
            active=True,
            streak_count=0
        )
        db.session.add(habit)
        
        # Advance onboarding step
        current_user.onboarding_step = 3
        db.session.commit()
        
        flash(f'Perfect! Your habit "{habit.name}" is now active.', 'success')
        return redirect(url_for('onboarding.completion'))
    
    return render_template('onboarding/habit_creation.html', form=form)

@onboarding_bp.route('/complete')
@login_required
def completion():
    """Final step: Complete onboarding."""
    if current_user.onboarding_completed:
        return redirect(url_for('dashboard.dashboard'))
    
    if current_user.onboarding_step < 3:
        return redirect(url_for('onboarding.values_selection'))
    
    # Mark onboarding as completed
    current_user.complete_onboarding()
    
    flash('🎉 Welcome to Elara! Your setup is complete and your journey begins now.', 'success')
    return redirect(url_for('dashboard.dashboard'))