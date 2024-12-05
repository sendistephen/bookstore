from flask import request, jsonify, current_app
from app.api.v1 import bp
from app.api.v1.auth import token_required, admin_required
from utils.error_handler import bad_request_error, internal_server_error
from app.services.book_service import BookService
from app.schemas.book_schema import BookSchema

@bp.route('/books', methods=['POST'])
@token_required
@admin_required
def create_book(current_user):
    """Create a new book endpoint"""
    try:
        # Check JSON request
        if not request.is_json:
            return bad_request_error('Request must be JSON')
        
        # Get request data
        data = request.get_json()
        
        # Check if book exists
        exists, reason = BookService.check_book_exists(data)
        if exists:
            return bad_request_error(reason)
        
        # Create book
        book, error = BookService.create_book(data)
        if error:
            return bad_request_error(error)
        
        return jsonify({
            'message': 'Book created successfully',
            'data': book
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Book creation error: {str(e)}")
        return internal_server_error('Error creating book')