from flask import Blueprint

api_v1_bp = Blueprint('api_v1_bp', __name__, url_prefix='/api/v1')

from app.controllers import book_controller