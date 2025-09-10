from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from models import db, LifeAssessment
from sqlalchemy import desc

assessment_bp = Blueprint('assessment', __name__)

@assessment_bp.route('/')
@login_required
def assessment_home():
    """Display assessment home page with latest assessment info."""
    # Get user's latest assessment
    latest_assessment = current_user.life_assessments.order_by(desc(LifeAssessment.created_at)).first()
    
    # Calculate days since last assessment
    days_since_last = None
    if latest_assessment:
        delta = datetime.utcnow() - latest_assessment.created_at
        days_since_last = delta.days
    
    return render_template('assessment/assessment_home.html',
                         latest_assessment=latest_assessment,
                         days_since_last=days_since_last,
                         today=date.today())

@assessment_bp.route('/wheel-of-life', methods=['GET', 'POST'])
@login_required
def wheel_of_life():
    """Create new Wheel of Life assessment."""
    import sys
    print(f"### WHEEL_OF_LIFE FUNCTION CALLED - METHOD: {request.method} ###", file=sys.stderr, flush=True)
    if request.method == 'POST':
        print("=== WHEEL OF LIFE FORM SUBMISSION DEBUG ===")
        print(f"Form data received: {dict(request.form)}")
        print(f"Request method: {request.method}")
        print(f"Request URL: {request.url}")
        print(f"Current user: {current_user.id if current_user else 'None'}")
        
        # Get scores from form
        try:
            career_score = int(request.form.get('career_score', 5))
            health_score = int(request.form.get('health_score', 5))
            relationships_score = int(request.form.get('relationships_score', 5))
            finance_score = int(request.form.get('finance_score', 5))
            personal_growth_score = int(request.form.get('personal_growth_score', 5))
            fun_recreation_score = int(request.form.get('fun_recreation_score', 5))
            environment_score = int(request.form.get('environment_score', 5))
            purpose_score = int(request.form.get('purpose_score', 5))
            notes = request.form.get('notes', '').strip()
            
            print(f"Parsed scores: career={career_score}, health={health_score}, relationships={relationships_score}")
            print(f"More scores: finance={finance_score}, growth={personal_growth_score}, fun={fun_recreation_score}")
            print(f"Final scores: environment={environment_score}, purpose={purpose_score}")
            print(f"Notes: '{notes}'")
            
            # Validate scores (must be 1-10)
            scores = [career_score, health_score, relationships_score, finance_score,
                     personal_growth_score, fun_recreation_score, environment_score, purpose_score]
            
            print(f"All scores for validation: {scores}")
            
            for i, score in enumerate(scores):
                if score < 1 or score > 10:
                    print(f"VALIDATION FAILED: Score {i} = {score} is out of range!")
                    flash('All scores must be between 1 and 10.', 'error')
                    return redirect(url_for('assessment.wheel_of_life'))
            
            print("VALIDATION PASSED: All scores are valid!")
            
            # Create new assessment
            print("Creating LifeAssessment object...")
            assessment = LifeAssessment(
                user_id=current_user.id,
                career_score=career_score,
                health_score=health_score,
                relationships_score=relationships_score,
                finance_score=finance_score,
                personal_growth_score=personal_growth_score,
                fun_recreation_score=fun_recreation_score,
                environment_score=environment_score,
                purpose_score=purpose_score,
                notes=notes
            )
            print(f"Assessment object created: {assessment}")
            
            # Calculate balance score
            print("Calculating balance score...")
            balance_result = assessment.calculate_balance()
            print(f"Balance calculation result: {balance_result}")
            
            # Save to database
            print("Adding to database session...")
            db.session.add(assessment)
            print("Committing to database...")
            db.session.commit()
            print(f"SUCCESS: Assessment saved with ID: {assessment.id}")
            
            flash('Life assessment completed successfully! Review your results below.', 'success')
            return redirect(url_for('assessment.view_assessment', assessment_id=assessment.id))
            
        except (ValueError, TypeError) as e:
            print(f"VALIDATION ERROR: {e}")
            print(f"Form data: {dict(request.form)}")
            flash('Please enter valid scores for all areas.', 'error')
            return redirect(url_for('assessment.wheel_of_life'))
        except Exception as e:
            print(f"DATABASE/GENERAL ERROR: {e}")
            print(f"Error type: {type(e)}")
            print(f"Form data: {dict(request.form)}")
            flash('An error occurred while saving your assessment. Please try again.', 'error')
            db.session.rollback()
            return redirect(url_for('assessment.wheel_of_life'))
    
    # GET request - show form
    return render_template('assessment/wheel_of_life.html')

@assessment_bp.route('/<int:assessment_id>')
@login_required
def view_assessment(assessment_id):
    """View specific assessment results."""
    assessment = LifeAssessment.query.filter_by(
        id=assessment_id, 
        user_id=current_user.id
    ).first_or_404()
    
    # Get analysis data
    balance_data = assessment.calculate_balance()
    improvement_areas = assessment.get_improvement_areas()
    scores_dict = assessment.get_scores_dict()
    
    return render_template('assessment/results.html',
                         assessment=assessment,
                         balance_data=balance_data,
                         improvement_areas=improvement_areas,
                         scores_dict=scores_dict,
                         today=date.today())

@assessment_bp.route('/history')
@login_required
def assessment_history():
    """View all user's assessments."""
    assessments = current_user.life_assessments.order_by(desc(LifeAssessment.created_at)).all()
    
    return render_template('assessment/history.html',
                         assessments=assessments,
                         today=date.today())

@assessment_bp.route('/api/latest')
@login_required
def get_latest_assessment():
    """API endpoint for latest assessment data (for dashboard widget)."""
    latest_assessment = current_user.life_assessments.order_by(desc(LifeAssessment.created_at)).first()
    
    if not latest_assessment:
        return jsonify({'assessment': None})
    
    # Calculate days since last assessment
    delta = datetime.utcnow() - latest_assessment.created_at
    days_since = delta.days
    
    # Get balance data
    balance_data = latest_assessment.calculate_balance()
    scores_dict = latest_assessment.get_scores_dict()
    improvement_areas = latest_assessment.get_improvement_areas()
    
    return jsonify({
        'assessment': {
            'id': latest_assessment.id,
            'overall_balance': balance_data['overall_balance'],
            'created_at': latest_assessment.created_at.isoformat(),
            'days_since': days_since,
            'scores': scores_dict,
            'improvement_areas': improvement_areas[:3],  # Top 3 areas needing attention
            'notes': latest_assessment.notes
        }
    })

@assessment_bp.route('/<int:assessment_id>/delete', methods=['POST'])
@login_required
def delete_assessment(assessment_id):
    """Delete an assessment."""
    assessment = LifeAssessment.query.filter_by(
        id=assessment_id, 
        user_id=current_user.id
    ).first_or_404()
    
    try:
        db.session.delete(assessment)
        db.session.commit()
        flash('Assessment deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting assessment. Please try again.', 'error')
    
    return redirect(url_for('assessment.assessment_history'))