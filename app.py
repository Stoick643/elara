import os
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager
from flask_migrate import Migrate
from models import db, User
from config import config

def create_app(config_name=None):
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)

    # Initialize Flask-Migrate for database migrations
    migrate = Migrate(app, db)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes import auth_bp, dashboard_bp, journal_bp
    from routes.goals import goals_bp
    from routes.habits import habits_bp
    from routes.calendar import calendar_bp
    from routes.avatar import avatar_bp
    from routes.chat import chat_bp
    from routes.discovery import discovery_bp
    from routes.tasks import tasks_bp
    from routes.assessment import assessment_bp
    from routes.onboarding import onboarding_bp
    from routes.settings import settings_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(journal_bp, url_prefix='/journal')
    app.register_blueprint(goals_bp, url_prefix='/goals')
    app.register_blueprint(habits_bp, url_prefix='/habits')
    app.register_blueprint(calendar_bp, url_prefix='/calendar')
    app.register_blueprint(avatar_bp, url_prefix='/avatar')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(discovery_bp, url_prefix='/discovery')
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    app.register_blueprint(assessment_bp, url_prefix='/assessment')
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(settings_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create default user if not exists
        if User.query.count() == 0:
            default_user = User(
                username=app.config['DEFAULT_USERNAME'],
                avatar_personality='friend'  # Set default personality for testing
            )
            default_user.set_password(app.config['DEFAULT_PASSWORD'])
            db.session.add(default_user)
            db.session.commit()
            print(f"Created default user: {app.config['DEFAULT_USERNAME']} with Friend personality")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Root route
    @app.route('/')
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.dashboard'))
        else:
            return render_template('landing.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)