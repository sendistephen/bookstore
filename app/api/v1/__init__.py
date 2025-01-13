from flask import Blueprint

bp = Blueprint('bookstore_api', __name__)

# Import routes after creating blueprint
from app.api.v1 import (
    auth, 
    users, 
    books, 
    book_categories, 
    authors, 
    cart, 
    book_image, 
    order, 
    payment, 
    currency
)
