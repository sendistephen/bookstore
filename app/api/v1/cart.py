from flask import request, jsonify, current_app
from app.api.v1 import bp
from utils.error_handler import bad_request_error, internal_server_error, not_found_error
from app.services.cart_service import CartService
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.schemas import CartSchema

cart_schema = CartSchema()

@bp.route('/cart', methods=['GET'])
@jwt_required()
def view_cart():
    """
    Get the current user's active cart
    
    Returns:
        - Cart details with items on success
        - Error message on failure
    """
    try:
        # Get current user from JWT token
        current_user_id = get_jwt_identity()
        
        # Get active cart
        cart, error = CartService.get_active_cart(current_user_id)
        if error:
            return not_found_error(error)
            
        return jsonify({
            'status': 'success',
            'message': 'Cart retrieved successfully',
            'data': {
                'cart': cart_schema.dump(cart)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving cart: {str(e)}")
        return internal_server_error('Failed to retrieve cart')

@bp.route('/cart/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    """
    Add item to user's cart
    
    Request JSON:
    {
        "book_id": "string",
        "quantity": "integer"
    }
    Returns:
          - Cart details on success
          - Error message on failure
    """
    try:
        if not request.is_json:
            return bad_request_error('Request must be JSON')
        
        # Get request data
        data = request.get_json()
        if not data:
            return bad_request_error('Request data is empty')
        
        # Validate required fields
        book_id = data.get('book_id')
        if not book_id:
            return bad_request_error('Book ID is required')
        
        quantity = data.get('quantity')
        if not quantity:
            return bad_request_error('Quantity is required')
        
        # Validate qty type and value
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return bad_request_error('Quantity must be greater than 0')
        except ValueError:
            return bad_request_error('Quantity must be a valid integer')
        
        # Get current user from JWT token
        current_user_id = get_jwt_identity()
        
        # Add to cart 
        cart, error = CartService.add_to_cart(current_user_id, book_id, quantity)
        if error:
            return bad_request_error(error)
            
        return jsonify({
            'status': 'success',
            'message': 'Item added to cart successfully',
            'data': {
                'cart': cart_schema.dump(cart)
            }
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error adding item to cart: {str(e)}")
        return internal_server_error('Failed to add item to cart')
    
@bp.route('/cart/update', methods=['PUT'])
@jwt_required()
def update_cart():
    """
    Update user's cart
    
    Request JSON:
    {
        "book_id": "string",
        "quantity": "integer"
    }
    Returns:
          - Cart details on success
          - Error message on failure
    """
    try:
        if not request.is_json:
            return bad_request_error('Request must be JSON')
        
        # Get request data
        data = request.get_json()
        if not data:
            return bad_request_error('Request data is empty')
        
        # Validate required fields
        book_id = data.get('book_id')
        if not book_id:
            return bad_request_error('Book ID is required')
        
        quantity = data.get('quantity')
        if quantity is None:
            return bad_request_error('Quantity is required')
        
        # Validate qty type and value
        try:
            quantity = int(quantity)
        except ValueError:
            return bad_request_error('Quantity must be a valid integer')
        
        # Get current user from JWT token
        current_user_id = get_jwt_identity()
        
        # Update cart item
        cart, error = CartService.update_cart_item(current_user_id, book_id, quantity)
        
        # Handle empty cart scenario
        if cart and cart.status == 'empty':
            return jsonify({
                'status': 'success',
                'message': 'Cart is now empty',
                'data': {
                    'cart': cart_schema.dump(cart)
                }
            }), 200
        
        # Handle other errors
        if error:
            return bad_request_error(error)
            
        return jsonify({
            'status': 'success',
            'message': 'Cart item updated successfully',
            'data': {
                'cart': cart_schema.dump(cart)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error updating cart item: {str(e)}")
        return internal_server_error('Failed to update cart item')