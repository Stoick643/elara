from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
import calendar as cal
from models import db, Task, Goal, Habit, JournalEntry, HabitLog
from sqlalchemy import func, and_

calendar_bp = Blueprint('calendar', __name__)

def get_month_calendar_data(year, month):
    """Generate calendar data for a specific month."""
    # Get first and last day of month
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    
    # Get all tasks for this month
    tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.due_date >= first_day,
        Task.due_date <= last_day
    ).all()
    
    # Get journal entries for this month
    journal_entries = JournalEntry.query.filter(
        JournalEntry.user_id == current_user.id,
        func.date(JournalEntry.created_at) >= first_day,
        func.date(JournalEntry.created_at) <= last_day
    ).all()
    
    # Get habit completions for this month
    habit_completions = {}
    habit_logs = HabitLog.query.join(Habit).filter(
        Habit.user_id == current_user.id,
        HabitLog.completed_date >= first_day,
        HabitLog.completed_date <= last_day
    ).all()
    
    for log in habit_logs:
        date_str = log.completed_date.strftime('%Y-%m-%d')
        if date_str not in habit_completions:
            habit_completions[date_str] = 0
        habit_completions[date_str] += 1
    
    # Organize data by date
    calendar_data = {}
    
    # Group tasks by date
    for task in tasks:
        if task.due_date not in calendar_data:
            calendar_data[task.due_date] = {
                'tasks': [],
                'completed_tasks': 0,
                'pending_tasks': 0,
                'journal_entries': [],
                'habits_completed': 0,
                'mood_avg': None
            }
        calendar_data[task.due_date]['tasks'].append(task)
        if task.completed:
            calendar_data[task.due_date]['completed_tasks'] += 1
        else:
            calendar_data[task.due_date]['pending_tasks'] += 1
    
    # Group journal entries by date
    for entry in journal_entries:
        entry_date = entry.created_at.date()
        if entry_date not in calendar_data:
            calendar_data[entry_date] = {
                'tasks': [],
                'completed_tasks': 0,
                'pending_tasks': 0,
                'journal_entries': [],
                'habits_completed': 0,
                'mood_avg': None
            }
        calendar_data[entry_date]['journal_entries'].append(entry)
    
    # Add habit completions
    for completion_date, count in habit_completions.items():
        if completion_date not in calendar_data:
            calendar_data[completion_date] = {
                'tasks': [],
                'completed_tasks': 0,
                'pending_tasks': 0,
                'journal_entries': [],
                'habits_completed': 0,
                'mood_avg': None
            }
        calendar_data[completion_date]['habits_completed'] = count
    
    # Calculate mood averages for days with journal entries
    for day_date, data in calendar_data.items():
        if data['journal_entries']:
            moods = [e.mood_score for e in data['journal_entries'] if e.mood_score]
            if moods:
                data['mood_avg'] = sum(moods) / len(moods)
    
    return calendar_data

@calendar_bp.route('/calendar')
@calendar_bp.route('/calendar/<int:year>/<int:month>')
@login_required
def calendar_view(year=None, month=None):
    """Display monthly calendar view."""
    if year is None or month is None:
        today = date.today()
        year, month = today.year, today.month
    
    # Validate date
    try:
        first_day = date(year, month, 1)
    except ValueError:
        flash('Invalid date provided.', 'error')
        today = date.today()
        return redirect(url_for('calendar.calendar_view', year=today.year, month=today.month))
    
    # Get calendar data
    calendar_data = get_month_calendar_data(year, month)
    
    # Generate calendar grid
    cal.setfirstweekday(6)  # Sunday = 0, Monday = 1, ..., Saturday = 6
    month_calendar = cal.monthcalendar(year, month)
    
    # Navigation dates
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1
    
    month_name = cal.month_name[month]
    
    return render_template('calendar/calendar_view.html',
                         calendar_data=calendar_data,
                         month_calendar=month_calendar,
                         year=year,
                         month=month,
                         month_name=month_name,
                         prev_year=prev_year,
                         prev_month=prev_month,
                         next_year=next_year,
                         next_month=next_month,
                         today=date.today())

@calendar_bp.route('/calendar/week')
@calendar_bp.route('/calendar/week/<int:year>/<int:week>')
@login_required
def week_view(year=None, week=None):
    """Display weekly calendar view."""
    if year is None or week is None:
        today = date.today()
        year, week, _ = today.isocalendar()
    
    # Get start and end of week
    start_of_week = datetime.strptime(f'{year}-W{week}-1', "%Y-W%W-%w").date()
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
    
    # Get data for this week
    week_data = {}
    for day in week_dates:
        calendar_data = get_month_calendar_data(day.year, day.month)
        if day in calendar_data:
            week_data[day] = calendar_data[day]
        else:
            week_data[day] = {
                'tasks': [],
                'completed_tasks': 0,
                'pending_tasks': 0,
                'journal_entries': [],
                'habits_completed': 0,
                'mood_avg': None
            }
    
    return render_template('calendar/week_view.html',
                         week_data=week_data,
                         week_dates=week_dates,
                         year=year,
                         week=week,
                         today=date.today())

@calendar_bp.route('/api/calendar/task/create', methods=['POST'])
@login_required
def create_task_on_date():
    """API endpoint to create task on specific date via calendar."""
    data = request.get_json()
    
    title = data.get('title')
    due_date_str = data.get('due_date')
    goal_id = data.get('goal_id')
    energy_level = data.get('energy_level', 'medium')
    
    if not title or not due_date_str:
        return jsonify({'success': False, 'message': 'Title and date are required'}), 400
    
    try:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    
    # Validate goal if provided
    goal = None
    if goal_id:
        goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first()
        if not goal:
            return jsonify({'success': False, 'message': 'Invalid goal'}), 400
    
    task = Task(
        user_id=current_user.id,
        goal_id=goal_id if goal else None,
        title=title,
        due_date=due_date,
        energy_required=energy_level
    )
    
    db.session.add(task)
    
    # Update goal progress if linked
    if goal:
        goal.calculate_progress()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Task "{title}" created for {due_date.strftime("%B %d, %Y")}',
        'task_id': task.id,
        'task_url': url_for('dashboard.dashboard')  # Could link to task detail view
    })

@calendar_bp.route('/api/calendar/task/<int:task_id>/move', methods=['POST'])
@login_required
def move_task_date(task_id):
    """API endpoint to move task to different date."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    data = request.get_json()
    new_date_str = data.get('new_date')
    
    if not new_date_str:
        return jsonify({'success': False, 'message': 'New date is required'}), 400
    
    try:
        new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    
    old_date = task.due_date
    task.due_date = new_date
    db.session.commit()
    
    old_date_str = old_date.strftime('%B %d, %Y') if old_date else 'unscheduled'
    new_date_str = new_date.strftime('%B %d, %Y')
    
    return jsonify({
        'success': True,
        'message': f'Task "{task.title}" moved from {old_date_str} to {new_date_str}',
        'task_id': task.id,
        'old_date': old_date.isoformat() if old_date else None,
        'new_date': new_date.isoformat()
    })

@calendar_bp.route('/api/calendar/date/<date_str>')
@login_required
def get_date_details(date_str):
    """API endpoint to get detailed information for a specific date."""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    
    # Get tasks for this date
    tasks = Task.query.filter_by(
        user_id=current_user.id,
        due_date=target_date
    ).order_by(Task.completed, Task.energy_required).all()
    
    # Get journal entries for this date
    journal_entries = JournalEntry.query.filter(
        JournalEntry.user_id == current_user.id,
        func.date(JournalEntry.created_at) == target_date
    ).order_by(JournalEntry.created_at.desc()).all()
    
    # Get habits for this date
    habits = Habit.query.filter_by(user_id=current_user.id, active=True).all()
    habit_status = []
    for habit in habits:
        completed_today = habit.habit_logs.filter_by(completed_date=target_date).first() is not None
        habit_status.append({
            'id': habit.id,
            'name': habit.name,
            'completed': completed_today,
            'streak': habit.streak_count
        })
    
    # Get available goals for task creation
    goals = Goal.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).order_by(Goal.title).all()
    
    return jsonify({
        'success': True,
        'date': target_date.isoformat(),
        'date_display': target_date.strftime('%A, %B %d, %Y'),
        'tasks': [{
            'id': t.id,
            'title': t.title,
            'completed': t.completed,
            'energy': t.energy_required,
            'energy_icon': t.get_energy_icon(),
            'goal_title': t.goal.title if t.goal else None
        } for t in tasks],
        'journal_entries': [{
            'id': e.id,
            'content': e.content[:100] + '...' if len(e.content) > 100 else e.content,
            'mood_score': e.mood_score,
            'mood_emoji': e.get_mood_emoji(),
            'created_at': e.created_at.strftime('%I:%M %p')
        } for e in journal_entries],
        'habits': habit_status,
        'goals': [{
            'id': g.id,
            'title': g.title,
            'progress': g.progress
        } for g in goals]
    })

@calendar_bp.route('/calendar/today')
@login_required
def today_view():
    """Detailed view of today's activities."""
    today = date.today()
    
    # Get today's data
    calendar_data = get_month_calendar_data(today.year, today.month)
    today_data = calendar_data.get(today, {
        'tasks': [],
        'completed_tasks': 0,
        'pending_tasks': 0,
        'journal_entries': [],
        'habits_completed': 0,
        'mood_avg': None
    })
    
    # Get all active habits to show completion status
    habits = Habit.query.filter_by(user_id=current_user.id, active=True).all()
    habit_status = []
    for habit in habits:
        completed_today = habit.is_completed_today()
        habit_status.append({
            'habit': habit,
            'completed': completed_today,
            'can_complete': not completed_today
        })
    
    # Get available goals for quick task creation
    goals = Goal.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).order_by(Goal.title).all()
    
    return render_template('calendar/today_view.html',
                         today=today,
                         today_data=today_data,
                         habit_status=habit_status,
                         goals=goals)