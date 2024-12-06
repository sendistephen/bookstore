from app.extensions import db
import uuid
from datetime import datetime

class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
     
    #  Pricing and inventory
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False)
    
    # Metadata
    publication_date = db.Column(db.Date, nullable=True)
    edition = db.Column(db.String(50), nullable=True)
    language = db.Column(db.String(50), nullable=True)
    
    # Relationships
    category_id = db.Column(db.String(36), db.ForeignKey('book_categories.id'), nullable=False)
    category = db.relationship('BookCategory', backref=db.backref('books', lazy=True))
    
    #Relationship to configuration
    author_id = db.Column(db.String(36), db.ForeignKey('authors.id'), nullable=True)
    author = db.relationship('Author', 
        back_populates='authored_books',  
        foreign_keys=[author_id]
    )
    
    # publisher_id = db.Column(db.String(36), db.ForeignKey('publisher.id'), nullable=False)
    # publisher = db.relationship('Publisher', back_populates='books')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)