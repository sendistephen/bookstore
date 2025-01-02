from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api.v1 import bp
from app.api.v1.auth_utils import admin_required
from app.models.order import Order, OrderStatus
from app.services.order_service import OrderService
from app.schemas.order_schema import OrderSchema, OrderQuerySchema
from app.services.cart_service import CartService
from app.models.user import User

from datetime import datetime

@bp.route('/orders/create', methods=['POST'])
@jwt_required()
def create_order():
    """
    Create a new order for the authenticated user.
    
    Request JSON should contain:
    - payment_method: Payment method for the order
    - cart_id: ID of the cart to create order from
    - billing_info: Billing information for the order
    - shipping_info (optional): Shipping information if different from billing
    """
    user_id = get_jwt_identity()
    
    try:
        # Validate payment method input
        schema = OrderSchema()
        payload = schema.load(request.json)
        
        # Log the incoming request data
        current_app.logger.info(f"Request JSON: {request.json}")
        
        # Get cart items for the user
        cart_items = CartService.get_user_cart_items_by_cart_id(
            user_id=user_id, 
            cart_id=payload['cart_id']
        )
        
        if not cart_items:
            current_app.logger.error(f"Cart is empty or does not belong to the user {user_id}")
            return jsonify({"error": "Cart is empty or does not belong to the user"}), 400
        
        # Prepare cart items for order creation
        order_items = list([
            {
                'book_id': item.book_id,
                'quantity': item.quantity,
            } for item in cart_items
        ])
        
        # Create order with billing and shipping details
        order = OrderService.create_order(
            user_id=user_id, 
            cart_items=order_items, 
            payment_method=payload['payment_method'],
            billing_info=payload['billing_info'],
            shipping_info=payload.get('shipping_info')  # Optional
        )
        
        current_app.logger.info(f"Order created successfully: {order.id}")
        
        return jsonify({
            "message": "Order created successfully",
            "order_id": order.id,
            "total_amount": order.total_amount
        }), 201
    
    except ValidationError as err:
        current_app.logger.error(f"ValidationError: {err}")
        return jsonify({"error": err.messages}), 400
    except ValueError as e:
        current_app.logger.error(f"ValueError: {str(e)}")
        return jsonify({"error": str(e)}), 400

@bp.route('/orders/process-payment', methods=['POST'])
@jwt_required()
def process_order_payment():
    """
    Process payment for a specific order.
    
    Request JSON should contain:
    - order_id: ID of the order to process
    - payment_method: Payment method (e.g., stripe, mobile money)
    """
    user_id = get_jwt_identity()
    
    try:
        # Log the incoming request data
        current_app.logger.info(f"Request JSON: {request.json}")
        
        # Validate input
        schema = OrderSchema(only=('order_id', 'transaction_id'), partial=True)
        payload = schema.load(request.json)
        
        current_app.logger.info(f"Validated payload: {payload}")
        
        # Process payment
        order = OrderService.process_payment(
            order_id=payload['order_id'], 
            payment_transaction_id=payload.get('transaction_id')
        )
        
        current_app.logger.info(f"Order processed successfully: {order.id}")
        
        return jsonify({
            "message": "Order processed successfully",
            "order_id": order.id,
            "status": order.status.value
        }), 200
    
    except ValueError as e:
        current_app.logger.error(f"ValueError: {str(e)}")
        return jsonify({"error": str(e)}), 400

@bp.route('/orders', methods=['GET'])
@jwt_required()
def get_user_orders():
    """
    Retrieve orders for the authenticated user.
    
    Optional query parameters:
    - page: Page number for pagination
    - per_page: Number of orders per page
    - status: Filter orders by status
    """
    user_id = get_jwt_identity()
    
    try:
        # Log the incoming request query parameters
        current_app.logger.info(f"Request query parameters: {request.args}")
        
        # Validate query parameters
        query_schema = OrderQuerySchema()
        query_params = query_schema.load(request.args, unknown='exclude')
        
        current_app.logger.info(f"Validated query parameters: {query_params}")
        
        # Get orders with optional status filter
        status = query_params.get('status')
        orders = OrderService.get_user_orders(
            user_id=user_id, 
            status=status
        )
        
        current_app.logger.info(f"Retrieved orders for user {user_id}")
        
        return jsonify({
            "orders": list([
                {
                    "id": order.id,
                    "total_amount": order.total_amount,
                    "status": order.status.value,
                    "created_at": order.created_at.isoformat(),
                    "payment_method": order.payment_method.value,
                    "items": list([
                        {
                            "book_id": item.book_id,
                            "quantity": item.quantity,
                            "price": item.price
                        } for item in order.order_items
                    ])
                } for order in orders
            ])
        }), 200
    
    except ValidationError as err:
        current_app.logger.error(f"ValidationError: {err}")
        return jsonify({"error": err.messages}), 400

@bp.route('/orders/all', methods=['GET'])
@jwt_required()
def get_all_user_orders():
    """
    Retrieve all orders for the authenticated user with advanced pagination and filtering

    Query Parameters:
    - page: Current page number (default: 1)
    - per_page: Number of items per page (default: 10)
    - sort_by: Field to sort by (default: 'created_at')
    - order: Sort order ('asc' or 'desc', default: 'desc')
    
    Filtering Parameters:
    - status: Filter by order status (e.g., 'pending', 'processing', 'paid')
    - payment_method: Filter by payment method (e.g., 'stripe', 'mtn_mobile_money')
    - date_filter: Filter by date range (options: 'today', 'yesterday', 'today_and_yesterday', 
                   '3days', '7days', '30days')
    """
    user_id = get_jwt_identity()
    
    # Log the incoming request query parameters
    current_app.logger.info(f"Request query parameters: {request.args}")
    
    # Get query parameters
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)
    sort_by = request.args.get('sort_by', default='created_at')
    order = request.args.get('order', default='desc')
    
    # Filtering parameters
    status = request.args.get('status')
    payment_method = request.args.get('payment_method')
    date_filter = request.args.get('date_filter')
    
    try:
        # Fetch orders with advanced filtering
        orders, total_orders, error = OrderService.get_all_user_orders(
            user_id=user_id,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            order=order,
            status=status,
            payment_method=payment_method,
            date_filter=date_filter
        )
        
        # If there's an error, return it
        if error:
            current_app.logger.error(f"Error fetching orders: {error}")
            return jsonify({
                'status': 'error',
                'message': error
            }), 400
        
        # Serialize orders
        orders_data = list([
            {
                'id': order.id,
                'total_amount': order.total_amount,
                'status': order.status.value,
                'payment_method': order.payment_method.value,
                'created_at': order.created_at.isoformat(),
                'order_items': list([
                    {
                        'book_id': item.book_id,
                        'quantity': item.quantity,
                        'price': item.price
                    } for item in order.order_items
                ])
            } for order in orders
        ])
        
        current_app.logger.info(f"Retrieved orders for user {user_id}")
        
        return jsonify({
            'status': 'success',
            'data': {
                'orders': orders_data,
                'total_orders': total_orders,
                'page': page,
                'per_page': per_page
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error fetching orders: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch orders'
        }), 500

@bp.route('/orders/cancel/<int:order_id>', methods=['PUT'])
@jwt_required()
def cancel_order(order_id):
    """
    Cancel a specific order for the authenticated user.
    
    URL parameter:
    - order_id: ID of the order to cancel
    """
    user_id = get_jwt_identity()
    
    try:
        # Log the incoming request
        current_app.logger.info(f"Attempting to cancel order {order_id} by user {user_id}")
        
        order = OrderService.cancel_order(order_id)
        
        current_app.logger.info(f"Order cancelled successfully: {order.id}")
        
        return jsonify({
            "message": "Order cancelled successfully",
            "order_id": order.id,
            "status": order.status.value
        }), 200
    
    except ValueError as e:
        current_app.logger.error(f"ValueError: {str(e)}")
        return jsonify({"error": str(e)}), 400

@bp.route('/orders/<order_id>/status', methods=['PUT'])
@jwt_required()
@admin_required()
def update_order_status(order_id):
    """
    Update order status by admin
    """
    admin_id = get_jwt_identity()
    data = request.json
    
    # Validate status is provided
    status = data.get('status', '').upper()
    if not status:
        return jsonify({"error": "Status is required"}), 400
    
    try:
        # Use service method to update order status
        order = OrderService.admin_update_order_status(
            admin_id=admin_id,
            order_id=order_id,
            new_status=status
        )
        
        return jsonify({
            "message": "Order status updated",
            "order_id": order.id,
            "new_status": order.status.value
        }), 200
    
    except ValueError as e:
        return jsonify({
            "error": str(e), 
            "valid_statuses": [s.name for s in OrderStatus]
        }), 400
    except Exception as e:
        current_app.logger.error(f"Status update error: {str(e)}")
        return jsonify({"error": "Update failed"}), 500

@bp.route('/admin/sales/analytics', methods=['GET'])
@jwt_required()
def get_sales_analytics():
    """
    Retrieve comprehensive sales analytics for the admin

    Query Parameters:
    - start_date: Start date for analytics (ISO format)
    - end_date: End date for analytics (ISO format)
    - status: Filter by specific order status
    - period: Predefined time period ('week', 'month', 'year')

    Supported Filters:
    - Specific date range: Provide start_date and end_date
    - Predefined periods: Use 'period' parameter
    - Status: Filter by order status (e.g., 'pending', 'processing', 'paid')

    Example Queries:
    1. Specific date range: 
       `/admin/sales/analytics?start_date=2025-01-01T00:00:00&end_date=2025-01-31T23:59:59`
    2. Predefined period: 
       `/admin/sales/analytics?period=month`
    3. Combined filter: 
       `/admin/sales/analytics?period=week&status=paid`
    """
    # Verify admin access
    user_id = get_jwt_identity()
    
    # TODO: Implement proper admin role check
    # For now, just ensure the user exists
    user = User.query.filter_by(id=user_id).first()
    if not user:
        current_app.logger.error(f"Access denied for user {user_id}")
        return jsonify({
            'status': 'error',
            'message': 'Access denied.'
        }), 403

    try:
        # Log the incoming request query parameters
        current_app.logger.info(f"Request query parameters: {request.args}")
        
        # Parse date parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        status = request.args.get('status')
        period = request.args.get('period')

        # Convert date strings to datetime objects
        start_date = datetime.fromisoformat(start_date_str) if start_date_str else None
        end_date = datetime.fromisoformat(end_date_str) if end_date_str else None

        # Validate period
        if period and period not in ['week', 'month', 'year']:
            current_app.logger.error(f"Invalid period: {period}")
            return jsonify({
                'status': 'error',
                'message': "Invalid period. Must be 'week', 'month', or 'year'."
            }), 400

        # Fetch sales analytics
        analytics = OrderService.get_sales_analytics(
            start_date=start_date,
            end_date=end_date,
            status=status,
            period=period
        )

        current_app.logger.info(f"Retrieved sales analytics")
        
        return jsonify({
            'status': 'success',
            'data': analytics
        }), 200

    except ValueError as ve:
        current_app.logger.error(f"ValueError: {str(ve)}")
        return jsonify({
            'status': 'error',
            'message': str(ve)
        }), 400
    except Exception as e:
        current_app.logger.error(f"Sales analytics error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate sales analytics'
        }), 500

@bp.route('/orders/history', methods=['GET'])
@jwt_required()
def get_user_order_history():
    """
    Retrieve user's order history
    
    Query Parameters:
    - page: Page number for pagination (default: 1)
    - per_page: Number of orders per page (default: 10)
    """
    user_id = get_jwt_identity()
    
    # Get query parameters with defaults
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    try:
        # Retrieve user's order history
        orders, total_orders = OrderService.get_user_order_history(
            user_id=user_id,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            "orders": orders,
            "total_orders": total_orders,
            "page": page,
            "per_page": per_page
        }), 200
    
    except ValueError as e:
        return jsonify({
            "error": str(e)
        }), 400

@bp.route('/admin/orders', methods=['GET'])
@jwt_required()
@admin_required()
def get_all_orders():
    """
    Retrieve all orders for admin with advanced filtering
    
    Query Parameters:
    - page: Page number for pagination (default: 1)
    - per_page: Number of orders per page (default: 10)
    - sort_by: Field to sort by (default: 'created_at')
    - order: Sort order ('asc' or 'desc', default: 'desc')
    - status: Filter by order status
    - start_date: Filter orders from this date (ISO format)
    - end_date: Filter orders up to this date (ISO format)
    """
    # Get query parameters with defaults
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    sort_by = request.args.get('sort_by', 'created_at')
    order = request.args.get('order', 'desc')
    status = request.args.get('status')
    
    # Parse dates if provided
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    start_date = None
    if start_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str)
        except ValueError:
            return jsonify({"error": "Invalid start_date format. Use ISO format."}), 400
    
    end_date = None
    if end_date_str:
        try:
            end_date = datetime.fromisoformat(end_date_str)
        except ValueError:
            return jsonify({"error": "Invalid end_date format. Use ISO format."}), 400
    
    try:
        # Retrieve orders for admin
        orders, total_orders, error = OrderService.get_all_orders_admin(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            order=order,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
        
        if error:
            return jsonify({"error": error}), 400
        
        return jsonify({
            "orders": orders,
            "total_orders": total_orders,
            "page": page,
            "per_page": per_page
        }), 200
    
    except ValueError as e:
        return jsonify({
            "error": str(e)
        }), 400
