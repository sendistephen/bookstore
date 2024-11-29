from app.extensions import db
import uuid


class Role(db.Model):
    """Role model for storing user roles"""
    __tablename__ = 'roles'

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(
            uuid.uuid4()))
    name = db.Column(db.String(50), unique=True, nullable=False)

    # relationships
    users = db.relationship(
        'User',
        secondary='user_roles',
        back_populates='roles',
        lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.name}>'
