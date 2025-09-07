from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Optional
from datetime import datetime, date
from models import db, Goal, Value, Task

goals_bp = Blueprint('goals', __name__)

class GoalForm(FlaskForm):
    """Form for creating and editing goals."""
    title = StringField('Goal Title', validators=[
        DataRequired(),
        Length(min=3, max=200)
    ])
    description = TextAreaField('Description', validators=[Optional()])
    value_id = SelectField('Life Area', coerce=int, validators=[Optional()])
    target_date = DateField('Target Date', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed')
    ], default='active')
    submit = SubmitField('Save Goal')

class TaskLinkForm(FlaskForm):
    """Form for linking tasks to goals."""
    task_id = HiddenField('Task ID', validators=[DataRequired()])
    goal_id = SelectField('Link to Goal', coerce=int, validators=[Optional()])
    submit = SubmitField('Link Task')

@goals_bp.route('/goals')
@login_required
def goals_list():
    """Display all user goals with progress."""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'active')
    
    query = Goal.query.filter_by(user_id=current_user.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    goals = query.order_by(Goal.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    # Update progress for all goals
    for goal in goals.items:
        goal.calculate_progress()
    db.session.commit()
    
    # Get values for categorization
    values = Value.query.filter_by(user_id=current_user.id).all()
    
    return render_template('goals/goals_list.html', 
                         goals=goals, 
                         values=values,
                         current_status=status_filter)

@goals_bp.route('/goals/create', methods=['GET', 'POST'])
@login_required
def create_goal():
    """Create a new goal."""
    form = GoalForm()
    
    # Populate value choices
    values = Value.query.filter_by(user_id=current_user.id).all()
    form.value_id.choices = [(0, 'No specific area')] + [(v.id, v.name) for v in values]
    
    if form.validate_on_submit():
        goal = Goal(
            user_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
            value_id=form.value_id.data if form.value_id.data > 0 else None,
            target_date=form.target_date.data,
            status=form.status.data
        )
        
        db.session.add(goal)
        db.session.commit()
        
        flash(f'Goal "{goal.title}" created successfully!', 'success')
        return redirect(url_for('goals.goals_list'))
    
    return render_template('goals/create_goal.html', form=form)

@goals_bp.route('/goals/<int:goal_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_goal(goal_id):
    """Edit an existing goal."""
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    form = GoalForm(obj=goal)
    
    # Populate value choices
    values = Value.query.filter_by(user_id=current_user.id).all()
    form.value_id.choices = [(0, 'No specific area')] + [(v.id, v.name) for v in values]
    
    if form.validate_on_submit():
        goal.title = form.title.data
        goal.description = form.description.data
        goal.value_id = form.value_id.data if form.value_id.data > 0 else None
        goal.target_date = form.target_date.data
        goal.status = form.status.data
        
        # If marking as completed, set completion date
        if form.status.data == 'completed' and goal.status != 'completed':
            goal.mark_complete()
        
        db.session.commit()
        flash(f'Goal "{goal.title}" updated successfully!', 'success')
        return redirect(url_for('goals.view_goal', goal_id=goal.id))
    
    # Set current value for form
    form.value_id.data = goal.value_id or 0
    
    return render_template('goals/edit_goal.html', form=form, goal=goal)

@goals_bp.route('/goals/<int:goal_id>')
@login_required
def view_goal(goal_id):
    """View goal details with linked tasks."""
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    
    # Update progress
    goal.calculate_progress()
    db.session.commit()
    
    # Get linked tasks
    linked_tasks = goal.tasks.order_by(Task.completed, Task.due_date).all()
    
    # Get unlinked tasks for potential linking
    unlinked_tasks = Task.query.filter_by(
        user_id=current_user.id,
        goal_id=None,
        completed=False
    ).limit(10).all()
    
    task_link_form = TaskLinkForm()
    task_link_form.goal_id.choices = [(goal.id, goal.title)]
    
    return render_template('goals/view_goal.html', 
                         goal=goal, 
                         linked_tasks=linked_tasks,
                         unlinked_tasks=unlinked_tasks,
                         task_link_form=task_link_form)

@goals_bp.route('/goals/<int:goal_id>/delete', methods=['POST'])
@login_required
def delete_goal(goal_id):
    """Delete a goal (unlinks tasks but doesn't delete them)."""
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    
    # Unlink all tasks from this goal
    for task in goal.tasks:
        task.goal_id = None
    
    goal_title = goal.title
    db.session.delete(goal)
    db.session.commit()
    
    flash(f'Goal "{goal_title}" deleted. Tasks were unlinked but preserved.', 'info')
    return redirect(url_for('goals.goals_list'))

@goals_bp.route('/api/goals/<int:goal_id>/progress')
@login_required
def get_goal_progress(goal_id):
    """API endpoint to get current goal progress."""
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    progress = goal.calculate_progress()
    db.session.commit()
    
    return jsonify({
        'goal_id': goal.id,
        'progress': progress,
        'total_tasks': goal.tasks.count(),
        'completed_tasks': goal.tasks.filter_by(completed=True).count(),
        'status': goal.status
    })

@goals_bp.route('/api/tasks/<int:task_id>/link-goal', methods=['POST'])
@login_required
def link_task_to_goal(task_id):
    """API endpoint to link a task to a goal."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    data = request.get_json()
    goal_id = data.get('goal_id')
    
    if goal_id:
        goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
        task.goal_id = goal_id
        goal.calculate_progress()
        message = f'Task "{task.title}" linked to goal "{goal.title}"'
    else:
        # Unlink from goal
        old_goal = task.goal
        task.goal_id = None
        if old_goal:
            old_goal.calculate_progress()
        message = f'Task "{task.title}" unlinked from goal'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': message,
        'task_id': task.id,
        'goal_id': task.goal_id
    })

@goals_bp.route('/values')
@login_required
def values_list():
    """Display and manage life area values."""
    values = Value.query.filter_by(user_id=current_user.id).order_by(Value.priority.desc()).all()
    return render_template('goals/values_list.html', values=values)

@goals_bp.route('/values/create', methods=['POST'])
@login_required
def create_value():
    """Create a new life area value."""
    name = request.form.get('name')
    description = request.form.get('description', '')
    priority = int(request.form.get('priority', 1))
    
    if name:
        value = Value(
            user_id=current_user.id,
            name=name,
            description=description,
            priority=priority
        )
        db.session.add(value)
        db.session.commit()
        flash(f'Life area "{name}" created!', 'success')
    
    return redirect(url_for('goals.values_list'))

@goals_bp.route('/api/goals/quick-create', methods=['POST'])
@login_required
def quick_create_goal():
    """API endpoint for quick goal creation from dashboard."""
    data = request.get_json()
    title = data.get('title')
    
    if not title:
        return jsonify({'success': False, 'message': 'Goal title is required'}), 400
    
    goal = Goal(
        user_id=current_user.id,
        title=title,
        description=data.get('description', ''),
        target_date=datetime.strptime(data.get('target_date'), '%Y-%m-%d').date() if data.get('target_date') else None
    )
    
    db.session.add(goal)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Goal "{title}" created!',
        'goal_id': goal.id,
        'goal_url': url_for('goals.view_goal', goal_id=goal.id)
    })

# Helper function for personality-based messages
def get_personality_goal_message(personality, context):
    """Get personality-specific messages for goal interactions."""
    messages = {
        'sage': {
            'created': 'A wise goal set. Remember, the journey of a thousand miles begins with one step.',
            'completed': 'Your perseverance has borne fruit. What wisdom will you carry forward?',
            'progress': 'Steady progress is the mark of wisdom. Continue with mindful intention.'
        },
        'champion': {
            'created': 'Yes! Another goal to conquer! You\'ve got this! 🏆',
            'completed': 'VICTORY! You absolutely crushed this goal! Time to celebrate! 🎉',
            'progress': 'Look at that progress! You\'re unstoppable! Keep pushing forward!'
        },
        'friend': {
            'created': 'I\'m here to support you with this new goal. We\'ll work through it together.',
            'completed': 'I\'m so proud of you for completing this goal! You should be proud too.',
            'progress': 'You\'re doing great! Remember, progress isn\'t always linear, and that\'s okay.'
        },
        'strategist': {
            'created': 'Goal established. Let\'s break this down into actionable steps.',
            'completed': 'Objective achieved. Let\'s analyze what worked and optimize for next time.',
            'progress': 'Progress data looks good. Consider these efficiency improvements...'
        },
        'zen_master': {
            'created': 'A new intention is set. Let it flow naturally into your daily practice.',
            'completed': 'Completion brings not ending, but transformation. What emerges next?',
            'progress': 'Progress flows like water - sometimes fast, sometimes slow, always forward.'
        }
    }
    
    return messages.get(personality, messages['friend']).get(context, '')