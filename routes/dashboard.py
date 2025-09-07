from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from models import db, Task, JournalEntry, Goal, Habit, Value
from sqlalchemy import desc, func
from routes.avatar import get_personality_message_for_context

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard view with comprehensive life coaching features."""
    today = datetime.utcnow().date()
    
    # Redirect to avatar selection if not set (temporarily disabled for testing)
    # if not current_user.avatar_personality:
    #     return redirect(url_for('avatar.select_personality'))
    
    # Get today's tasks (limit 5 for HCI principles)
    todays_tasks = Task.query.filter_by(
        user_id=current_user.id,
        completed=False
    ).filter(
        (Task.due_date == today) | (Task.due_date == None)
    ).order_by(Task.energy_required, Task.created_at).limit(5).all()
    
    # Get recent journal entry
    recent_journal = JournalEntry.query.filter_by(
        user_id=current_user.id
    ).order_by(desc(JournalEntry.created_at)).first()
    
    # Calculate this week's progress
    week_start = today - timedelta(days=today.weekday())
    completed_this_week = Task.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).filter(
        Task.completed_at >= week_start
    ).count()
    
    total_this_week = Task.query.filter_by(
        user_id=current_user.id
    ).filter(
        Task.created_at >= week_start
    ).count()
    
    week_progress = (completed_this_week / total_this_week * 100) if total_this_week > 0 else 0
    
    # Get mood trend for last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    mood_entries = JournalEntry.query.filter_by(
        user_id=current_user.id
    ).filter(
        JournalEntry.created_at >= week_ago
    ).order_by(JournalEntry.created_at).all()
    
    mood_trend = [
        {
            'date': entry.created_at.strftime('%m/%d'),
            'mood': entry.mood_score or 5,
            'emoji': entry.get_mood_emoji()
        }
        for entry in mood_entries
    ]
    
    # Calculate average mood
    avg_mood = sum(entry['mood'] for entry in mood_trend) / len(mood_trend) if mood_trend else 5
    
    # ===== NEW PHASE 2 FEATURES =====
    
    # Get active goals with progress
    active_goals = Goal.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).order_by(Goal.progress.desc()).limit(3).all()
    
    # Update goal progress
    for goal in active_goals:
        goal.calculate_progress()
    db.session.commit()
    
    # Get today's habits
    active_habits = Habit.query.filter_by(
        user_id=current_user.id,
        active=True
    ).order_by(Habit.streak_count.desc()).all()
    
    # Separate completed vs pending habits for today
    habits_today = []
    for habit in active_habits:
        habits_today.append({
            'habit': habit,
            'completed': habit.is_completed_today(),
            'can_complete': not habit.is_completed_today()
        })
    
    # Calculate habit completion rate for today
    completed_habits_count = sum(1 for h in habits_today if h['completed'])
    habit_completion_rate = (completed_habits_count / len(habits_today) * 100) if habits_today else 0
    
    # Get personality-based welcome message
    personality_message = get_personality_message_for_context(current_user, 'welcome')
    
    # Get upcoming deadlines (goals and tasks)
    upcoming_deadlines = []
    
    # Add goal deadlines
    for goal in Goal.query.filter_by(user_id=current_user.id, status='active').all():
        if goal.target_date and goal.target_date >= today:
            days_until = (goal.target_date - today).days
            upcoming_deadlines.append({
                'type': 'goal',
                'title': goal.title,
                'date': goal.target_date,
                'days_until': days_until,
                'progress': goal.progress
            })
    
    # Add task deadlines
    for task in Task.query.filter_by(user_id=current_user.id, completed=False).all():
        if task.due_date and task.due_date >= today:
            days_until = (task.due_date - today).days
            upcoming_deadlines.append({
                'type': 'task',
                'title': task.title,
                'date': task.due_date,
                'days_until': days_until,
                'energy': task.energy_required,
                'energy_icon': task.get_energy_icon()
            })
    
    # Sort by date and limit to 5
    upcoming_deadlines = sorted(upcoming_deadlines, key=lambda x: x['date'])[:5]
    
    # Calculate life areas balance (if user has values)
    life_balance = {}
    values = Value.query.filter_by(user_id=current_user.id).all()
    for value in values:
        goals_count = value.goals.filter_by(status='active').count()
        completed_goals = value.goals.filter_by(status='completed').count()
        life_balance[value.name] = {
            'active_goals': goals_count,
            'completed_goals': completed_goals,
            'priority': value.priority
        }
    
    return render_template('dashboard/dashboard.html',
                         # Existing data
                         todays_tasks=todays_tasks,
                         recent_journal=recent_journal,
                         week_progress=week_progress,
                         completed_this_week=completed_this_week,
                         mood_trend=mood_trend,
                         avg_mood=round(avg_mood, 1),
                         
                         # New Phase 2 data
                         active_goals=active_goals,
                         habits_today=habits_today,
                         habit_completion_rate=habit_completion_rate,
                         personality_message=personality_message,
                         upcoming_deadlines=upcoming_deadlines,
                         life_balance=life_balance,
                         today=today)

@dashboard_bp.route('/api/complete-task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    """Mark a task as complete."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    task.mark_complete()
    db.session.commit()
    return jsonify({'success': True, 'message': 'Task completed!'})

@dashboard_bp.route('/api/quick-mood', methods=['POST'])
@login_required
def quick_mood():
    """Quick mood check-in."""
    mood = request.json.get('mood', 5)
    
    # Create a minimal journal entry
    entry = JournalEntry(
        user_id=current_user.id,
        content=f"Quick mood check-in",
        mood_score=mood
    )
    db.session.add(entry)
    db.session.commit()
    
    return jsonify({'success': True, 'emoji': entry.get_mood_emoji()})

@dashboard_bp.route('/api/quick-task', methods=['POST'])
@login_required
def quick_add_task():
    """Quick task creation from dashboard."""
    data = request.get_json()
    title = data.get('title')
    
    if not title:
        return jsonify({'success': False, 'message': 'Task title required'}), 400
    
    task = Task(
        user_id=current_user.id,
        title=title,
        energy_required=data.get('energy', 'medium'),
        due_date=datetime.strptime(data.get('due_date'), '%Y-%m-%d').date() if data.get('due_date') else None
    )
    
    db.session.add(task)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Task "{title}" created!',
        'task_id': task.id
    })

@dashboard_bp.route('/api/habit-checkin/<int:habit_id>', methods=['POST'])
@login_required
def habit_checkin_dashboard(habit_id):
    """Quick habit check-in from dashboard."""
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    
    if habit.check_in_today():
        db.session.commit()
        
        # Get personality-specific celebration message
        from routes.avatar import PERSONALITIES
        personality = current_user.avatar_personality or 'friend'
        celebration_messages = {
            'sage': f'Wisdom grows through consistent practice. Well done on {habit.name}.',
            'champion': f'YES! Another victory! {habit.name} COMPLETED! 🔥',
            'friend': f'Great job completing {habit.name}! I\'m proud of your consistency.',
            'strategist': f'{habit.name} completed. Streak optimized to {habit.streak_count} days.',
            'zen_master': f'Like the sun rises each day, you return to {habit.name}. Beautiful.'
        }
        
        return jsonify({
            'success': True,
            'message': celebration_messages.get(personality, celebration_messages['friend']),
            'streak_count': habit.streak_count,
            'streak_emoji': habit.get_streak_emoji()
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Habit already completed today!'
        })

@dashboard_bp.route('/api/dashboard-stats')
@login_required
def get_dashboard_stats():
    """Get comprehensive dashboard statistics."""
    today = date.today()
    
    # Tasks stats
    total_tasks = Task.query.filter_by(user_id=current_user.id).count()
    completed_tasks = Task.query.filter_by(user_id=current_user.id, completed=True).count()
    
    # Goals stats
    total_goals = Goal.query.filter_by(user_id=current_user.id).count()
    completed_goals = Goal.query.filter_by(user_id=current_user.id, status='completed').count()
    
    # Habits stats
    total_habits = Habit.query.filter_by(user_id=current_user.id, active=True).count()
    completed_today_habits = sum(1 for h in Habit.query.filter_by(user_id=current_user.id, active=True).all() 
                               if h.is_completed_today())
    
    # Journal stats
    total_entries = JournalEntry.query.filter_by(user_id=current_user.id).count()
    this_week_entries = JournalEntry.query.filter_by(user_id=current_user.id).filter(
        JournalEntry.created_at >= datetime.now() - timedelta(days=7)
    ).count()
    
    return jsonify({
        'tasks': {
            'total': total_tasks,
            'completed': completed_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        },
        'goals': {
            'total': total_goals,
            'completed': completed_goals,
            'completion_rate': (completed_goals / total_goals * 100) if total_goals > 0 else 0
        },
        'habits': {
            'total': total_habits,
            'completed_today': completed_today_habits,
            'completion_rate_today': (completed_today_habits / total_habits * 100) if total_habits > 0 else 0
        },
        'journal': {
            'total_entries': total_entries,
            'this_week': this_week_entries
        }
    })