from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Regexp
from models import db, User

auth_bp = Blueprint('auth', __name__)

class LoginForm(FlaskForm):
    """Login form for authentication."""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=2, max=80)
    ])
    password = PasswordField('Password', validators=[
        DataRequired()
    ])
    submit = SubmitField('Enter Elara')

class RegistrationForm(FlaskForm):
    """Registration form for new users."""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=2, max=80, message='Username must be between 2 and 80 characters.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.'),
        Regexp(r'(?=.*[A-Z])', message='Password must contain at least one uppercase letter.'),
        Regexp(r'(?=.*\d)', message='Password must contain at least one number.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    avatar_personality = SelectField('Choose Your AI Coach Personality', validators=[DataRequired()], choices=[
        ('sage', '🧙‍♂️ The Sage - Wise and philosophical, asks deep questions'),
        ('champion', '🏆 The Champion - Energetic cheerleader, celebrates wins'),
        ('friend', '🤝 The Friend - Warm and empathetic, non-judgmental'),
        ('strategist', '🎯 The Strategist - Analytical and data-driven'),
        ('zen_master', '🧘 The Zen Master - Calm and mindful, focuses on present')
    ])
    submit = SubmitField('Create My Elara Account')
    
    def validate_username(self, username):
        """Check if username is already taken."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash('Welcome back to Elara!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create new user
        user = User(
            username=form.username.data,
            avatar_personality=form.avatar_personality.data
        )
        user.set_password(form.password.data)
        
        # Save to database
        db.session.add(user)
        db.session.commit()
        
        # Log the user in immediately
        login_user(user, remember=True)
        flash(f'Welcome to Elara, {user.username}! Your {user.avatar_personality.replace("_", " ").title()} coach is ready to help you.', 'success')
        
        # Redirect to onboarding if needed, otherwise dashboard
        if user.needs_onboarding():
            return redirect(url_for('onboarding.welcome'))
        else:
            return redirect(url_for('dashboard.dashboard'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out. See you soon!', 'info')
    return redirect(url_for('index'))