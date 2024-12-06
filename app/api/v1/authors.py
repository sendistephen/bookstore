from flask import jsonify, current_app, request
from marshmallow import ValidationError
from app.api.v1 import bp
from app.services.author_service import AuthorService
from app.schemas.author_schema import AuthorSchema
from utils.error_handler import bad_request_error, error_response, not_found, internal_server_error
from app.api.v1.auth import token_required, admin_required

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
    pass

@bp.route('/authors', methods=['POST'])
@token_required
@admin_required
def create_author(current_user):
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
            'status':'success',
            'message': 'Author created successfully',
            'data': author
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Author creation error: {str(e)}")
        return internal_server_error('Error creating author')

@bp.route('/authors/<author_id>', methods=['PUT', 'PATCH'])
@token_required
@admin_required
def update_author(current_user, author_id):
    """Update an author"""
    pass

@bp.route('/authors/<author_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_author(current_user, author_id):
    """Delete an author"""
    pass

@bp.route('/authors/<author_id>/books', methods=['GET'])
def get_books_by_author(author_id):
    """Get books by author"""
    pass
