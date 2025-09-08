from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from datetime import datetime, date, timedelta
from models import db, Habit, HabitLog

habits_bp = Blueprint('habits', __name__)

class HabitForm(FlaskForm):
    """Form for creating habits with cue-routine-reward structure."""
    name = StringField('Habit Name', validators=[
        DataRequired(),
        Length(min=3, max=200)
    ])
    description = TextAreaField('Description (Optional)', validators=[Optional()])
    
    # Habit Loop Components
    cue = StringField('Cue (Trigger)', validators=[
        DataRequired(),
        Length(min=5, max=500)
    ], description='What triggers this habit? (time, location, emotion, etc.)')
    
    routine = StringField('Routine (The Behavior)', validators=[
        DataRequired(),
        Length(min=5, max=500)
    ], description='What exactly will you do?')
    
    reward = StringField('Reward (The Benefit)', validators=[
        DataRequired(),
        Length(min=5, max=500)
    ], description='What benefit will you get from doing this?')
    
    frequency = SelectField('Frequency', choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly')
    ], default='daily')
    
    submit = SubmitField('Create Habit')

@habits_bp.route('/habits')
@login_required
def habits_dashboard():
    """Main habits dashboard with today's check-ins."""
    today = date.today()
    
    # Get all active habits
    habits = Habit.query.filter_by(
        user_id=current_user.id,
        active=True
    ).order_by(Habit.streak_count.desc()).all()
    
    # Separate completed vs pending for today
    completed_today = []
    pending_today = []
    
    for habit in habits:
        if habit.is_completed_today():
            completed_today.append(habit)
        else:
            pending_today.append(habit)
    
    # Calculate stats
    total_habits = len(habits)
    completion_rate = (len(completed_today) / total_habits * 100) if total_habits > 0 else 0
    longest_streak = max([h.best_streak for h in habits]) if habits else 0
    
    return render_template('habits/dashboard.html',
                         habits=habits,
                         completed_today=completed_today,
                         pending_today=pending_today,
                         completion_rate=completion_rate,
                         longest_streak=longest_streak,
                         today=today)

@habits_bp.route('/habits/create', methods=['GET', 'POST'])
@login_required
def create_habit_wizard():
    """Guided habit creation wizard using psychological principles."""
    form = HabitForm()
    
    if form.validate_on_submit():
        habit = Habit(
            user_id=current_user.id,
            name=form.name.data,
            description=form.description.data,
            cue=form.cue.data,
            routine=form.routine.data,
            reward=form.reward.data,
            frequency=form.frequency.data
        )
        
        db.session.add(habit)
        db.session.commit()
        
        flash(f'Habit "{habit.name}" created! Your habit loop is ready to activate.', 'success')
        return redirect(url_for('habits.view_habit', habit_id=habit.id))
    
    return render_template('habits/create_wizard.html', form=form)

@habits_bp.route('/habits/<int:habit_id>')
@login_required
def view_habit(habit_id):
    """View habit details with streak history and analytics."""
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    
    # Get recent completion history (last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_logs = HabitLog.query.filter(
        HabitLog.habit_id == habit.id,
        HabitLog.completed_date >= thirty_days_ago
    ).order_by(HabitLog.completed_date.desc()).all()
    
    # Create calendar heatmap data
    completion_dates = [log.completed_date for log in recent_logs]
    calendar_data = []
    for i in range(30):
        day = date.today() - timedelta(days=i)
        calendar_data.append({
            'date': day,
            'completed': day in completion_dates,
            'day_name': day.strftime('%a'),
            'day_number': day.day
        })
    
    calendar_data.reverse()  # Show oldest to newest
    
    # Calculate completion rate
    total_days = len(calendar_data)
    completed_days = len([d for d in calendar_data if d['completed']])
    completion_rate = (completed_days / total_days * 100) if total_days > 0 else 0
    
    return render_template('habits/view_habit.html',
                         habit=habit,
                         calendar_data=calendar_data,
                         completion_rate=completion_rate,
                         recent_logs=recent_logs[:10],
                         today=date.today())

@habits_bp.route('/habits/<int:habit_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    """Edit habit details."""
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    form = HabitForm(obj=habit)
    
    if form.validate_on_submit():
        habit.name = form.name.data
        habit.description = form.description.data
        habit.cue = form.cue.data
        habit.routine = form.routine.data
        habit.reward = form.reward.data
        habit.frequency = form.frequency.data
        
        db.session.commit()
        flash(f'Habit "{habit.name}" updated successfully!', 'success')
        return redirect(url_for('habits.view_habit', habit_id=habit.id))
    
    return render_template('habits/edit_habit.html', form=form, habit=habit)

@habits_bp.route('/api/habits/<int:habit_id>/checkin', methods=['POST'])
@login_required
def check_in_habit(habit_id):
    """API endpoint for daily habit check-in."""
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    
    if habit.check_in_today():
        db.session.commit()
        
        # Determine celebration level
        celebration_type = 'normal'
        if habit.streak_count == 1:
            celebration_type = 'first'
        elif habit.streak_count == 7:
            celebration_type = 'week'
        elif habit.streak_count == 30:
            celebration_type = 'month'
        elif habit.streak_count == 100:
            celebration_type = 'hundred'
        elif habit.streak_count > habit.best_streak - 1:
            celebration_type = 'personal_best'
        
        return jsonify({
            'success': True,
            'message': f'Great job! You\'ve completed "{habit.name}"',
            'streak_count': habit.streak_count,
            'streak_emoji': habit.get_streak_emoji(),
            'celebration_type': celebration_type,
            'is_personal_best': habit.streak_count == habit.best_streak
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Habit already completed today!',
            'streak_count': habit.streak_count
        })

@habits_bp.route('/api/habits/<int:habit_id>/skip', methods=['POST'])
@login_required
def skip_habit(habit_id):
    """API endpoint to skip a habit for today."""
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    
    # This would typically break the streak, but we'll be gentle
    return jsonify({
        'success': True,
        'message': f'Skipped "{habit.name}" for today. Tomorrow is a fresh start!',
        'streak_count': habit.streak_count
    })

@habits_bp.route('/habits/<int:habit_id>/pause', methods=['POST'])
@login_required
def pause_habit(habit_id):
    """Pause/unpause a habit."""
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    
    habit.active = not habit.active
    db.session.commit()
    
    status = 'paused' if not habit.active else 'resumed'
    flash(f'Habit "{habit.name}" has been {status}.', 'info')
    
    return redirect(url_for('habits.view_habit', habit_id=habit.id))

@habits_bp.route('/habits/<int:habit_id>/delete', methods=['POST'])
@login_required
def delete_habit(habit_id):
    """Delete a habit and all its logs."""
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    
    habit_name = habit.name
    db.session.delete(habit)
    db.session.commit()
    
    flash(f'Habit "{habit_name}" has been deleted.', 'info')
    return redirect(url_for('habits.habits_dashboard'))

@habits_bp.route('/api/habits/quick-checkin', methods=['POST'])
@login_required
def quick_checkin_all():
    """Quick check-in for multiple habits from dashboard."""
    data = request.get_json()
    habit_ids = data.get('habit_ids', [])
    
    results = []
    for habit_id in habit_ids:
        habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()
        if habit and habit.check_in_today():
            results.append({
                'habit_id': habit.id,
                'name': habit.name,
                'success': True,
                'streak': habit.streak_count
            })
    
    if results:
        db.session.commit()
    
    return jsonify({
        'success': True,
        'completed_habits': results,
        'total_completed': len(results)
    })

@habits_bp.route('/api/habits/stats')
@login_required
def get_habits_stats():
    """Get overall habit statistics."""
    habits = Habit.query.filter_by(user_id=current_user.id, active=True).all()
    
    if not habits:
        return jsonify({
            'total_habits': 0,
            'completion_rate_today': 0,
            'avg_streak': 0,
            'best_streak': 0
        })
    
    completed_today = sum(1 for h in habits if h.is_completed_today())
    avg_streak = sum(h.streak_count for h in habits) / len(habits)
    best_streak = max(h.best_streak for h in habits)
    
    return jsonify({
        'total_habits': len(habits),
        'completion_rate_today': (completed_today / len(habits)) * 100,
        'avg_streak': round(avg_streak, 1),
        'best_streak': best_streak,
        'completed_today': completed_today,
        'pending_today': len(habits) - completed_today
    })

# Habit templates for quick setup
HABIT_TEMPLATES = {
    'health': [
        {
            'name': 'Morning Meditation',
            'cue': 'After I wake up and brush my teeth',
            'routine': 'I will meditate for 10 minutes using a meditation app',
            'reward': 'I will feel calmer and more centered for the day'
        },
        {
            'name': 'Daily Exercise',
            'cue': 'At 7 AM when my workout clothes are laid out',
            'routine': 'I will do 30 minutes of exercise (gym, walk, or home workout)',
            'reward': 'I will feel energized and proud of taking care of my health'
        }
    ],
    'productivity': [
        {
            'name': 'Daily Planning',
            'cue': 'After my morning coffee',
            'routine': 'I will write down my top 3 priorities for the day',
            'reward': 'I will feel organized and focused on what matters most'
        },
        {
            'name': 'Email Processing',
            'cue': 'At 2 PM after lunch',
            'routine': 'I will process all emails in my inbox using the 2-minute rule',
            'reward': 'I will have a clear inbox and reduced stress'
        }
    ],
    'learning': [
        {
            'name': 'Daily Reading',
            'cue': 'After dinner is finished',
            'routine': 'I will read for 20 minutes from a book',
            'reward': 'I will learn something new and feel intellectually stimulated'
        }
    ]
}

@habits_bp.route('/habits/templates')
@login_required
def habit_templates():
    """Display habit templates for quick setup."""
    return render_template('habits/templates.html', templates=HABIT_TEMPLATES)

@habits_bp.route('/api/habits/create-from-template', methods=['POST'])
@login_required
def create_from_template():
    """Create habit from template."""
    data = request.get_json()
    template = data.get('template')
    
    if not template:
        return jsonify({'success': False, 'message': 'Template data required'}), 400
    
    habit = Habit(
        user_id=current_user.id,
        name=template['name'],
        cue=template['cue'],
        routine=template['routine'],
        reward=template['reward'],
        frequency='daily'
    )
    
    db.session.add(habit)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Habit "{habit.name}" created from template!',
        'habit_id': habit.id,
        'habit_url': url_for('habits.view_habit', habit_id=habit.id)
    })