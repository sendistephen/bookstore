from flask import current_app
from app.extensions import db
from app.models.order import Order, OrderItem, OrderStatus, PaymentMethod, OrderStatusChangeLog
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
        # Log input parameters for debugging
        logging.info(f"Creating new order - User ID: {user_id}, Cart Items: {cart_items}, Payment Method: {payment_method}, Billing Info: {billing_info}, Shipping Info: {shipping_info}")
        
        # Calculate total amount and validate items
        total_amount = 0
        order_items = []

        for item in cart_items:
            book = db.session.query(Book).get(item['book_id'])
            if not book:
                logging.error(f"Book with ID {item['book_id']} not found")
                raise ValueError(f"Book with ID {item['book_id']} not found")
            
            # Validate quantity against available stock
            if book.stock_quantity < item['quantity']:
                logging.error(f"Insufficient stock for book {book.title}")
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
            logging.info(f"Order created successfully. Order ID: {order.id}")
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
        # Log input parameters for debugging
        logging.info(f"Retrieving user orders - User ID: {user_id}, Status: {status}")
        
        query = db.session.query(Order).filter(Order.user_id == user_id)
        
        if status:
            try:
                # Convert string status to enum
                status_enum = OrderStatus(status.lower())
                query = query.filter(Order.status == status_enum)
            except ValueError:
                # Provide a clear error message with valid status options
                valid_statuses = [s.value for s in OrderStatus]
                logging.error(f"Invalid status: {status}. Valid statuses: {valid_statuses}")
                raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        orders = query.order_by(Order.created_at.desc()).all()
        logging.info(f"Retrieved user orders. Order count: {len(orders)}")
        return orders

    @staticmethod
    def get_user_order_history(
        user_id: str, 
        page: int = 1, 
        per_page: int = 10
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieve simplified order history for a user
        
        Args:
            user_id (str): ID of the user
            page (int, optional): Page number for pagination. Defaults to 1.
            per_page (int, optional): Number of orders per page. Defaults to 10.
        
        Returns:
            Tuple containing:
            - List of simplified order details
            - Total number of orders
        """
        try:
            # Base query for user's orders
            query = db.session.query(Order).filter(Order.user_id == user_id)
            
            # Count total orders
            total_orders = query.count()
            
            # Retrieve orders with pagination, sorted by most recent first
            orders = (query.order_by(Order.created_at.desc())
                      .offset((page - 1) * per_page)
                      .limit(per_page)
                      .all())
            
            # Simplify order details for UI
            simplified_orders = [
                {
                    "id": order.id,
                    "total_amount": order.total_amount,
                    "status": order.status.value,
                    "created_at": order.created_at.isoformat(),
                    "items_count": len(order.order_items)
                } for order in orders
            ]
            
            logging.info(f"Retrieved user order history. User ID: {user_id}, Total Orders: {total_orders}")
            
            return simplified_orders, total_orders
        
        except Exception as e:
            logging.error(f"Failed to retrieve user order history: {str(e)}")
            raise ValueError(f"Failed to retrieve order history: {str(e)}")

    @staticmethod
    def get_all_orders_admin(
        page: int = 1, 
        per_page: int = 10,
        sort_by: str = 'created_at',
        order: str = 'desc',
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[List[Dict[str, Any]], int, Optional[str]]:
        """
        Retrieve comprehensive order list for admin with advanced filtering
        
        Args:
            page (int, optional): Page number for pagination. Defaults to 1.
            per_page (int, optional): Number of orders per page. Defaults to 10.
            sort_by (str, optional): Field to sort by. Defaults to 'created_at'.
            order (str, optional): Sort order ('asc' or 'desc'). Defaults to 'desc'.
            status (Optional[str]): Filter by order status
            start_date (Optional[datetime]): Filter orders from this date
            end_date (Optional[datetime]): Filter orders up to this date
        
        Returns:
            Tuple containing:
            - List of detailed order information
            - Total number of orders
            - Error message (if any)
        """
        try:
            # Start with base query
            query = db.session.query(Order)
            
            # Apply status filter if provided
            if status:
                query = query.filter(Order.status == OrderStatus[status.upper()])
            
            # Apply date range filter
            if start_date:
                query = query.filter(Order.created_at >= start_date)
            if end_date:
                query = query.filter(Order.created_at <= end_date)
            
            # Apply sorting
            if order.lower() == 'desc':
                query = query.order_by(desc(getattr(Order, sort_by)))
            else:
                query = query.order_by(asc(getattr(Order, sort_by)))
            
            # Count total orders
            total_orders = query.count()
            
            # Apply pagination
            orders = (query.offset((page - 1) * per_page)
                      .limit(per_page)
                      .all())
            
            # Prepare detailed order information
            detailed_orders = [
                {
                    "id": order.id,
                    "user_id": order.user_id,
                    "total_amount": order.total_amount,
                    "status": order.status.value,
                    "payment_method": order.payment_method.value if order.payment_method else None,
                    "created_at": order.created_at.isoformat(),
                    "updated_at": order.updated_at.isoformat(),
                    "items_count": len(order.order_items),
                    "billing_name": order.billing_name,
                    "shipping_status": order.status.name
                } for order in orders
            ]
            
            logging.info(f"Retrieved admin orders. Total Orders: {total_orders}")
            
            return detailed_orders, total_orders, None
        
        except Exception as e:
            logging.error(f"Failed to retrieve admin orders: {str(e)}")
            return [], 0, str(e)

    @staticmethod
    def admin_update_order_status(
        admin_id: str, 
        order_id: str, 
        new_status: str,
        reason: Optional[str] = None
    ) -> Order:
        """
        Update the status of an order by an admin with comprehensive validation
        
        Args:
            admin_id (str): ID of the admin updating the order
            order_id (str): ID of the order to update
            new_status (str): New status for the order
            reason (Optional[str]): Reason for status change (for audit trail)
        
        Returns:
            Order: Updated order object
        
        Raises:
            ValueError: If order is not found or status is invalid
        """
        # Validate input parameters
        if not new_status or not isinstance(new_status, str):
            logging.error("Status must be a non-empty string")
            raise ValueError("Status must be a non-empty string")
        
        try:
            # Convert string status to enum, using uppercase
            new_status_enum = OrderStatus[new_status.upper()]
            logging.info(f"Converted status to enum: {new_status_enum}")
        except KeyError:
            valid_statuses = [s.name for s in OrderStatus]
            logging.error(f"Invalid status: {new_status}. Valid statuses: {valid_statuses}")
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # Find the order
        order = db.session.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            logging.error(f"Order not found. Order ID: {order_id}")
            raise ValueError("Order not found")
        
        # Store previous status for audit
        previous_status = order.status
        
        # Update order status
        order.status = new_status_enum
        order.updated_at = datetime.utcnow()
        
        try:
            # Create an audit log entry
            audit_log = OrderStatusChangeLog(
                order_id=order.id,
                admin_id=admin_id,
                previous_status=previous_status.value,
                new_status=new_status_enum.value,
                reason=reason
            )
            db.session.add(audit_log)
            
            db.session.commit()
            db.session.refresh(order)
            
            logging.info(f"Admin order status update. Order ID: {order.id}, Previous Status: {previous_status.name}, New Status: {new_status_enum.name}")
            
            return order
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to update order status by admin: {str(e)}")
            raise ValueError("Failed to update order status")

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
        # Log input parameters for debugging
        logging.info(f"Processing payment - Order ID: {order_id}, Payment Transaction ID: {payment_transaction_id}")
        
        order = db.session.query(Order).get(order_id)
        
        if not order:
            logging.error(f"Order not found. Order ID: {order_id}")
            raise ValueError("Order not found")
        
        if order.status != OrderStatus.PENDING:
            logging.error(f"Order cannot be paid. Order ID: {order_id}, Status: {order.status.name}")
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
            logging.error(f"Payment processing failed: {str(e)}")
            raise ValueError(f"Payment processing failed: {str(e)}")
        
        order.updated_at = datetime.utcnow()
        db.session.commit()
        db.session.refresh(order)
        logging.info(f"Payment processed successfully. Order ID: {order.id}, Status: {order.status.name}")
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
        # Log input parameters for debugging
        logging.info(f"Cancelling order - Order ID: {order_id}")
        
        order = db.session.query(Order).get(order_id)
        
        if not order:
            logging.error(f"Order not found. Order ID: {order_id}")
            raise ValueError("Order not found")
        
        # Only allow cancellation of pending or processing orders
        if order.status not in [OrderStatus.PENDING, OrderStatus.PROCESSING]:
            logging.error(f"Order cannot be cancelled. Order ID: {order_id}, Status: {order.status.name}")
            raise ValueError("Order cannot be cancelled")
        
        # Restore book stock
        for item in order.order_items:
            book = db.session.query(Book).get(item.book_id)
            book.stock += item.quantity
        
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        db.session.refresh(order)
        logging.info(f"Order cancelled successfully. Order ID: {order.id}, Status: {order.status.name}")
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
        # Log input parameters for debugging
        logging.info(f"Generating sales analytics - Start Date: {start_date}, End Date: {end_date}, Status: {status}, Period: {period}")
        
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
                    logging.error(f"Invalid status: {status}")
                    raise ValueError(f"Invalid status: {status}")

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
            analytics = {
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
            logging.info(f"Generated sales analytics successfully")
            return analytics

        except Exception as e:
            logging.error(f"Failed to generate sales analytics: {str(e)}")
            raise