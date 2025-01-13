from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate

# Optional imports
try:
    from flask_jwt_extended import JWTManager
except ImportError:
    JWTManager = None

try:
    from flask_mail import Mail
except ImportError:
    Mail = None

# Initialize extensions
db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
mail = Mail() if Mail else None

def init_extensions(app):
    """Initialize all extensions for the Flask application"""
    # Initialize core extensions
    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    
    # Conditionally initialize Mail if imported
    if mail:
        mail.init_app(app)
    
    # Conditionally initialize JWT if imported
    if JWTManager:
        JWTManager(app)

    return app
