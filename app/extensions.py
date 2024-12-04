from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from app.services.email_service import mail

# instantiate SQLAlchemy and Migrate
db: SQLAlchemy = SQLAlchemy()
migrate: Migrate = Migrate()
ma = Marshmallow()

def init_extensions(app):
    """
    Intialize all extensions for the Flask application
    
    Args:
        app (Flask): The Flask application instance
    """
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Initialize Marshmallow
    ma.init_app(app)
    
    # Initialize Flask-Migrate
    migrate.init_app(app, db)
    
    # Initialize Mail
    mail.init_app(app)
