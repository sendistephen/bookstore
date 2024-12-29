from flask import request, jsonify, current_app
from app.api.v1 import bp
from app.api.v1.auth_utils import admin_required
from utils.error_handler import bad_request_error, internal_server_error, not_found
from app.services.book_service import BookService
from flask_jwt_extended import jwt_required, get_jwt_identity

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
            search = search.strip("'\"")
            search = search if search else None

        category_id = request.args.get('category_id')

        # Validate per_page
        per_page = min(max(per_page, 1), 100)

        # Fetch books
        books, total, error = BookService.get_all_books(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            order=order,
            search=search,
            category_id=category_id
        )
        
        if error:
            return internal_server_error(error)

        return jsonify({
            'status': 'success',
            'data': {
                'books': books,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error fetching books: {str(e)}")
        return internal_server_error('Failed to fetch books')

@bp.route('/books/<book_id>', methods=['GET'])
def get_book(book_id):
    """Get a book by ID"""
    try:
        book, error = BookService.get_book_by_id(book_id)
        if error:
            return not_found(error)

        return jsonify({
            'status': 'success',
            'data': {
                'book': book
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error fetching book: {str(e)}")
        return internal_server_error('Failed to fetch book')

@bp.route('/books', methods=['POST'])
@jwt_required()
@admin_required()
def create_book():
    """Create a new book"""
    try:
        if not request.is_json:
            return bad_request_error('Request must be JSON')

        data = request.get_json()
        book, error = BookService.create_book(data)
        
        if error:
            return bad_request_error(error)

        return jsonify({
            'status': 'success',
            'message': 'Book created successfully',
            'data': {
                'book': book
            }
        }), 201

    except Exception as e:
        current_app.logger.error(f"Error creating book: {str(e)}")
        return internal_server_error('Failed to create book')

@bp.route('/books/<book_id>', methods=['PUT'])
@jwt_required()
@admin_required()
def update_book(book_id):
    """Update a book"""
    try:
        if not request.is_json:
            return bad_request_error('Request must be JSON')

        data = request.get_json()
        book, error = BookService.update_book(book_id, data)
        
        if error:
            return bad_request_error(error)

        return jsonify({
            'status': 'success',
            'message': 'Book updated successfully',
            'data': {
                'book': book
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error updating book: {str(e)}")
        return internal_server_error('Failed to update book')

@bp.route('/books/<book_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_book(book_id):
    """Delete a book"""
    try:
        success, error = BookService.delete_book(book_id)
        
        if error:
            return not_found(error)

        return jsonify({
            'status': 'success',
            'message': 'Book deleted successfully'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error deleting book: {str(e)}")
        return internal_server_error('Failed to delete book')