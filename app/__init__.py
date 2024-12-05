from flask import Flask
from flask_session import Session
import redis
from app.extensions import init_extensions
from config.logging_config import setup_logging
from app.api.v1 import bp as api_v1_bp
from config.config import Config

def create_app(config_class=Config):
    """Application factory setup"""
    app = Flask(__name__)
    
    app.config['METHODS'] = ['GET', 'POST', 'PUT','PATCH', 'DELETE','HEAD', 'OPTIONS']
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Setup logging first
    setup_logging(app)
    
    # Setup Redis for session
    try:
        redis_client = redis.from_url(app.config['REDIS_URL'])
        redis_client.ping()  # Test connection
        app.config['SESSION_REDIS'] = redis_client
        app.logger.info(f"Redis connected successfully at {app.config['REDIS_URL']}")
    except redis.ConnectionError as e:
        app.logger.error(f"Redis connection failed: {str(e)}")
        app.config['SESSION_TYPE'] = 'filesystem'
        app.logger.warning("Falling back to filesystem sessions")
    
    # Initialize Flask-Session before other extensions
    Session(app)
    
    # Initialize all extensions
    init_extensions(app)
    
    # Register blueprints
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    
    return app
