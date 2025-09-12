import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    database_url = os.environ.get('DATABASE_URL') or 'sqlite:///data/elara.db'
    # Fix for Render PostgreSQL URLs (they use postgres:// instead of postgresql://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Login
    SESSION_COOKIE_NAME = 'elara_session'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds
    
    # WTForms
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens
    
    # User defaults (for single-user setup)
    DEFAULT_USERNAME = os.environ.get('DEFAULT_USERNAME', 'me')
    DEFAULT_PASSWORD = os.environ.get('DEFAULT_PASSWORD', 'elara2024')
    
    # Application settings
    ITEMS_PER_PAGE = 10
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # LLM Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
    MOONSHOT_API_KEY = os.environ.get('MOONSHOT_API_KEY')
    LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'gemini')
    LLM_MAX_TOKENS = int(os.environ.get('LLM_MAX_TOKENS', '2048'))
    LLM_TEMPERATURE = float(os.environ.get('LLM_TEMPERATURE', '0.7'))
    LLM_RATE_LIMIT = int(os.environ.get('LLM_RATE_LIMIT', '10'))

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # Ensure SECRET_KEY is set in production
    if not os.environ.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY must be set in production environment")

# Dictionary to easily access configurations
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}