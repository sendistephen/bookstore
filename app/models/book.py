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
    
    # Book cover image
    front_cover_url = db.Column(db.String(500))
    front_cover_public_id = db.Column(db.String(255))
    back_cover_url = db.Column(db.String(500))
    back_cover_public_id = db.Column(db.String(255))
    
    # Metadata
    publication_date = db.Column(db.Date)
    edition = db.Column(db.String(50), nullable=True)
    language = db.Column(db.String(50), nullable=True)
    
    # Relationships
    author_id = db.Column(db.String(36), db.ForeignKey('authors.id'), nullable=False)
    author = db.relationship('Author', back_populates='authored_books')
    
    category_id = db.Column(db.String(36), db.ForeignKey('book_categories.id'), nullable=False)
    category = db.relationship('BookCategory', backref='books')
    
    cart_items = db.relationship('CartItem', back_populates='book', lazy='dynamic')
    
    # Order relationship
    order_items = db.relationship('OrderItem', back_populates='book', lazy='dynamic')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)