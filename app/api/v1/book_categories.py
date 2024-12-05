from flask import jsonify, current_app, request
from marshmallow import ValidationError
from app.api.v1 import bp
from app.services.book_category_service import BookCategoryService
from app.schemas.book_category_schema import BookCategorySchema
from utils.error_handler import bad_request_error, error_response, not_found, internal_server_error
from app.api.v1.auth import token_required, admin_required


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
@token_required
@admin_required
def create_book_category(current_user):
    """
    Create a new book category endpoint.
    
    Authentication:
        Requires valid token and admin privileges
    
    Parameters:
        name: Name of the category
        description: Description of the category
    
    Returns:
        201: Category created successfully
        400: Validation error
        500: Server error
    """
    try:
        data = request.get_json()

        schema = BookCategorySchema()
        
        try:
            validated_data = schema.load(data)
        except ValidationError as e:
            return bad_request_error(e.messages)
            
        try:
            new_category = BookCategoryService.create_book_category(
                name=validated_data['name'], 
                description=validated_data.get('description')
            )
            
            return jsonify({
                'status': 'success',
                'message': 'Book category created successfully',
                'data': new_category.to_dict()
            }), 201

        except ValueError as ve:
            return bad_request_error(str(ve))

    except Exception as e:
        current_app.logger.error(f"Error creating book category: {str(e)}")

        return error_response(500, str(e))


@bp.route('/book-categories/<category_id>', methods=['PUT'])
@token_required
@admin_required
def update_book_category(current_user, category_id):
    """
    Update an existing book category endpoint.
    
    Authentication:
        Requires valid token and admin privileges
    
    Parameters:
        category_id: ID of the category to update
        name: Name of the category
        description: Description of the category
    
    Returns:
        200: Category updated successfully
        400: Validation error
        404: Category not found
        500: Server error
    """
    try:
        data = request.get_json(silent=True)
        
        if data is None:
            return jsonify({
                'status': 'error',
                'message': 'Invalid JSON or empty request body'
            }), 400

        schema = BookCategorySchema(context={'category_id': category_id})
        
        try:
            validated_data = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'status': 'error',
                'message': 'Validation failed',
                'errors': e.messages
            }), 400
        
        updated_category = BookCategoryService.replace_book_category(
            category_id,
            validated_data
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Book category updated successfully',
            'data': updated_category.to_dict()
        }), 200

    except ValueError as ve:
        return jsonify({
            'status': 'error',
            'message': str(ve)
        }), 404

    except Exception as e:
        current_app.logger.error(f"Unexpected error updating book category", exc_info=True)

        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred while processing the request'
        }), 500
        

@bp.route('/book-categories/<category_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_book_category(current_user, category_id):
    """
    Delete a book category endpoint.
    
    Authentication:
        Requires valid token and admin privileges
    
    Parameters:
        category_id: ID of the category to delete
    
    Returns:
        200: Category successfully deleted
        404: Category not found
        500: Server error
    """
    try:
        BookCategoryService.delete_book_category(category_id)
        
        return jsonify({
            'status': 'success',
            'message': 'Book category deleted successfully'
        }), 200
        
    except ValueError as ve:
        return not_found(str(ve))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting book category: {str(e)}")
        return internal_server_error(str(e))