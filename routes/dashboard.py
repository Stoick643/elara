from flask import Blueprint, render_template, redirect, url_for, jsonify, request, session
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from models import db, Task, JournalEntry, Goal, Habit, Value
from sqlalchemy import desc, func
from routes.avatar import get_personality_message_for_context
from services.ai_coach import AICoach

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard view with comprehensive life coaching features."""
    today = datetime.utcnow().date()

    # Redirect to avatar selection if not set
    if not current_user.avatar_personality:
        return redirect(url_for('avatar.select_personality'))
    
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
    
    # Get AI-generated daily message (with session caching)
    ai_message = None
    message_timestamp = None
    is_message_fresh = False

    # Check session cache for AI message
    if 'ai_dashboard_message' in session and 'ai_message_timestamp' in session:
        cached_timestamp = datetime.fromisoformat(session['ai_message_timestamp'])
        # Cache for 6 hours
        if (datetime.utcnow() - cached_timestamp).total_seconds() < 6 * 3600:
            ai_message = session['ai_dashboard_message']
            message_timestamp = cached_timestamp
            is_message_fresh = (datetime.utcnow() - cached_timestamp).total_seconds() < 3600

    # Generate new message if not cached or expired
    if not ai_message:
        try:
            ai_coach = AICoach()
            message_data = ai_coach.generate_daily_dashboard_message(current_user.id)
            ai_message = message_data['message']
            message_timestamp = message_data['timestamp']
            is_message_fresh = True

            # Cache in session
            session['ai_dashboard_message'] = ai_message
            session['ai_message_timestamp'] = message_timestamp.isoformat()
            session['ai_message_personality'] = message_data['personality']
        except Exception as e:
            # Fallback to simple personality message if AI fails
            ai_message = get_personality_message_for_context(current_user, 'welcome')
            message_timestamp = datetime.utcnow()
            is_message_fresh = True

    # Get personality-based welcome message (kept for backwards compatibility)
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
    
    # ===== PHASE 3 FEATURES: Discovery & Alignment =====
    
    # Get discovery progress
    discovery_progress = current_user.get_discovery_progress()
    
    # Get orphaned tasks (tasks not connected to goals)
    orphaned_tasks = current_user.get_orphaned_tasks()[:10]  # Limit to 10 for UI
    orphaned_count = current_user.get_orphaned_tasks_count()
    
    # Show discovery prompt if not completed
    show_discovery_prompt = not discovery_progress['overall_complete']
    
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
                         today=today,

                         # Phase 3: Discovery & Alignment
                         discovery_progress=discovery_progress,
                         orphaned_tasks=orphaned_tasks,
                         orphaned_count=orphaned_count,
                         show_discovery_prompt=show_discovery_prompt,

                         # AI Coach message
                         ai_message=ai_message,
                         message_timestamp=message_timestamp,
                         is_message_fresh=is_message_fresh)

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


# ===== PHASE 3: ORPHANED TASKS & CONNECTION SYSTEM =====

@dashboard_bp.route('/api/orphaned-tasks')
@login_required
def get_orphaned_tasks():
    """Get all orphaned tasks for the user."""
    orphaned_tasks = current_user.get_orphaned_tasks()
    return jsonify({
        'success': True,
        'tasks': [{
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'energy_required': task.energy_required,
            'energy_icon': task.get_energy_icon(),
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'created_at': task.created_at.isoformat()
        } for task in orphaned_tasks]
    })


@dashboard_bp.route('/api/connect-task-to-goal', methods=['POST'])
@login_required
def connect_task_to_goal():
    """Connect an orphaned task to an existing goal."""
    data = request.get_json()
    task_id = data.get('task_id')
    goal_id = data.get('goal_id')
    
    if not task_id or not goal_id:
        return jsonify({'success': False, 'message': 'Task ID and Goal ID required'}), 400
    
    # Verify task belongs to user and is orphaned
    task = Task.query.filter_by(id=task_id, user_id=current_user.id, goal_id=None).first()
    if not task:
        return jsonify({'success': False, 'message': 'Task not found or already connected'}), 404
    
    # Verify goal belongs to user
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    if not goal:
        return jsonify({'success': False, 'message': 'Goal not found'}), 404
    
    # Connect task to goal
    task.goal_id = goal_id
    db.session.commit()
    
    # Recalculate goal progress
    goal.calculate_progress()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Task "{task.title}" connected to goal "{goal.title}"',
        'new_goal_progress': goal.progress
    })


@dashboard_bp.route('/api/create-goal-from-tasks', methods=['POST'])
@login_required
def create_goal_from_tasks():
    """Create a new goal and connect selected orphaned tasks to it."""
    data = request.get_json()
    goal_title = data.get('goal_title', '').strip()
    task_ids = data.get('task_ids', [])
    value_id = data.get('value_id')  # Optional values connection
    
    if not goal_title:
        return jsonify({'success': False, 'message': 'Goal title is required'}), 400
    
    if not task_ids:
        return jsonify({'success': False, 'message': 'At least one task must be selected'}), 400
    
    # Verify all tasks belong to user and are orphaned
    tasks = Task.query.filter(
        Task.id.in_(task_ids),
        Task.user_id == current_user.id,
        Task.goal_id == None
    ).all()
    
    if len(tasks) != len(task_ids):
        return jsonify({'success': False, 'message': 'Some tasks not found or already connected'}), 400
    
    # Create new goal
    goal = Goal(
        user_id=current_user.id,
        title=goal_title,
        value_id=value_id,
        description=f"Goal created from {len(tasks)} related tasks"
    )
    db.session.add(goal)
    db.session.flush()  # Get goal ID
    
    # Connect tasks to new goal
    for task in tasks:
        task.goal_id = goal.id
    
    db.session.commit()
    
    # Calculate initial progress
    goal.calculate_progress()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Goal "{goal_title}" created with {len(tasks)} connected tasks',
        'goal_id': goal.id,
        'goal_progress': goal.progress
    })


@dashboard_bp.route('/api/ai-task-suggestions')
@login_required
def get_ai_task_suggestions():
    """Get AI suggestions for connecting orphaned tasks."""
    try:
        ai_coach = AICoach()
        suggestions = ai_coach.suggest_task_goal_connections(current_user.id)

        return jsonify({
            'success': True,
            'suggestions': suggestions
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Unable to generate AI suggestions',
            'error': str(e)
        }), 500


@dashboard_bp.route('/api/ai/refresh-daily-message', methods=['POST'])
@login_required
def refresh_daily_message():
    """Refresh the AI daily message (rate limited to once per hour)."""
    # Check if message was refreshed recently (within 1 hour)
    if 'ai_message_last_refresh' in session:
        last_refresh = datetime.fromisoformat(session['ai_message_last_refresh'])
        seconds_since_refresh = (datetime.utcnow() - last_refresh).total_seconds()

        if seconds_since_refresh < 3600:  # 1 hour = 3600 seconds
            minutes_remaining = int((3600 - seconds_since_refresh) / 60)
            return jsonify({
                'success': False,
                'message': f'Please wait {minutes_remaining} more minute(s) before refreshing again.',
                'wait_time': minutes_remaining
            }), 429  # Too Many Requests

    try:
        ai_coach = AICoach()
        message_data = ai_coach.generate_daily_dashboard_message(current_user.id)

        # Update session cache
        session['ai_dashboard_message'] = message_data['message']
        session['ai_message_timestamp'] = message_data['timestamp'].isoformat()
        session['ai_message_personality'] = message_data['personality']
        session['ai_message_last_refresh'] = datetime.utcnow().isoformat()

        return jsonify({
            'success': True,
            'message': message_data['message'],
            'timestamp': message_data['timestamp'].isoformat(),
            'personality': message_data['personality'],
            'is_fresh': True
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Unable to generate new message. Please try again later.',
            'error': str(e)
        }), 500