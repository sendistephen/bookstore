from flask import Flask
from cachelib import FileSystemCache
import redis
from flask_session import Session

from app.extensions import init_extensions
from config.logging_config import setup_logging
from config.config import Config
from app.api.v1 import bp as api_v1_bp

def create_app(config_class=Config):
    """Application factory setup"""
    app = Flask(__name__)
        
    # Load configuration
    app.config.from_object(config_class)
    
    # Setup logging first
    setup_logging(app)
    
    # Setup Redis for session
    try:
        redis_client = redis.from_url(app.config['REDIS_URL']) if app.config.get('REDIS_URL') else None
        if redis_client:
            redis_client.ping()  # Test connection
            app.config['SESSION_REDIS'] = redis_client
            app.config['SESSION_TYPE'] = 'redis'
            app.logger.info(f"Redis connected successfully at {app.config['REDIS_URL']}")
    except (redis.ConnectionError, KeyError) as e:
        app.logger.error(f"Redis connection failed: {str(e)}")
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
    
    # Initialize Session
    session = Session(app)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    
    return app
