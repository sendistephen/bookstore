from app.api.v1 import bp
from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.cart_service import CartService
from app.services.order_service import OrderService
from app.schemas.order_schema import OrderSchema, OrderQuerySchema
from app.models.user import User

from datetime import datetime, timedelta

@bp.route('/orders/create', methods=['POST'])
@jwt_required()
def create_order():
    """
    Create a new order for the authenticated user.
    
    Request JSON should contain:
    - payment_method: Payment method for the order
    - cart_id: ID of the cart to create order from
    """
    user_id = get_jwt_identity()
    
    try:
        # Validate payment method input
        schema = OrderSchema()
        payload = schema.load(request.json)
        
        # Get cart items for the user
        cart_items = CartService.get_user_cart_items_by_cart_id(
            user_id=user_id, 
            cart_id=payload['cart_id']
        )
        
        if not cart_items:
            return jsonify({"error": "Cart is empty or does not belong to the user"}), 400
        
        # Prepare cart items for order creation
        order_items = [
            {
                'book_id': item.book_id,
                'quantity': item.quantity,
            } for item in cart_items
        ]
        
        # Create preliminary order
        order = OrderService.create_order(
            user_id=user_id, 
            cart_items=order_items, 
            payment_method=payload['payment_method']
        )
        
        return jsonify({
            "message": "Order created successfully",
            "order_id": order.id,
            "total_amount": order.total_amount
        }), 201
    
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    except ValueError as e:
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
        # Validate input
        schema = OrderSchema(only=('order_id', 'transaction_id'), partial=True)
        payload = schema.load(request.json)
        
        # Process payment
        order = OrderService.process_payment(
            order_id=payload['order_id'], 
            payment_transaction_id=payload.get('transaction_id')
        )
        
        return jsonify({
            "message": "Order processed successfully",
            "order_id": order.id,
            "status": order.status.value
        }), 200
    
    except ValueError as e:
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
        # Validate query parameters
        query_schema = OrderQuerySchema()
        query_params = query_schema.load(request.args, unknown='exclude')
        
        # Get orders with optional status filter
        status = query_params.get('status')
        orders = OrderService.get_user_orders(
            user_id=user_id, 
            status=status
        )
        
        return jsonify({
            "orders": [
                {
                    "id": order.id,
                    "total_amount": order.total_amount,
                    "status": order.status.value,
                    "created_at": order.created_at.isoformat(),
                    "payment_method": order.payment_method.value,
                    "items": [
                        {
                            "book_id": item.book_id,
                            "quantity": item.quantity,
                            "price": item.price
                        } for item in order.order_items
                    ]
                } for order in orders
            ]
        }), 200
    
    except ValidationError as err:
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
    
    try:
        # Extract query parameters with defaults
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        sort_by = request.args.get('sort_by', 'created_at')
        order = request.args.get('order', 'desc')

        # Filtering parameters
        status = request.args.get('status')
        payment_method = request.args.get('payment_method')
        date_filter = request.args.get('date_filter')

        # Validate per_page
        per_page = min(max(per_page, 1), 100)

        # Fetch orders
        orders, total, error = OrderService.get_all_user_orders(
            user_id=user_id,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            order=order,
            status=status,
            payment_method=payment_method,
            date_filter=date_filter
        )
        
        if error:
            return jsonify({
                'status': 'error',
                'message': error
            }), 400

        return jsonify({
            'status': 'success',
            'data': {
                'orders': [
                    {
                        "id": order.id,
                        "total_amount": order.total_amount,
                        "status": order.status.value,
                        "created_at": order.created_at.isoformat(),
                        "payment_method": order.payment_method.value,
                        "items": [
                            {
                                "book_id": item.book_id,
                                "quantity": item.quantity,
                                "price": item.price
                            } for item in order.order_items
                        ]
                    } for order in orders
                ],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error fetching orders: {str(e)}")
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
        order = OrderService.cancel_order(order_id)
        
        return jsonify({
            "message": "Order cancelled successfully",
            "order_id": order.id,
            "status": order.status.value
        }), 200
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/vendor/orders/<order_id>/status', methods=['PATCH'])
@jwt_required()
def update_vendor_order_status(order_id):
    """
    Update the status of an order for a vendor

    Requires:
    - Authenticated vendor
    - Order must contain books from the vendor
    - Status must be a valid transition

    Allowed Status Transitions:
    - PENDING -> PROCESSING or CANCELLED
    - PROCESSING -> SHIPPED or CANCELLED
    - SHIPPED -> DELIVERED

    Request JSON:
    {
        "status": "processing"  # New status for the order
    }
    """
    # Get the current user's identity
    user_id = get_jwt_identity()

    # Verify the user is a vendor
    vendor = User.query.filter_by(id=user_id).first()
    if not vendor:
        return jsonify({
            'status': 'error',
            'message': 'Only vendors can update order status'
        }), 403

    # Parse the request
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Status is required'
        }), 400

    # Update order status
    updated_order, error = OrderService.update_order_status_for_vendor(
        order_id=order_id,
        vendor_id=vendor.id,
        new_status=data['status']
    )

    # Handle potential errors
    if error:
        return jsonify({
            'status': 'error',
            'message': error
        }), 400

    # Return updated order details
    return jsonify({
        'status': 'success',
        'data': {
            'order_id': updated_order.id,
            'new_status': updated_order.status.value,
            'updated_at': updated_order.updated_at.isoformat()
        }
    }), 200

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
        return jsonify({
            'status': 'error',
            'message': 'Access denied.'
        }), 403

    try:
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

        return jsonify({
            'status': 'success',
            'data': analytics
        }), 200

    except ValueError as ve:
        return jsonify({
            'status': 'error',
            'message': str(ve)
        }), 400
    except Exception as e:
        current_app.logger.error(f"Sales analytics error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate sales analytics'
        }), 500
