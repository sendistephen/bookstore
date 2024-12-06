from app.extensions import db
from datetime import datetime
import uuid

class Author(db.Model):
    """
    Author model representing book authors

    Attributes:
        - id (str): Unique identifier for the author
        - name (str): Author's full name
        - biography (str): Author's biography
        - authored_books (list): Relationship to the books written by the author
        - created_at (datetime): Creation timestamp
        - updated_at (datetime): Last update timestamp
    """
    __tablename__ = 'authors'
    
    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    biography = db.Column(db.Text, nullable=True)

    authored_books = db.relationship(
        'Book', 
        back_populates='author', 
        cascade='save-update, merge',  # Less aggressive deletion strategy
        lazy='dynamic'  # Allows for more flexible querying
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        """String representation of the Author"""
        return f'<Author {self.name}>'