from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from app.services.email_service import mail

# instantiate SQLAlchemy and Migrate
db: SQLAlchemy = SQLAlchemy()
migrate: Migrate = Migrate()
ma = Marshmallow()

# TODO: initalize caching here..

def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    mail.init_app(app)
