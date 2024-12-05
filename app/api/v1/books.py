from flask import request, jsonify, current_app
from app.api.v1 import bp
from app.api.v1.auth import token_required, admin_required
from utils.error_handler import bad_request_error, internal_server_error
from app.services.book_service import BookService
from app.schemas.book_schema import BookSchema

@bp.route('/books', methods=['GET'])
def get_books():
    """
    Fetch books with advanced pagination and filtering
    
    Query Parameters:
    - page: Current page number (default: 1)
    - per_page: Number of items per page (default: 10)
    - sort_by: Field to sort by (default: 'created_at')
    - order: Sort order ('asc' or 'desc', default: 'desc')
    - search: Search term for title or description
    - category_id: Filter by category ID
    """
    try:
        # Extract query parameters with defaults
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        sort_by = request.args.get('sort_by', 'created_at')
        order = request.args.get('order', 'desc')
        
        # Handle search parameter
        search = request.args.get('search')
        if search is not None:
            # Remove surrounding quotes if present
            search = search.strip("'\"")
            # Ensure search is not an empty string
            search = search if search else None
        
        category_id = request.args.get('category_id')

        # Validate per_page (prevent excessive data retrieval)
        per_page = min(max(per_page, 1), 100)

        # Fetch books
        result = BookService.get_all_books(
            page=page, 
            per_page=per_page, 
            sort_by=sort_by, 
            order=order, 
            search=search, 
            category_id=category_id
        )

        if result is None:
            return internal_server_error('Error fetching books')

        return jsonify(result), 200

    except Exception as e:
        current_app.logger.error(f"Books retrieval error: {str(e)}")
        return internal_server_error('Error retrieving books')

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