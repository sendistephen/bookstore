from app.extensions import db
import uuid
from datetime import datetime

class BookCategory(db.Model):
    """Book category model for storing book categories"""
    
    __tablename__ = 'book_categories'
    
    # Use a longer UUID string
    id = db.Column(db.String(36), unique=True, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Ensure name is unique
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert the BookCategory object to a dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }