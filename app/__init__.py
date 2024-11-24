from flask import Flask
from config.config import Config
from app.extensions import init_extensions
from app.blueprints.api_v1 import api_v1_bp
from config.logging_config import setup_logging


def create_app(config_class=Config):
    """Application factory setup"""

    app = Flask(__name__)

    # Load configuration variables from the config module
    app.config.from_object(config_class)

    # Initialize logging
    setup_logging(app)

    # Register blueprints
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')

    # Initialize extensions
    init_extensions(app)

    return app
