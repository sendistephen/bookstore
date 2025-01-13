from flask import current_app, render_template
import logging
from threading import Thread
from datetime import datetime
import pytz

try:
    from flask_mail import Message, Mail
except ImportError:
    Message = None
    Mail = None

def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail = Mail(app)
            mail.send(msg)
        except Exception as e:
            logging.error(f"Failed to send async email: {str(e)}")
            logging.exception(e)
            raise

def send_email(subject, recipients, template, **kwargs):
    """
    Send email using Flask-Mail
    
    Args:
        subject (str): Email subject
        recipients (list): List of recipient email addresses
        template (str): Email template to use
        **kwargs: Additional template parameters
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Ensure template path is correct
    if not template.startswith('email/'):
        template = f'email/{template}'
    
    # Default context for all emails
    default_context = {
        'year': datetime.now(pytz.UTC).year,
        'contact_url': current_app.config.get('CONTACT_URL', '#'),
        'frontend_url': current_app.config.get('FRONTEND_URL', '#')
    }
    
    # Update kwargs with default context
    kwargs.update({k: v for k, v in default_context.items() if k not in kwargs})
    
    # Check if Mail is available
    if not Mail:
        logging.warning("Flask-Mail not installed. Email sending disabled.")
        return False
    
    try:
        # Create mail extension instance
        mail = Mail(current_app)
        
        # Create message
        msg = Message(
            subject=subject,
            recipients=recipients,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@bookstore.com')
        )
        
        # Render email template
        try:
            msg.html = render_template(template, **kwargs)
        except Exception as e:
            logging.error(f"Failed to render email template: {str(e)}")
            return False
        
        # Fallback plain text body
        try:
            msg.body = render_template(template.replace('.html', '.txt'), **kwargs) if template.endswith('.html') else msg.html
        except Exception as e:
            logging.error(f"Failed to render email plain text body: {str(e)}")
            return False
        
        # Send email
        if not current_app.config.get('TESTING', False):
            try:
                Thread(
                    target=send_async_email,
                    args=(current_app._get_current_object(), msg)
                ).start()
            except Exception as e:
                logging.error(f"Failed to send email asynchronously: {str(e)}")
                return False
        
        logging.info(f"Email sent to {recipients}")
        return True
    
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")
        logging.exception(e)
        return False

def send_verification_email(user, verification_url):
    """Send verification email to user"""
    try:
        return send_email(
            'Verify Your Bookstore Account',
            [user.email],
            'verify_email.html',
            user=user,
            verification_url=verification_url
        )
    except Exception as e:
        logging.error(f"Failed to send verification email: {str(e)}")
        logging.exception(e)
        return False

def send_password_reset_email(user, reset_url):
    """Send password reset email to user"""
    try:
        return send_email(
            'Reset Your Bookstore Password',
            [user.email],
            'reset_password.html',
            user=user,
            reset_url=reset_url
        )
    except Exception as e:
        logging.error(f"Failed to send password reset email: {str(e)}")
        logging.exception(e)
        return False

def send_password_changed_email(user, device_info):
    """Send password changed notification email"""
    try:
        timestamp = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')
        
        return send_email(
            'Your Bookstore Password Has Been Changed',
            [user.email],
            'password_changed.html',
            user=user,
            timestamp=timestamp,
            location=device_info.get('location', 'Unknown'),
            device=device_info.get('device', 'Unknown')
        )
    except Exception as e:
        logging.error(f"Failed to send password changed email: {str(e)}")
        logging.exception(e)
        return False
