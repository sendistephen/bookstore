import os
from flask import render_template
from flask_mail import Mail, Message
from app.extensions import mail, db
from app.models.order import Order
from app.models.book import Book
from typing import Dict, Any
import logging

class NotificationService:
    @staticmethod
    def send_order_invoice(order: Order):
        """
        Send order invoice email to user
        
        Args:
            order (Order): Completed order
        """
        try:
            # Fetch user email
            user = order.user
            
            # Prepare order items details
            order_items_details = []
            for item in order.order_items:
                book = db.session.query(Book).get(item.book_id)
                order_items_details.append({
                    'book_name': book.title,
                    'book_cover': book.front_cover_url or '/static/default_book_cover.png',
                    'quantity': item.quantity,
                    'unit_price': book.price,
                    'total_price': item.price
                })
            
            # Render email template
            email_body = render_template(
                'order_invoice.html',
                order_id=order.id,
                order_date=order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                order_status=order.status.value,
                payment_method=order.payment_method.value,
                order_items=order_items_details,
                total_amount=order.total_amount
            )
            
            # Create message
            msg = Message(
                subject=f'Order Invoice #{ order.id }',
                recipients=[user.email],
                html=email_body
            )
            
            # Send email
            mail.send(msg)
            
            logging.info(f"Order invoice email sent for Order #{order.id}")
        
        except Exception as e:
            logging.error(f"Failed to send order invoice email: {str(e)}")
            # Optionally, you could implement a retry mechanism or 
            # store failed notifications for later processing
