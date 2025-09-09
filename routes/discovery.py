"""
Discovery routes for values assessment and vision building.
Level A of the 3-level hierarchy: Discover who you are and what matters to you.
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, CoreValueAssessment, VisionStatement, Value
from services.ai_coach import AICoach
from datetime import datetime
import json

discovery_bp = Blueprint('discovery', __name__)

# Core values list for assessment (based on Schwartz Theory and positive psychology)
CORE_VALUES_LIST = [
    # Achievement & Power
    'Achievement', 'Success', 'Excellence', 'Recognition', 'Leadership', 'Power', 'Authority', 'Influence',
    
    # Security & Stability  
    'Security', 'Stability', 'Safety', 'Order', 'Tradition', 'Loyalty', 'Reliability', 'Predictability',
    
    # Relationships & Connection
    'Family', 'Friendship', 'Love', 'Community', 'Belonging', 'Connection', 'Intimacy', 'Service',
    
    # Growth & Learning
    'Growth', 'Learning', 'Curiosity', 'Knowledge', 'Wisdom', 'Innovation', 'Creativity', 'Discovery',
    
    # Freedom & Independence
    'Freedom', 'Independence', 'Autonomy', 'Choice', 'Adventure', 'Spontaneity', 'Variety', 'Travel',
    
    # Meaning & Purpose
    'Purpose', 'Meaning', 'Spirituality', 'Faith', 'Contribution', 'Legacy', 'Impact', 'Justice',
    
    # Health & Well-being
    'Health', 'Fitness', 'Peace', 'Balance', 'Serenity', 'Mindfulness', 'Joy', 'Happiness',
    
    # Authenticity & Expression
    'Authenticity', 'Integrity', 'Honesty', 'Truth', 'Expression', 'Uniqueness', 'Individuality', 'Art',
    
    # Financial & Material
    'Wealth', 'Financial Security', 'Luxury', 'Comfort', 'Resources', 'Abundance', 'Generosity'
]


@discovery_bp.route('/discovery')
@login_required
def discovery_home():
    """Discovery home page showing progress and next steps."""
    progress = current_user.get_discovery_progress()
    current_assessment = current_user.get_current_values_assessment()
    current_vision = current_user.get_current_vision()
    
    return render_template('discovery/discovery_home.html',
                         progress=progress,
                         current_assessment=current_assessment,
                         current_vision=current_vision)


@discovery_bp.route('/discovery/values')
@login_required
def values_assessment():
    """Start values discovery assessment."""
    # Check if user already has current assessment
    existing_assessment = current_user.get_current_values_assessment()
    
    return render_template('discovery/values_assessment.html',
                         values_list=CORE_VALUES_LIST,
                         existing_assessment=existing_assessment)


@discovery_bp.route('/discovery/values/card-sort')
@login_required
def values_card_sort():
    """Interactive card sorting for values discovery."""
    return render_template('discovery/values_card_sort.html',
                         values_list=CORE_VALUES_LIST)


@discovery_bp.route('/api/discovery/values/save', methods=['POST'])
@login_required
def save_values_assessment():
    """Save completed values assessment."""
    data = request.get_json()
    
    # Validate required data
    top_values = data.get('top_values', [])
    if not top_values or len(top_values) < 3:
        return jsonify({'error': 'Please select at least 3 core values'}), 400
    
    # Archive any existing current assessment
    existing = current_user.get_current_values_assessment()
    if existing:
        existing.is_current = False
        db.session.commit()
    
    # Create new assessment
    assessment = CoreValueAssessment(
        user_id=current_user.id,
        assessment_type=data.get('assessment_type', 'card_sort'),
        top_values=top_values,
        values_definition=data.get('values_definition', {}),
        values_stories=data.get('values_stories', {}),
        daily_expressions=data.get('daily_expressions', {}),
        insights_gained=data.get('insights_gained', ''),
        alignment_assessment=data.get('alignment_assessment', None)
    )
    
    db.session.add(assessment)
    db.session.commit()
    
    # Create/update Value records in the database
    assessment.create_values_records()
    
    flash('Values assessment completed successfully!', 'success')
    return jsonify({
        'success': True,
        'assessment_id': assessment.id,
        'redirect_url': url_for('discovery.values_reflection', assessment_id=assessment.id)
    })


@discovery_bp.route('/discovery/values/<int:assessment_id>/reflection')
@login_required
def values_reflection(assessment_id):
    """Reflection page after values assessment."""
    assessment = CoreValueAssessment.query.filter_by(
        id=assessment_id,
        user_id=current_user.id
    ).first_or_404()
    
    return render_template('discovery/values_reflection.html',
                         assessment=assessment)


@discovery_bp.route('/discovery/vision')
@login_required
def vision_builder():
    """Start vision statement creation."""
    # Check if user has completed values assessment
    values_assessment = current_user.get_current_values_assessment()
    if not values_assessment:
        flash('Please complete your values assessment first', 'warning')
        return redirect(url_for('discovery.values_assessment'))
    
    existing_vision = current_user.get_current_vision()
    
    return render_template('discovery/vision_builder.html',
                         values_assessment=values_assessment,
                         existing_vision=existing_vision)


@discovery_bp.route('/api/discovery/vision/save', methods=['POST'])
@login_required  
def save_vision_statement():
    """Save completed vision statement."""
    data = request.get_json()
    
    # Validate required data
    vision_statement = data.get('vision_statement', '').strip()
    if not vision_statement:
        return jsonify({'error': 'Vision statement is required'}), 400
    
    # Archive any existing current vision
    existing = current_user.get_current_vision()
    version = 1
    if existing:
        existing.is_current = False
        version = existing.version + 1
        db.session.commit()
    
    # Create new vision
    vision = VisionStatement(
        user_id=current_user.id,
        version=version,
        vision_statement=vision_statement,
        mission_statement=data.get('mission_statement', ''),
        core_purpose=data.get('core_purpose', ''),
        legacy_intention=data.get('legacy_intention', ''),
        life_themes=data.get('life_themes', []),
        peak_experiences=data.get('peak_experiences', ''),
        future_self_visualization=data.get('future_self_visualization', ''),
        confidence_level=data.get('confidence_level', None)
    )
    
    db.session.add(vision)
    db.session.commit()
    
    flash('Vision statement created successfully!', 'success')
    return jsonify({
        'success': True,
        'vision_id': vision.id,
        'redirect_url': url_for('discovery.discovery_complete')
    })


@discovery_bp.route('/discovery/complete')
@login_required
def discovery_complete():
    """Completion page showing user's discovered values and vision."""
    if not current_user.has_completed_discovery():
        flash('Please complete both values assessment and vision creation', 'warning')
        return redirect(url_for('discovery.discovery_home'))
    
    values_assessment = current_user.get_current_values_assessment()
    vision_statement = current_user.get_current_vision()
    orphaned_tasks_count = current_user.get_orphaned_tasks_count()
    
    return render_template('discovery/discovery_complete.html',
                         values_assessment=values_assessment,
                         vision_statement=vision_statement,
                         orphaned_tasks_count=orphaned_tasks_count)


@discovery_bp.route('/api/discovery/ai-guidance', methods=['POST'])
@login_required
def get_ai_guidance():
    """Get AI guidance for discovery process."""
    data = request.get_json()
    guidance_type = data.get('type')  # 'values', 'vision', 'reflection'
    context = data.get('context', {})
    
    try:
        ai_coach = AICoach()
        
        if guidance_type == 'values':
            response = ai_coach.guide_values_discovery(current_user.id, context)
        elif guidance_type == 'vision':
            response = ai_coach.guide_vision_creation(current_user.id, context)
        elif guidance_type == 'reflection':
            response = ai_coach.provide_discovery_reflection(current_user.id, context)
        else:
            return jsonify({'error': 'Invalid guidance type'}), 400
        
        return jsonify({
            'success': True,
            'guidance': response
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to generate AI guidance',
            'details': str(e)
        }), 500