from flask import jsonify, current_app
from app.api.v1 import bp
from app.services.book_category_service import BookCategoryService
from utils.error_handler import error_response
from app.api.v1.auth import token_required

@bp.route('/book-categories', methods=['GET'])
@token_required
def list_book_categories(current_user=None):
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
            'book_categories': categories_list,
            'total_categories': len(categories_list)
        }), 200
    except Exception as e:
        # Log the error for server-side tracking
        current_app.logger.error(f"Error listing book categories: {str(e)}")
        
        # Return a generic error response
        return error_response(str(e), 500)