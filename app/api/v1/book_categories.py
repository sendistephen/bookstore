from flask import jsonify, current_app, request
from marshmallow import ValidationError
from app.api.v1 import bp
from app.services.book_category_service import BookCategoryService
from app.schemas.book_category_schema import BookCategorySchema
from utils.error_handler import bad_request_error, error_response, not_found_error, internal_server_error
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1.auth_utils import admin_required


@bp.route('/book-categories', methods=['GET'])
def list_book_categories():
    """
    Retrieve list of book categories endpoint.
    
    Returns:
        200: List of book categories
        500: Server error
    """
    try:
        book_categories = BookCategoryService.get_all_book_categories()
        categories_list = [category.to_dict() for category in book_categories]
        
        return jsonify({
            'status': 'success',
            'data': {
                'book_categories': categories_list,
                'total_categories': len(categories_list)
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error listing book categories: {str(e)}")
        return error_response(500, str(e))


@bp.route('/book-categories', methods=['POST'])
@jwt_required()
@admin_required()
def create_book_category():
    """Create a new book category endpoint."""
    try:
        if not request.is_json:
            return bad_request_error('Request must be JSON')
            
        schema = BookCategorySchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return bad_request_error(err.messages)
            
        category = BookCategoryService.create_book_category(data)
        
        return jsonify({
            'status': 'success',
            'message': 'Book category created successfully',
            'data': schema.dump(category)
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error creating book category: {str(e)}")
        return error_response(500, str(e))


@bp.route('/book-categories/<category_id>', methods=['PUT'])
@jwt_required()
@admin_required()
def update_book_category(category_id):
    """Update an existing book category endpoint."""
    try:
        if not request.is_json:
            return bad_request_error('Request must be JSON')
            
        schema = BookCategorySchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return bad_request_error(err.messages)
            
        category = BookCategoryService.update_book_category(category_id, data)
        if not category:
            return not_found_error('Book category not found')
            
        return jsonify({
            'status': 'success',
            'message': 'Book category updated successfully',
            'data': schema.dump(category)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error updating book category: {str(e)}")
        return error_response(500, str(e))


@bp.route('/book-categories/<category_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_book_category(category_id):
    """Delete a book category endpoint."""
    try:
        if BookCategoryService.delete_book_category(category_id):
            return jsonify({
                'status': 'success',
                'message': 'Book category deleted successfully'
            }), 200
        else:
            return not_found_error('Book category not found')
            
    except Exception as e:
        current_app.logger.error(f"Error deleting book category: {str(e)}")
        return error_response(500, str(e))