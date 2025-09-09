from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from models import db, Task, Goal
from sqlalchemy import desc

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/tasks')
@login_required
def task_list():
    """Display all user tasks with filtering options."""
    # Get filter parameters
    filter_type = request.args.get('filter', 'all')  # all, pending, completed, overdue
    goal_filter = request.args.get('goal_id', type=int)
    search = request.args.get('search', '').strip()
    
    # Base query
    query = Task.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if filter_type == 'pending':
        query = query.filter_by(completed=False)
    elif filter_type == 'completed':
        query = query.filter_by(completed=True)
    elif filter_type == 'overdue':
        query = query.filter(
            Task.completed == False,
            Task.due_date < date.today()
        )
    
    # Goal filter
    if goal_filter:
        query = query.filter_by(goal_id=goal_filter)
    
    # Search filter
    if search:
        query = query.filter(Task.title.contains(search))
    
    # Order tasks
    query = query.order_by(
        Task.completed.asc(),  # Uncompleted first
        Task.due_date.asc().nullslast(),  # Due date ascending
        Task.created_at.desc()  # Most recent first
    )
    
    tasks = query.all()
    
    # Get available goals for filtering
    goals = Goal.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).order_by(Goal.title).all()
    
    # Calculate task counts
    total_tasks = Task.query.filter_by(user_id=current_user.id).count()
    pending_tasks = Task.query.filter_by(user_id=current_user.id, completed=False).count()
    completed_tasks = Task.query.filter_by(user_id=current_user.id, completed=True).count()
    overdue_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.completed == False,
        Task.due_date < date.today()
    ).count()
    
    return render_template('tasks/task_list.html',
                         tasks=tasks,
                         goals=goals,
                         filter_type=filter_type,
                         goal_filter=goal_filter,
                         search=search,
                         total_tasks=total_tasks,
                         pending_tasks=pending_tasks,
                         completed_tasks=completed_tasks,
                         overdue_tasks=overdue_tasks,
                         today=date.today())

@tasks_bp.route('/tasks/<int:task_id>')
@login_required
def task_detail(task_id):
    """Display individual task details."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    # Get available goals for potential reassignment
    goals = Goal.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).order_by(Goal.title).all()
    
    return render_template('tasks/task_detail.html',
                         task=task,
                         goals=goals,
                         today=date.today())

@tasks_bp.route('/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task():
    """Create a new task."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date_str = request.form.get('due_date', '').strip()
        energy_required = request.form.get('energy_required', 'medium')
        goal_id = request.form.get('goal_id', type=int)
        
        # Validation
        if not title:
            flash('Task title is required.', 'error')
            return redirect(url_for('tasks.create_task'))
        
        # Parse due date
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid due date format.', 'error')
                return redirect(url_for('tasks.create_task'))
        
        # Validate goal if provided
        goal = None
        if goal_id:
            goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first()
            if not goal:
                flash('Invalid goal selected.', 'error')
                return redirect(url_for('tasks.create_task'))
        
        # Create task
        task = Task(
            user_id=current_user.id,
            goal_id=goal_id if goal else None,
            title=title,
            description=description,
            due_date=due_date,
            energy_required=energy_required
        )
        
        db.session.add(task)
        db.session.commit()
        
        # Update goal progress if linked
        if goal:
            goal.calculate_progress()
            db.session.commit()
        
        flash(f'Task "{title}" created successfully!', 'success')
        return redirect(url_for('tasks.task_detail', task_id=task.id))
    
    # GET request - show form
    goals = Goal.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).order_by(Goal.title).all()
    
    # Pre-fill due date from query param if coming from calendar
    default_due_date = request.args.get('due_date', '')
    
    return render_template('tasks/task_create.html',
                         goals=goals,
                         default_due_date=default_due_date,
                         date=date)

@tasks_bp.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    """Edit an existing task."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date_str = request.form.get('due_date', '').strip()
        energy_required = request.form.get('energy_required', 'medium')
        goal_id = request.form.get('goal_id', type=int)
        
        # Validation
        if not title:
            flash('Task title is required.', 'error')
            return redirect(url_for('tasks.edit_task', task_id=task_id))
        
        # Parse due date
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid due date format.', 'error')
                return redirect(url_for('tasks.edit_task', task_id=task_id))
        
        # Validate goal if provided
        goal = None
        if goal_id:
            goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first()
            if not goal:
                flash('Invalid goal selected.', 'error')
                return redirect(url_for('tasks.edit_task', task_id=task_id))
        
        # Update task
        old_goal_id = task.goal_id
        task.title = title
        task.description = description
        task.due_date = due_date
        task.energy_required = energy_required
        task.goal_id = goal_id if goal else None
        
        db.session.commit()
        
        # Update progress for old and new goals
        if old_goal_id and old_goal_id != goal_id:
            old_goal = Goal.query.get(old_goal_id)
            if old_goal:
                old_goal.calculate_progress()
        
        if goal:
            goal.calculate_progress()
        
        db.session.commit()
        
        flash(f'Task "{title}" updated successfully!', 'success')
        return redirect(url_for('tasks.task_detail', task_id=task.id))
    
    # GET request - show form
    goals = Goal.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).order_by(Goal.title).all()
    
    return render_template('tasks/task_edit.html',
                         task=task,
                         goals=goals,
                         date=date)

@tasks_bp.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    """Delete a task."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    title = task.title
    goal = task.goal
    
    db.session.delete(task)
    db.session.commit()
    
    # Update goal progress if task was linked
    if goal:
        goal.calculate_progress()
        db.session.commit()
    
    flash(f'Task "{title}" deleted successfully!', 'success')
    return redirect(url_for('tasks.task_list'))

@tasks_bp.route('/api/tasks/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(task_id):
    """Toggle task completion status."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    if task.completed:
        task.completed = False
        task.completed_at = None
        message = f'Task "{task.title}" marked as incomplete'
        action = 'uncompleted'
    else:
        task.mark_complete()
        message = f'Task "{task.title}" completed! 🎉'
        action = 'completed'
    
    db.session.commit()
    
    # Update goal progress if linked
    if task.goal:
        task.goal.calculate_progress()
        db.session.commit()
    
    return jsonify({
        'success': True,
        'message': message,
        'action': action,
        'task_id': task.id,
        'completed': task.completed
    })