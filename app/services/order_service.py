from typing import List, Dict, Optional, Any, Tuple
from app.extensions import db
from app.models.order import Order, OrderItem, OrderStatus, PaymentMethod
from app.models.book import Book
from app.models.user import User
from app.services.notification_service import NotificationService
from datetime import datetime, timedelta
import math
from flask import current_app

class OrderService:
    @staticmethod
    def create_order(
        user_id: str, 
        cart_items: List[Dict[str, Any]], 
        payment_method: PaymentMethod
    ) -> Order:
        """
        Create a new order from cart items
        
        Args:
            user_id (str): ID of the user placing the order
            cart_items (List[Dict]): List of items to order
            payment_method (PaymentMethod): Selected payment method
        
        Returns:
            Order: Created order object
        
        Raises:
            ValueError: If cart is empty or items are invalid
        """
        # Calculate total amount and validate items
        total_amount = 0
        order_items = []

        for item in cart_items:
            book = db.session.query(Book).get(item['book_id'])
            if not book:
                raise ValueError(f"Book with ID {item['book_id']} not found")
            
            # Validate quantity against available stock
            if book.stock_quantity < item['quantity']:
                raise ValueError(f"Insufficient stock for book {book.title}")

            # Create order item
            order_item = OrderItem(
                book_id=book.id,
                quantity=item['quantity'],
                price=book.price * item['quantity']
            )
            order_items.append(order_item)
            total_amount += order_item.price

            # Update book stock
            book.stock_quantity -= item['quantity']

        # Create order
        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            status=OrderStatus.PENDING,
            payment_method=payment_method,
            order_items=order_items
        )

        # Save to database
        db.session.add(order)
        db.session.commit()
        db.session.refresh(order)

        return order

    @staticmethod
    def get_user_orders(
        user_id: str, 
        status: Optional[str] = None
    ) -> List[Order]:
        """
        Retrieve orders for a specific user
        
        Args:
            user_id (str): ID of the user
            status (Optional[str]): Filter by order status
        
        Returns:
            List[Order]: List of user's orders
        
        Raises:
            ValueError: If an invalid status is provided
        """
        query = db.session.query(Order).filter(Order.user_id == user_id)
        
        if status:
            try:
                # Convert string status to enum
                status_enum = OrderStatus(status.lower())
                query = query.filter(Order.status == status_enum)
            except ValueError:
                # Provide a clear error message with valid status options
                valid_statuses = [s.value for s in OrderStatus]
                raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        return query.order_by(Order.created_at.desc()).all()

    @staticmethod
    def _get_date_range(date_filter: Optional[str]) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Convert date filter string to start and end datetime
        
        Supported filters:
        - 'today': Orders from the start of today
        - 'yesterday': Orders from yesterday
        - 'today_and_yesterday': Orders from yesterday and today
        - '3days': Orders from 3 days ago
        - '7days': Orders from 7 days ago
        - '30days': Orders from 30 days ago
        
        Args:
            date_filter (Optional[str]): Date range filter
        
        Returns:
            Tuple of (start_date, end_date)
        """
        if not date_filter:
            return None, None
        
        # Use the current time from the system
        now = datetime.now()
        
        # Reset time to start of day
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        date_ranges = {
            'today': (today_start, now),
            'yesterday': (
                today_start - timedelta(days=1), 
                today_start
            ),
            'today_and_yesterday': (
                today_start - timedelta(days=1), 
                now
            ),
            '3days': (
                today_start - timedelta(days=3), 
                now
            ),
            '7days': (
                today_start - timedelta(days=7), 
                now
            ),
            '30days': (
                today_start - timedelta(days=30), 
                now
            )
        }
        
        # Validate and return date range
        if date_filter.lower() not in date_ranges:
            raise ValueError(f"Invalid date filter. Must be one of: {', '.join(date_ranges.keys())}")
        
        return date_ranges[date_filter.lower()]

    @staticmethod
    def get_all_user_orders(
        user_id: str, 
        page: int = 1, 
        per_page: int = 10,
        sort_by: str = 'created_at',
        order: str = 'desc',
        status: Optional[str] = None,
        payment_method: Optional[str] = None,
        date_filter: Optional[str] = None
    ) -> Tuple[List[Order], int, Optional[str]]:
        """
        Retrieve all orders for a specific user with advanced filtering and pagination
        
        Args:
            user_id (str): ID of the user
            page (int, optional): Page number for pagination. Defaults to 1.
            per_page (int, optional): Number of orders per page. Defaults to 10.
            sort_by (str, optional): Field to sort by. Defaults to 'created_at'.
            order (str, optional): Sort order ('asc' or 'desc'). Defaults to 'desc'.
            status (Optional[str]): Filter by order status
            payment_method (Optional[str]): Filter by payment method
            date_filter (Optional[str]): Filter by date range
        
        Returns:
            Tuple containing:
            - List of orders for the current page
            - Total number of orders
            - Error message (if any)
        """
        try:
            # Validate sort_by and order parameters
            valid_sort_fields = ['created_at', 'total_amount', 'status']
            if sort_by not in valid_sort_fields:
                return [], 0, f"Invalid sort_by. Must be one of: {', '.join(valid_sort_fields)}"
            
            if order not in ['asc', 'desc']:
                return [], 0, "Invalid order. Must be 'asc' or 'desc'"
            
            # Base query for user's orders
            query = db.session.query(Order).filter(Order.user_id == user_id)
            
            # Apply status filter
            if status:
                try:
                    status_enum = OrderStatus(status.lower())
                    query = query.filter(Order.status == status_enum)
                except ValueError:
                    return [], 0, f"Invalid status. Must be one of: {', '.join([s.value for s in OrderStatus])}"
            
            # Apply payment method filter
            if payment_method:
                try:
                    payment_method_enum = PaymentMethod(payment_method.lower())
                    query = query.filter(Order.payment_method == payment_method_enum)
                except ValueError:
                    return [], 0, f"Invalid payment method. Must be one of: {', '.join([pm.value for pm in PaymentMethod])}"
            
            # Apply date range filter
            if date_filter:
                try:
                    start_date, end_date = OrderService._get_date_range(date_filter)
                    if start_date:
                        query = query.filter(Order.created_at >= start_date)
                    if end_date:
                        query = query.filter(Order.created_at <= end_date)
                except ValueError as e:
                    return [], 0, str(e)
            
            # Determine sort column and direction
            sort_column = getattr(Order, sort_by)
            sort_method = sort_column.desc() if order == 'desc' else sort_column.asc()
            
            # Count total orders after filtering
            total_orders = query.count()
            
            # Paginate and order results
            paginated_orders = (
                query.order_by(sort_method)
                .offset((page - 1) * per_page)
                .limit(per_page)
                .all()
            )
            
            return paginated_orders, total_orders, None
        
        except Exception as e:
            current_app.logger.error(f"Error fetching orders: {str(e)}")
            return [], 0, str(e)

    @staticmethod
    def update_order_status(
        order_id: int, 
        new_status: OrderStatus
    ) -> Order:
        """
        Update the status of an existing order
        
        Args:
            order_id (int): ID of the order to update
            new_status (OrderStatus): New status for the order
        
        Returns:
            Order: Updated order
        
        Raises:
            ValueError: If order not found
        """
        order = db.session.query(Order).get(order_id)
        
        if not order:
            raise ValueError("Order not found")
        
        order.status = new_status
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        db.session.refresh(order)
        
        return order

    @staticmethod
    def process_payment(
        order_id: int, 
        payment_transaction_id: Optional[str] = None
    ) -> Order:
        """
        Process payment for a pending order
        
        Args:
            order_id (int): Order to process
            payment_transaction_id (str, optional): Transaction ID for online payments
        
        Returns:
            Order: Processed order
        """
        order = db.session.query(Order).get(order_id)
        
        if not order:
            raise ValueError("Order not found")
        
        if order.status != OrderStatus.PENDING:
            raise ValueError("Order cannot be paid")
        
        try:
            # Check payment method
            if order.payment_method == PaymentMethod.ORDER_ON_DELIVERY:
                # For order on delivery, just mark as processing
                order.status = OrderStatus.PROCESSING
                
                # Reserve stock for delivery
                for item in order.order_items:
                    book = db.session.query(Book).get(item.book_id)
                    book.reserved_stock -= item.quantity
            else:
                # Existing payment processing logic
                payment_successful = True  # Mock payment success
                
                if payment_successful:
                    # Confirm order and finalize stock
                    order.status = OrderStatus.PAID
                    order.payment_transaction_id = payment_transaction_id
                    
                    # Finalize stock reduction
                    for item in order.order_items:
                        book = db.session.query(Book).get(item.book_id)
                        book.stock -= item.quantity
                        book.reserved_stock -= item.quantity
                    
                    # Send order invoice email
                    NotificationService.send_order_invoice(order)
                else:
                    # Payment failed, restore reserved stock
                    order.status = OrderStatus.CANCELLED
                    for item in order.order_items:
                        book = db.session.query(Book).get(item.book_id)
                        book.reserved_stock -= item.quantity
        
        except Exception as e:
            # Rollback in case of any processing error
            db.session.rollback()
            raise ValueError(f"Payment processing failed: {str(e)}")
        
        order.updated_at = datetime.utcnow()
        db.session.commit()
        db.session.refresh(order)
        
        return order

    @staticmethod
    def cancel_order(order_id: int) -> Order:
        """
        Cancel an existing order and restore book stock
        
        Args:
            order_id (int): ID of the order to cancel
        
        Returns:
            Order: Cancelled order
        
        Raises:
            ValueError: If order cannot be cancelled
        """
        order = db.session.query(Order).get(order_id)
        
        if not order:
            raise ValueError("Order not found")
        
        # Only allow cancellation of pending or processing orders
        if order.status not in [OrderStatus.PENDING, OrderStatus.PROCESSING]:
            raise ValueError("Order cannot be cancelled")
        
        # Restore book stock
        for item in order.order_items:
            book = db.session.query(Book).get(item.book_id)
            book.stock += item.quantity
        
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        db.session.refresh(order)
        
        return order