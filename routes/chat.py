"""
Chat routes for AI Coach interactions.
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, ChatHistory
from services.ai_coach import AICoach
from datetime import datetime
import markdown

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/chat')
@login_required
def chat_interface():
    """Display the chat interface with AI coach."""
    # Get conversation history
    ai_coach = AICoach()
    history = ai_coach.get_conversation_history(current_user.id, limit=50)
    
    # Process markdown for assistant messages
    for msg in history:
        if msg['role'] == 'assistant':
            msg['content'] = markdown.markdown(msg['content'], extensions=['nl2br'])
    
    # Get user's avatar personality for UI styling
    personality = current_user.avatar_personality or 'friend'
    
    return render_template('avatar/chat.html',
                         personality=personality,
                         conversation_history=history)


@chat_bp.route('/api/chat/send', methods=['POST'])
@login_required
def send_message():
    """Process user message and return AI response."""
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    if len(message) > 2000:
        return jsonify({'error': 'Message too long (max 2000 characters)'}), 400
    
    try:
        # Initialize AI coach
        ai_coach = AICoach()
        
        # Generate response
        ai_response, tokens_used = ai_coach.generate_response(
            current_user.id,
            message,
            include_context=True
        )
        
        # Save conversation
        ai_coach.save_conversation(
            current_user.id,
            message,
            ai_response,
            tokens_used
        )
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'timestamp': datetime.utcnow().isoformat(),
            'personality': current_user.avatar_personality
        })
        
    except ValueError as e:
        # API key not configured
        return jsonify({
            'error': str(e),
            'help': 'Please configure your LLM API keys in the .env file'
        }), 500
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to generate response',
            'details': str(e)
        }), 500


@chat_bp.route('/api/chat/history')
@login_required
def get_history():
    """Get conversation history for current user."""
    limit = request.args.get('limit', 20, type=int)
    
    ai_coach = AICoach()
    history = ai_coach.get_conversation_history(current_user.id, limit=limit)
    
    return jsonify({
        'success': True,
        'messages': history,
        'count': len(history)
    })


@chat_bp.route('/api/chat/clear', methods=['POST'])
@login_required
def clear_history():
    """Clear conversation history for current user."""
    # Delete all chat history for user
    ChatHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    flash('Conversation history cleared', 'success')
    return jsonify({'success': True})