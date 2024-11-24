from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# instantiate SQLAlchemy and Migrate
db: SQLAlchemy = SQLAlchemy()
migrate: Migrate = Migrate()
# TODO: initalize caching here..


def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
