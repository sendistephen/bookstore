from flask import jsonify, current_app, request
from app.api.v1 import bp
from app.services.author_service import AuthorService
from utils.error_handler import bad_request_error, error_response, not_found, internal_server_error
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1.auth_utils import admin_required

@bp.route('/authors', methods=['GET'])
def list_authors():
    """List all authors"""
    try:
        authors, error = AuthorService.get_authors()
        if error:
            return error_response(500, 'Failed to retrieve authors', error)

        return jsonify({
            'status': 'success',
            'data': {
                'authors': authors,
                'total_authors': len(authors)
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error listing authors: {str(e)}")
        return error_response(500, 'Internal server error', str(e))

@bp.route('/authors/<author_id>', methods=['GET'])
def get_author(author_id):
    """Get an author by ID"""
    try:
        author, error = AuthorService.get_author_by_id(author_id)
        if error:
            return not_found(error)
            
        return jsonify({
            'status': 'success',
            'data': {
                'author': author
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting author: {str(e)}")
        return error_response(500, 'Internal server error', str(e))

@bp.route('/authors', methods=['POST'])
@jwt_required()
@admin_required()
def create_author():
    """Create a new author"""
    try:
        # Check JSON request
        payload = request.get_json()
        if not payload:
            return bad_request_error('Request must be JSON')

        # Check if author exists
        exists, error = AuthorService.check_author_exists(payload)
        if exists:
            return bad_request_error(error)
        
        # Create author
        author, error = AuthorService.create_author(payload)
        if error:
            return error_response(400, 'Author creation failed', error)

        return jsonify({
            'status': 'success',
            'message': 'Author created successfully',
            'data': {
                'author': author
            }
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error creating author: {str(e)}")
        return error_response(500, 'Internal server error', str(e))

@bp.route('/authors/<author_id>', methods=['PUT'])
@jwt_required()
@admin_required()
def update_author(author_id):
    """Update an author"""
    try:
        # Check JSON request
        payload = request.get_json()
        if not payload:
            return bad_request_error('Request must be JSON')

        # Update author
        author, error = AuthorService.update_author(author_id, payload)
        if error:
            return error_response(400, 'Author update failed', error)

        return jsonify({
            'status': 'success',
            'message': 'Author updated successfully',
            'data': {
                'author': author
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error updating author: {str(e)}")
        return error_response(500, 'Internal server error', str(e))

@bp.route('/authors/<author_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_author(author_id):
    """Delete an author"""
    try:
        # Delete author
        success, error = AuthorService.delete_author(author_id)
        if error:
            return error_response(400, 'Author deletion failed', error)

        return jsonify({
            'status': 'success',
            'message': 'Author deleted successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error deleting author: {str(e)}")
        return error_response(500, 'Internal server error', str(e))

@bp.route('/authors/<author_id>/books', methods=['GET'])
def get_books_by_author(author_id):
    """Get books by author"""
    try:
        books, error = AuthorService.get_books_by_author(author_id)
        if error:
            return not_found(error)
            
        return jsonify({
            'status': 'success',
            'data': {
                'books': books,
                'total_books': len(books)
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting books by author: {str(e)}")
        return error_response(500, 'Internal server error', str(e))
