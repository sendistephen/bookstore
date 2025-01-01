import os
from flask import current_app, render_template
from flask_mail import Message
from threading import Thread
from app.extensions import mail, db
from app.models.order import Order, OrderStatus, OrderItem
from app.models.book import Book
from app.models.user import User
from typing import Dict, Any
import logging
import traceback
from datetime import timedelta

def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {str(e)}")
            raise

def send_email(subject, recipients, template, **kwargs):
    """Send email using template"""
    try:
        app = current_app._get_current_object()
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=render_template(template, **kwargs),
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        if current_app.config['TESTING']:
            return
            
        Thread(
            target=send_async_email,
            args=(app, msg)
        ).start()
        
    except Exception as e:
        current_app.logger.error(f"Error preparing email: {str(e)}")
        raise

class NotificationService:
    @staticmethod
    def _get_book_cover_url(book: Book) -> str:
        """
        Get the book cover URL from Cloudinary or fallback to default
        
        Args:
            book (Book): Book model instance
        
        Returns:
            str: URL of the book cover
        """
        default_cover = '/static/default_book_cover.png'
        
        # If front_cover_public_id exists, construct Cloudinary URL
        if book.front_cover_public_id:
            return f"https://res.cloudinary.com/{current_app.config['CLOUDINARY_CLOUD_NAME']}/image/upload/{book.front_cover_public_id}"
        
        # If front_cover_url is a full URL, use it
        if book.front_cover_url and book.front_cover_url.startswith(('http://', 'https://')):
            return book.front_cover_url
        
        # If front_cover_url is a Cloudinary path
        if book.front_cover_url:
            return f"https://res.cloudinary.com/{current_app.config['CLOUDINARY_CLOUD_NAME']}/image/upload/{book.front_cover_url}"
        
        # Fallback to default cover
        return default_cover

    @staticmethod
    def send_order_invoice(order: Order):
        """
        Send order invoice or receipt based on payment status
        
        Args:
            order (Order): Order object to send invoice/receipt for
        """
        try:
            # Get the user associated with the order
            user = db.session.query(User).get(order.user_id)
            
            # Prepare order items details
            order_items_details = []
            for item in order.order_items:
                book = db.session.query(Book).get(item.book_id)
                
                # Construct book cover URL
                book_cover = NotificationService._get_book_cover_url(book)
                
                order_items_details.append({
                    'book_name': book.title,
                    'book_cover': book_cover,
                    'quantity': item.quantity,
                    'unit_price': book.price,
                    'total_price': item.price
                })
            
            # Prepare billing and shipping details
            billing_address = {
                'full_name': order.billing_name,
                'street': order.billing_street,
                'city': order.billing_city,
                'state': order.billing_state or 'N/A',
                'country': order.billing_country,
                'postal_code': order.billing_postal_code,
                'email': order.billing_email,
                'phone': order.billing_phone
            }
            
            # Prepare invoice details
            invoice_details = {
                'invoice_number': f"{order.id[:8].upper()}",
                'date_of_issue': order.created_at.strftime("%B %d, %Y"),
                'date_due': (order.created_at + timedelta(days=30)).strftime("%B %d, %Y")
            }
            
            # Prepare company details
            company_details = {
                'name': 'Bookstore Marketplace',
                'street': '900 Villa Street',
                'city': 'Mountain View',
                'state': 'California',
                'postal_code': '94041',
                'country': 'United States',
                'email': 'contact@bookstore.com'
            }
            
            # Determine email template and subject based on order status
            if order.status != OrderStatus.PAID:
                email_template = 'email/order_confirmation.html'
                email_subject = f'Invoice #{ order.id }'
            else:
                email_template = 'email/order_confirmation.html'
                email_subject = f'Receipt #{ order.id }'
            
            # Send email asynchronously
            msg = Message(
                subject=email_subject,
                recipients=[user.email],
                html=render_template(
                    email_template,
                    order_id=order.id,
                    order_date=order.created_at.strftime("%B %d, %Y"),
                    order_status=order.status.value,
                    payment_method=order.payment_method.value,
                    order_items=order_items_details,
                    billing_address=billing_address,
                    invoice_details=invoice_details,
                    company_details=company_details,
                    total_amount=order.total_amount
                )
            )
            
            # Send email in background
            current_app.extensions['mail'].send(msg)
            
            logging.info(f"Order invoice/receipt sent for order {order.id}")
        
        except Exception as e:
            logging.error(f"Failed to send order invoice/receipt: {str(e)}")
            # Optionally, you could add a retry mechanism or notification here
