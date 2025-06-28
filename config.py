# config.py - UPDATED with TestingConfig
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///storyforge.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Claude API Configuration
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    AI_SIMULATION_MODE = os.environ.get('AI_SIMULATION_MODE', 'false').lower() == 'true'
    DEFAULT_CLAUDE_MODEL = os.environ.get('DEFAULT_CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')
    
    # Rate limiting for Claude API
    CLAUDE_MAX_REQUESTS_PER_MINUTE = int(os.environ.get('CLAUDE_MAX_REQUESTS_PER_MINUTE', 50))
    CLAUDE_MAX_TOKENS_PER_REQUEST = int(os.environ.get('CLAUDE_MAX_TOKENS_PER_REQUEST', 4000))
    
    # Token limits by plan
    TOKEN_LIMITS = {
        'free': 1000,
        'pro': 10000,
        'enterprise': 50000
    }

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///storyforge_dev.db'

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    AI_SIMULATION_MODE = True
    PAYMENT_SIMULATION_MODE = True
    SERVER_NAME = 'localhost.localdomain'  # Required for URL generation in testing

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,  # Add testing configuration
    'default': DevelopmentConfig
}