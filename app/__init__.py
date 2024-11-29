from flask import Flask
from config.config import Config
from app.extensions import init_extensions
import os

def create_app(config_class=Config):
    """Application factory setup"""

    app = Flask(__name__, template_folder=config_class.TEMPLATE_DIR)

    # Load configuration variables from the config module
    app.config.from_object(config_class)

    # Initialize logging
    from config.logging_config import setup_logging
    setup_logging(app)

    # Register API v1 blueprint
    from app.api.v1 import bp as api_v1_bp
    app.register_blueprint(api_v1_bp)

    # Initialize extensions
    init_extensions(app)

    return app
