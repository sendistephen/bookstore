from flask import jsonify, current_app, request
from marshmallow import ValidationError
from app.api.v1 import bp
from app.services.book_category_service import BookCategoryService
from app.schemas.book_category_schema import BookCategorySchema
from utils.error_handler import bad_request_error, error_response
from app.api.v1.auth import token_required, admin_required


@bp.route('/book-categories', methods=['GET'])
def list_book_categories():
    """
    Retrieve list of book categories

    Returns:
        JSON response with list of book categories
    """
    try:
        # Fetch all book categories
        book_categories = BookCategoryService.get_all_book_categories()

        # Convert categories to dictionary for JSON serialization
        categories_list = [category.to_dict() for category in book_categories]

        return jsonify({
            'status': 'success',
            'data': {
                'book_categories': categories_list,
                'total_categories': len(categories_list)
            }
        }), 200
    except Exception as e:
        # Log the error for server-side tracking
        current_app.logger.error(f"Error listing book categories: {str(e)}")

        # Return a generic error response
        return error_response(500, str(e))


@bp.route('/book-categories', methods=['POST'])
@token_required
@admin_required
def create_book_category(current_user):
    """
    Create a new book category

    Args:
        current_user (User): The currently authenticated user

    Returns:
        JSON response with the created book category
    """
    try:
        # Extract category data from the request payload
        data = request.get_json()

        # Create a schema instance for validation
        schema = BookCategorySchema()
        
        try:
            # Validate the input data against the schema
            validated_data = schema.load(data)
        except ValidationError as e:
            # Return validation errors
            return bad_request_error(e.messages)
            
        try:
            # Create a new book category
            new_category = BookCategoryService.create_book_category(
                name=validated_data['name'], 
                description=validated_data.get('description')
            )
            
            # Return the created category as a JSON response
            return jsonify({
                'status': 'success',
                'message': 'Book category created successfully',
                'data': new_category.to_dict()
            }), 201

        except ValueError as ve:
            return bad_request_error(str(ve))

    except Exception as e:
        # Log the error for server-side tracking
        current_app.logger.error(f"Error creating book category: {str(e)}")

        # Return a generic error response
        return error_response(500, str(e))

@bp.route('/book-categories/<category_id>', methods=['PUT'])
@token_required
@admin_required
def update_book_category(current_user, category_id):
    """
    Update an existing book category
    
    Args:
        current_user (User): The currently authenticated user
        category_id (str): The ID of the category to update
    
    Returns:
        JSON response with the updated book category
    """
    try:
        # Extract category data from the request payload
        data = request.get_json(silent=True)
        
        # Validate that data is not None
        if data is None:
            return jsonify({
                'status': 'error',
                'message': 'Invalid JSON or empty request body'
            }), 400

        # Create a schema instance for validation
        schema = BookCategorySchema(context={'category_id': category_id})
        
        # Validate the input data against the schema
        try:
            validated_data = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'status': 'error',
                'message': 'Validation failed',
                'errors': e.messages
            }), 400
        
        # Perform the update
        updated_category = BookCategoryService.replace_book_category(
            category_id,
            validated_data
        )
        
        # Return the updated category
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
        # Log the full traceback for server-side tracking
        current_app.logger.error(f"Unexpected error updating book category", exc_info=True)

        # Return a generic error response
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred while processing the request'
        }), 500