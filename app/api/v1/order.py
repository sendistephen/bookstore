from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api.v1 import bp
from app.api.v1.auth_utils import admin_required
from app.models.order import Order, OrderStatus
from app.services.order_service import OrderService
from app.schemas.order_schema import OrderSchema, OrderQuerySchema
from app.services.cart_service import CartService
from app.models.user import User
from marshmallow import ValidationError

from datetime import datetime

# ---------CUSTOMER ORDER ROUTES---------


@bp.route('/orders/create', methods=['POST'])
@jwt_required()
def create_order():
    """
    Create a new order for the authenticated user.

    Request JSON should contain:
    - payment_method: Payment method for the order
    - cart_id: ID of the cart to create order from
    - billing_info (optional): Billing information for the order
      Required fields: name, email, phone, country
    """
    user_id = get_jwt_identity()

    try:
        # Validate payment method input
        schema = OrderSchema()

        # Get request payload
        payload = request.json or {}

        # If billing_info is not in request, return an error
        if 'billing_info' not in payload:
            return jsonify({
                "error": "Billing information is required",
                "details": {
                    "required_fields": [
                        {"name": "Full Name (2-100 characters)"},
                        {"email": "Valid email address"},
                        {"phone": "Phone number (10-20 characters)"},
                        {"country": "Country name (2-100 characters)"}
                    ]
                }
            }), 400

        # Load and validate payload
        payload = schema.load(payload)

        # Set default status if not provided
        payload['status'] = payload.get('status', OrderStatus.PENDING.value)

        # Log the incoming request data
        current_app.logger.info(f"Request JSON: {payload}")

        # Get cart items for the user
        cart_items = CartService.get_user_cart_items_by_cart_id(
            user_id=user_id,
            cart_id=payload['cart_id']
        )

        if not cart_items:
            current_app.logger.error(
                f"Cart is empty or does not belong to the user {user_id}")
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
    - payment_method: Payment method (stripe, mobile money)
    """
    user_id = get_jwt_identity()

    try:
        # Log the incoming request data
        current_app.logger.info(f"Request JSON: {request.json}")

        # Validate input
        schema = OrderSchema(only=('order_id', 'payment_method'), partial=True)
        payload = schema.load(request.json)

        # Retrieve the order
        order = Order.query.filter_by(
            id=payload['order_id'], user_id=user_id).first()

        if not order:
            return jsonify({"error": "Order not found"}), 404

        # Convert total amount from UGX to USD for Stripe
        from app.services.currency_service import CurrencyService

        # Convert total amount to USD
        total_amount_usd = CurrencyService.convert_currency(
            amount=order.total_amount,
            base_currency='UGX',
            target_currency='USD'
        )

        # Round to 2 decimal places for Stripe
        total_amount_usd = round(total_amount_usd, 2)

        current_app.logger.info(
            f"Order total: {order.total_amount} UGX = {total_amount_usd} USD"
        )

        # Generate a mock transaction ID for testing
        import uuid
        mock_transaction_id = f'stripe_txn_{str(uuid.uuid4())}'

        # Process payment
        order = OrderService.process_payment(
            order_id=order.id,
            payment_transaction_id=mock_transaction_id
        )

        current_app.logger.info(f"Order processed successfully: {order.id}")

        return jsonify({
            "message": "Order processed successfully",
            "order_id": order.id,
            "status": order.status.value,
            "total_amount_usd": total_amount_usd,
            "transaction_id": mock_transaction_id
        }), 200

    except ValidationError as err:
        current_app.logger.error(f"ValidationError: {err}")
        return jsonify({"error": err.messages}), 400
    except ValueError as e:
        current_app.logger.error(f"ValueError: {str(e)}")
        return jsonify({"error": str(e)}), 400


@bp.route('/orders/cancel/<order_id>', methods=['PUT'])
@jwt_required()
def cancel_order(order_id):
    """
    Cancel a specific order for the authenticated user.

    URL parameter:
    - order_id: ID of the order to cancel
    """
    user_id = get_jwt_identity()

    # Validate order_id is a non-empty string and looks like a valid UUID
    if not order_id or not isinstance(order_id, str):
        current_app.logger.error(f"Invalid order_id: {order_id}")
        return jsonify({
            "status": "error",
            "message": "Invalid order ID"
        }), 400

    try:
        # Log the incoming request
        current_app.logger.info(f"Attempting to cancel order {order_id} by user {user_id}")

        cancelled_order = OrderService.cancel_order(order_id=order_id, user_id=user_id)

        current_app.logger.info(f"Order cancelled successfully: {cancelled_order.id}")
        
        return jsonify({
            "message": "Order cancelled successfully",
            "order_id": cancelled_order.id,
            "status": cancelled_order.status.value
        }), 200

    except ValueError as e:
        current_app.logger.error(f"ValueError: {str(e)}")
        return jsonify({"error": str(e)}), 400


@bp.route('/orders/my-orders', methods=['GET'])
@jwt_required()
def get_customer_orders():
    """
    Retrieve user's order history

    Query Parameters:
    - page: Page number for pagination (default: 1)
    - per_page: Number of orders per page (default: 10)
    """
    user_id = get_jwt_identity()

    # Get query parameters with defaults
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    try:
        # Retrieve customers's order history
        orders, total_orders, error = OrderService.get_customer_orders(
            user_id=user_id,
            page=page,
            per_page=per_page
        )
        # Check if there are any errors
        if error:
            current_app.logger.error(
                f"Error retrieving customer orders: {error}")
            return jsonify({
                "status": "error",
                "message": error}), 400

        return jsonify({
            "status": "success",
            "data": {
                "orders": orders,
                "total_orders": total_orders,
                "page": page,
                "per_page": per_page
            }
        }), 200

    except ValueError as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ---------ADMIN ORDER ROUTES---------
@bp.route('/admin/orders/<order_id>/status', methods=['PUT'])
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
@admin_required()
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
        start_date = datetime.fromisoformat(
            start_date_str) if start_date_str else None
        end_date = datetime.fromisoformat(
            end_date_str) if end_date_str else None

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


@bp.route('/admin/orders', methods=['GET'])
@jwt_required()
@admin_required()
def get_all_orders_by_admin():
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
