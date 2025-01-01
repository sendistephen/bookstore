from flask import current_app
from app.extensions import db
from app.models.order import Order, OrderItem, OrderStatus, PaymentMethod
from app.models.book import Book
from app.models.book_category import BookCategory
from app.services.notification_service import NotificationService
from datetime import datetime, timedelta
from sqlalchemy import func, text, desc, asc
from typing import Dict, Any, Optional, Tuple, List
import logging

class OrderService:
    @staticmethod
    def create_order(
        user_id: str, 
        cart_items: List[Dict[str, Any]], 
        payment_method: PaymentMethod,
        billing_info: Dict[str, Any],
        shipping_info: Optional[Dict[str, Any]] = None
    ) -> Order:
        """
        Create a new order from cart items
        
        Args:
            user_id (str): ID of the user placing the order
            cart_items (List[Dict]): List of items to order
            payment_method (PaymentMethod): Selected payment method
            billing_info (Dict): Billing information for the order
            shipping_info (Optional[Dict]): Optional shipping information
        
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
            
            # Update total amount and reduce book stock
            total_amount += order_item.price
            book.stock_quantity -= item['quantity']
            
            order_items.append(order_item)

        # Create new order
        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            payment_method=payment_method,
            status=OrderStatus.PENDING,
            
            # Billing Information
            billing_name=billing_info['name'],
            billing_email=billing_info['email'],
            billing_phone=billing_info['phone'],
            billing_street=billing_info['street'],
            billing_city=billing_info['city'],
            billing_state=billing_info.get('state', ''),
            billing_postal_code=billing_info['postal_code'],
            billing_country=billing_info['country']
        )

        # Add shipping information if provided
        if shipping_info:
            order.shipping_name = shipping_info['name']
            order.shipping_email = shipping_info['email']
            order.shipping_phone = shipping_info['phone']
            order.shipping_street = shipping_info['street']
            order.shipping_city = shipping_info['city']
            order.shipping_state = shipping_info.get('state', '')
            order.shipping_postal_code = shipping_info['postal_code']
            order.shipping_country = shipping_info['country']
        else:
            # Use billing info for shipping if not provided
            order.shipping_name = billing_info['name']
            order.shipping_email = billing_info['email']
            order.shipping_phone = billing_info['phone']
            order.shipping_street = billing_info['street']
            order.shipping_city = billing_info['city']
            order.shipping_state = billing_info.get('state', '')
            order.shipping_postal_code = billing_info['postal_code']
            order.shipping_country = billing_info['country']

        # Add order items to the order
        order.order_items = order_items

        # Commit changes
        try:
            db.session.add(order)
            db.session.commit()

            # Send order confirmation email
            NotificationService.send_order_invoice(order)

            return order
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to create order: {str(e)}")
            raise

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
        Retrieve all orders for a specific user with advanced pagination and filtering
        
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
            # Start with base query
            query = db.session.query(Order).filter(Order.user_id == user_id)
            
            # Apply status filter
            if status:
                try:
                    status_enum = OrderStatus[status.upper()]
                    query = query.filter(Order.status == status_enum)
                except KeyError:
                    raise ValueError(f"Invalid order status: {status}")
            
            # Apply payment method filter
            if payment_method:
                try:
                    payment_method_enum = PaymentMethod[payment_method.upper()]
                    query = query.filter(Order.payment_method == payment_method_enum)
                except KeyError:
                    raise ValueError(f"Invalid payment method: {payment_method}")
            
            # Apply date filter
            if date_filter:
                now = datetime.utcnow()
                if date_filter == 'today':
                    query = query.filter(
                        Order.created_at >= now.replace(hour=0, minute=0, second=0, microsecond=0)
                    )
                elif date_filter == 'yesterday':
                    yesterday = now - timedelta(days=1)
                    query = query.filter(
                        Order.created_at >= yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
                        Order.created_at < now.replace(hour=0, minute=0, second=0, microsecond=0)
                    )
                elif date_filter == 'today_and_yesterday':
                    yesterday = now - timedelta(days=1)
                    query = query.filter(
                        Order.created_at >= yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
                    )
                elif date_filter == '3days':
                    three_days_ago = now - timedelta(days=3)
                    query = query.filter(Order.created_at >= three_days_ago)
                elif date_filter == '7days':
                    seven_days_ago = now - timedelta(days=7)
                    query = query.filter(Order.created_at >= seven_days_ago)
                elif date_filter == '30days':
                    thirty_days_ago = now - timedelta(days=30)
                    query = query.filter(Order.created_at >= thirty_days_ago)
                else:
                    raise ValueError(f"Invalid date filter: {date_filter}")
            
            # Apply sorting
            if order.lower() == 'desc':
                query = query.order_by(desc(getattr(Order, sort_by)))
            else:
                query = query.order_by(asc(getattr(Order, sort_by)))
            
            # Apply pagination
            total_orders = query.count()
            orders = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return orders, total_orders, None
        
        except Exception as e:
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

    @staticmethod
    def get_sales_analytics(
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        period: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive sales analytics for the bookstore admin

        Args:
            start_date (Optional[datetime]): Start date for analytics
            end_date (Optional[datetime]): End date for analytics
            status (Optional[str]): Filter by specific order status
            period (Optional[str]): Predefined time period ('week', 'month', 'year')

        Returns:
            Dictionary containing various sales metrics
        """
        try:
            # Adjust dates based on period if provided
            now = datetime.now()
            if period:
                if period == 'week':
                    start_date = now - timedelta(days=7)
                elif period == 'month':
                    start_date = now - timedelta(days=30)
                elif period == 'year':
                    start_date = now - timedelta(days=365)
                end_date = now

            # Base query for orders
            query = db.session.query(Order)

            # Apply date range filter if provided
            if start_date:
                query = query.filter(Order.created_at >= start_date)
            if end_date:
                query = query.filter(Order.created_at <= end_date)

            # Apply status filter if provided
            if status:
                try:
                    status_enum = OrderStatus(status.lower())
                    query = query.filter(Order.status == status_enum)
                except ValueError:
                    raise ValueError(f"Invalid status. Must be one of: {', '.join([s.value for s in OrderStatus])}")

            # Total sales metrics
            total_orders = query.count()
            total_revenue = db.session.query(func.sum(Order.total_amount)).filter(query.whereclause).scalar() or 0

            # Sales by status
            status_breakdown = (
                db.session.query(
                    Order.status, 
                    func.count(Order.id).label('order_count'),
                    func.sum(Order.total_amount).label('total_amount')
                )
                .filter(query.whereclause)
                .group_by(Order.status)
                .all()
            )

            # Payment method breakdown
            payment_method_breakdown = (
                db.session.query(
                    Order.payment_method, 
                    func.count(Order.id).label('order_count'),
                    func.sum(Order.total_amount).label('total_amount')
                )
                .filter(query.whereclause)
                .group_by(Order.payment_method)
                .all()
            )

            # Top selling books
            top_books = (
                db.session.query(
                    Book.id.label('book_id'),
                    Book.title,
                    Book.author,
                    BookCategory.name.label('category_name'),
                    func.sum(OrderItem.quantity).label('total_quantity'),
                    func.sum(OrderItem.price * OrderItem.quantity).label('total_revenue')
                )
                .join(OrderItem, Book.id == OrderItem.book_id)
                .join(Order, OrderItem.order_id == Order.id)
                .join(BookCategory, Book.category_id == BookCategory.id)
                .filter(query.whereclause)
                .group_by(Book.id, Book.title, Book.author, BookCategory.name)
                .order_by(text('total_quantity DESC'))
                .limit(10)
                .all()
            )

            # Underperforming books (lowest sales)
            underperforming_books = (
                db.session.query(
                    Book.id.label('book_id'),
                    Book.title,
                    Book.author,
                    BookCategory.name.label('category_name'),
                    Book.price,
                    func.sum(OrderItem.quantity).label('total_quantity'),
                    func.sum(OrderItem.price * OrderItem.quantity).label('total_revenue')
                )
                .outerjoin(OrderItem, Book.id == OrderItem.book_id)
                .outerjoin(Order, OrderItem.order_id == Order.id)
                .join(BookCategory, Book.category_id == BookCategory.id)
                .filter(query.whereclause)
                .group_by(Book.id, Book.title, Book.author, BookCategory.name, Book.price)
                .order_by(text('total_quantity ASC'))
                .limit(10)
                .all()
            )

            # Prepare the analytics response
            return {
                'total_orders': total_orders,
                'total_revenue': float(total_revenue),
                'average_order_value': float(total_revenue / total_orders) if total_orders > 0 else 0,
                'status_breakdown': [
                    {
                        'status': str(status),
                        'order_count': count,
                        'total_amount': float(amount)
                    } for status, count, amount in status_breakdown
                ],
                'payment_method_breakdown': [
                    {
                        'payment_method': str(method),
                        'order_count': count,
                        'total_amount': float(amount)
                    } for method, count, amount in payment_method_breakdown
                ],
                'top_selling_books': [
                    {
                        'book_id': book_id,
                        'title': title,
                        'author': author,
                        'category': category,
                        'total_quantity': quantity,
                        'total_revenue': float(revenue)
                    } for book_id, title, author, category, quantity, revenue in top_books
                ],
                'underperforming_books': [
                    {
                        'book_id': book_id,
                        'title': title,
                        'author': author,
                        'category': category,
                        'price': float(price),
                        'total_quantity': quantity or 0,
                        'total_revenue': float(revenue or 0)
                    } for book_id, title, author, category, price, quantity, revenue in underperforming_books
                ]
            }

        except Exception as e:
            current_app.logger.error(f"Error generating sales analytics: {str(e)}")
            raise