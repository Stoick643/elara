from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from datetime import datetime
from models import db, JournalEntry

journal_bp = Blueprint('journal', __name__)

class JournalForm(FlaskForm):
    """Form for journal entries."""
    content = TextAreaField('What\'s on your mind?', validators=[
        DataRequired(message='Please write something...')
    ])
    mood_score = IntegerField('Mood (1-10)', validators=[
        NumberRange(min=1, max=10, message='Mood must be between 1 and 10')
    ])
    energy_level = IntegerField('Energy (1-10)', validators=[
        NumberRange(min=1, max=10, message='Energy must be between 1 and 10')
    ])
    submit = SubmitField('Save Entry')

@journal_bp.route('/', methods=['GET', 'POST'])
@login_required
def journal():
    """Create new journal entry."""
    form = JournalForm()
    
    if form.validate_on_submit():
        entry = JournalEntry(
            user_id=current_user.id,
            content=form.content.data,
            mood_score=form.mood_score.data,
            energy_level=form.energy_level.data
        )
        db.session.add(entry)
        db.session.commit()
        flash('Journal entry saved!', 'success')
        return redirect(url_for('journal.history'))
    
    # Set default values
    form.mood_score.data = 5
    form.energy_level.data = 5
    
    return render_template('journal/journal_form.html', form=form)

@journal_bp.route('/history')
@login_required
def history():
    """View journal history."""
    page = request.args.get('page', 1, type=int)
    entries = JournalEntry.query.filter_by(
        user_id=current_user.id
    ).order_by(JournalEntry.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('journal/history.html', entries=entries)

@journal_bp.route('/entry/<int:entry_id>')
@login_required
def view_entry(entry_id):
    """View specific journal entry."""
    entry = JournalEntry.query.filter_by(
        id=entry_id,
        user_id=current_user.id
    ).first_or_404()
    
    return render_template('journal/view_entry.html', entry=entry)

@journal_bp.route('/api/autosave', methods=['POST'])
@login_required
def autosave():
    """Auto-save journal entry draft."""
    data = request.json
    
    # Store in session or temporary storage
    # For MVP, we'll just return success
    return jsonify({
        'success': True,
        'saved_at': datetime.utcnow().strftime('%H:%M:%S')
    })