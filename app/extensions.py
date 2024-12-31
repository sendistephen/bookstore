from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate

# Optional imports
try:
    from flask_jwt_extended import JWTManager
except ImportError:
    JWTManager = None

try:
    from flask_session import Session
except ImportError:
    Session = None

# Initialize extensions
db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()

def init_extensions(app):
    """Initialize all extensions for the Flask application"""
    # Initialize core extensions
    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    
    # Conditionally initialize JWT if imported
    if JWTManager:
        jwt = JWTManager(app)
    
    # Conditionally initialize Session if imported
    if Session and app.config.get('SESSION_TYPE'):
        Session(app)
