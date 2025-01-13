from app.api.v1 import bp
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.payment_service import StripePaymentService
from app.services.order_service import OrderService
from app.models.order import Order, OrderStatus
from app.models.book import Book
from app.extensions import db
from app.services.currency_service import CurrencyService


def convert_ugx_to_usd(amount_ugx: float) -> float:
    """
    Convert Ugandan Shillings (UGX) to US Dollars (USD)

    Args:
        amount_ugx (float): Amount in Ugandan Shillings

    Returns:
        float: Equivalent amount in US Dollars
    """
    try:
        return CurrencyService.convert_currency(
            amount=amount_ugx,
            base_currency='UGX',
            target_currency='USD'
        )
    except Exception as e:
        current_app.logger.error(f"Currency conversion error: {e}")
        # Fallback to hardcoded rate if API call fails
        return amount_ugx * CurrencyService._FALLBACK_RATES.get(('UGX', 'USD'), 0.00027)


@bp.route('/payments/stripe/create-intent', methods=['POST'])
@jwt_required()
def create_payment_intent():
    """
    Create a Stripe Payment Intent for an order

    Expects JSON with:
    - order_id: Unique order identifier
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    order_id = data.get('order_id')

    if not order_id:
        return jsonify({"error": "Order ID is required"}), 400

    try:
        # Fetch order with more flexible status checking
        order = Order.query.filter(
            Order.id == order_id,
            Order.user_id == user_id,
            Order.status.in_([OrderStatus.PENDING, OrderStatus.PROCESSING])
        ).first()

        if not order:
            return jsonify({
                "error": "Order not found or not eligible for payment",
                "details": "Order may be already paid, cancelled, or does not exist"
            }), 404

        # Detailed logging of order details
        current_app.logger.info(
            f"Processing payment for Order {order_id}: "
            f"Total Amount UGX: {order.total_amount}, "
            f"User ID: {user_id}"
        )

        # Convert total amount to USD
        total_amount_usd = convert_ugx_to_usd(order.total_amount)

        # Ensure minimum Stripe payment amount
        MIN_STRIPE_AMOUNT = 0.50  # $0.50 USD
        if total_amount_usd < MIN_STRIPE_AMOUNT:
            # Force minimum amount for very small orders
            total_amount_usd = MIN_STRIPE_AMOUNT
            current_app.logger.warning(
                f"Order total {total_amount_usd} is below Stripe minimum. "
                f"Forcing to minimum {MIN_STRIPE_AMOUNT} USD"
            )

        # Detailed logging of conversion
        current_app.logger.info(
            f"Payment Amount Conversion: "
            f"{order.total_amount} UGX = {total_amount_usd} USD"
        )

        # Initialize Stripe Payment Service
        payment_service = StripePaymentService()

        # Create Payment Intent
        success, payment_details = payment_service.initialize_payment(
            amount=total_amount_usd,
            currency='usd',
            order_id=order_id
        )

        if not success:
            current_app.logger.error(
                f"Payment Intent Creation Failed: "
                f"Order {order_id}, Amount {total_amount_usd} USD, "
                f"Error: {payment_details.get('error', 'Unknown error')}"
            )
            return jsonify({
                "error": "Failed to create payment intent",
                "details": payment_details.get('error', 'Unknown error')
            }), 500

        # Optional: Update order status to processing
        order.status = OrderStatus.PROCESSING
        db.session.commit()

        return jsonify({
            'checkout_session_id': payment_details['client_secret'],
            'payment_intent_id': payment_details['payment_intent_id'],
            'total_amount_usd': total_amount_usd,
            'total_amount_ugx': order.total_amount,
            'order_details': {
                'order_id': order_id,
                'items_count': len(order.order_items),
                'items': [
                    {
                        'book_title': Book.query.get(item.book_id).title,
                        'quantity': item.quantity,
                        'price_ugx': item.price,
                        'price_usd': convert_ugx_to_usd(item.price)
                    } for item in order.order_items
                ]
            }
        }), 200

    except Exception as e:
        current_app.logger.error(
            f"Payment intent creation error for Order {order_id}: {str(e)}",
            exc_info=True
        )
        return jsonify({
            "error": "Failed to create payment intent",
            "details": str(e)
        }), 500


@bp.route('/payments/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """
    Stripe Webhook Endpoint for Payment Events
    """
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        payment_service = StripePaymentService()
        event = payment_service.handle_webhook(payload, sig_header)

        # Process different event types
        if event['event_type'] == 'payment_success':
            order_id = event['order_id']
            order = Order.query.filter_by(id=order_id).first()

            if order:
                # Update order status
                order.status = OrderStatus.PAID
                db.session.commit()

                # Optional: Trigger additional processing
                OrderService.process_paid_order(order)

        elif event['event_type'] == 'payment_failed':
            order_id = event['order_id']
            order = Order.query.filter_by(id=order_id).first()

            if order:
                # Update order status
                order.status = OrderStatus.CANCELLED
                db.session.commit()

        return jsonify({"status": "success"}), 200

    except Exception as e:
        current_app.logger.error(f"Stripe Webhook Error: {str(e)}")
        return jsonify({"error": "Webhook processing failed"}), 400
