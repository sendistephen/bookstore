from flask import Blueprint

bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Import routes after creating blueprint to avoid circular imports
from app.api.v1 import auth  
from app.api.v1 import users, books, book_categories