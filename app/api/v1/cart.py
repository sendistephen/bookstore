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

@bp.route('/cart/clear', methods=['DELETE'])
@jwt_required()
def clear_cart():
    """
    Clear all items from the user's cart
    
    Returns:
          - Cart details on success
          - Error message on failure
    """
    try:
        # Get current user from JWT token
        current_user_id = get_jwt_identity()
        
        # Clear cart
        cart, error = CartService.clear_cart(current_user_id)
        
        # Handle errors
        if error:
            return bad_request_error(error)
            
        return jsonify({
            'status': 'success',
            'message': 'Cart cleared successfully',
            'data': {
                'cart_cleared': True,
                'cart_id': cart.id,
                'total_items': cart.total_items,
                'total_price': cart.total_price
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error clearing cart: {str(e)}")
        return internal_server_error('Failed to clear cart')

@bp.route('/cart/remove', methods=['DELETE'])
@jwt_required()
def remove_cart_item():
    """
    Remove a specific item from the user's cart
    Reduces quantity by 1, or removes the entire item if quantity is 1
    
    Request JSON:
    {
        "book_id": "string"
    }
    Returns:
          - Cart details on success
          - Error message on failure
    """
    try:
        # Validate JSON request
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
        
        # Get current user from JWT token
        current_user_id = get_jwt_identity()
        
        # Remove cart item
        cart, removed_item_info, error = CartService.remove_cart_item(current_user_id, book_id)
        
        # Handle errors
        if error:
            return bad_request_error(error)
            
        # Prepare response message
        if removed_item_info['removed_completely']:
            message = f"'{removed_item_info['book_title']}' completely removed from cart"
        else:
            message = f"Quantity of '{removed_item_info['book_title']}' reduced. " \
                      f"Remaining quantity: {removed_item_info['remaining_quantity']}"
        
        return jsonify({
            'status': 'success',
            'message': message,
            'data': {
                'cart_id': cart.id,
                'total_items': cart.total_items,
                'total_price': cart.total_price,
                'removed_item': {
                    'book_id': removed_item_info['book_id'],
                    'book_title': removed_item_info['book_title'],
                    'previous_quantity': removed_item_info['previous_quantity'],
                    'removed_completely': removed_item_info['removed_completely']
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error removing cart item: {str(e)}")
        return internal_server_error('Failed to remove cart item')