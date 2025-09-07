from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db, Task, JournalEntry
from sqlalchemy import desc

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard view."""
    # Get today's tasks
    today = datetime.utcnow().date()
    todays_tasks = Task.query.filter_by(
        user_id=current_user.id,
        completed=False
    ).filter(
        (Task.due_date == today) | (Task.due_date == None)
    ).limit(5).all()
    
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
    
    return render_template('dashboard/dashboard.html',
                         todays_tasks=todays_tasks,
                         recent_journal=recent_journal,
                         week_progress=week_progress,
                         completed_this_week=completed_this_week,
                         mood_trend=mood_trend,
                         avg_mood=round(avg_mood, 1))

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