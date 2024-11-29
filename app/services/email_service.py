from flask import current_app, render_template
from flask_mail import Message, Mail
from threading import Thread
from datetime import datetime
import pytz

mail = Mail()

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

def send_verification_email(user, verification_url):
    """Send verification email to user"""
    try:
        send_email(
            'Verify Your Bookstore Account',
            [user.email],
            'email/verify_email.html',
            user=user,
            verification_url=verification_url,
            contact_url=current_app.config.get('CONTACT_URL'),
            year=datetime.now(pytz.UTC).year
        )
    except Exception as e:
        current_app.logger.error(f"Failed to send verification email: {str(e)}")
        raise

def send_password_reset_email(user, reset_url):
    """Send password reset email to user"""
    try:
        send_email(
            'Reset Your Bookstore Password',
            [user.email],
            'email/reset_password.html',
            user=user,
            reset_url=reset_url,
            contact_url=current_app.config.get('CONTACT_URL')
        )
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email: {str(e)}")
        raise

def send_password_changed_email(user, device_info):
    """Send password changed notification email"""
    try:
        timestamp = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')
        reset_url = f"{current_app.config['FRONTEND_URL']}/reset-password"
        
        send_email(
            'Your Bookstore Password Has Been Changed',
            [user.email],
            'email/password_changed.html',
            user=user,
            timestamp=timestamp,
            location=device_info.get('location', 'Unknown'),
            device=device_info.get('device', 'Unknown'),
            reset_url=reset_url,
            contact_url=current_app.config.get('CONTACT_URL')
        )
    except Exception as e:
        current_app.logger.error(f"Failed to send password changed email: {str(e)}")
        raise
