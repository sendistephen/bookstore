from datetime import datetime, timedelta
from flask import current_app, url_for
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
from app.models.user import User, db
from app.models.role import Role
from app.services.email_service import send_verification_email, send_password_reset_email, send_password_changed_email
from app.services.role_service import RoleService
from utils.error_handler import bad_request_error
import secrets

class AuthService:
    @staticmethod
    def register_user(data):
        """Register a new user and send verification email"""
        try:
            # Check if user exists (case-insensitive)
            existing_username = User.query.filter(
                db.func.lower(User.username) == db.func.lower(data['username'])
            ).first()
            if existing_username:
                raise ValueError('Username already exists')

            existing_email = User.query.filter(
                db.func.lower(User.email) == db.func.lower(data['email'])
            ).first()
            if existing_email:
                raise ValueError('Email already exists')
            
            # Validate password
            is_valid, message = User.validate_password(data['password'])
            if not is_valid:
                raise ValueError(message)
            
            # Create user
            user = User(
                username=data['username'],
                name=data['name'],
                email=data['email'],
                phone=data.get('phone')
            )
            user.set_password(data['password'])
            
            # Generate verification token
            verification_token = secrets.token_urlsafe(32)
            user.verification_token = verification_token
            user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
            
            # Get or create customer role and assign to user
            customer_role = RoleService.get_customer_role()
            user.roles.append(customer_role)
            
            db.session.add(user)
            db.session.commit()
            
            # Generate verification URL
            verification_url = url_for(
                'api_v1.verify_email',
                token=verification_token,
                _external=True
            )
            
            # Send verification email
            send_verification_email(user, verification_url)
            
            return {
                'status': 'success',
                'message': 'Registration successful. Please check your email to verify your account.',
                'data': {
                    'user_id': user.id,
                    'email': user.email
                }
            }
            
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def login_user(email, password):
        """Authenticate user and generate access token"""
        # Find user by email (case-insensitive)
        user = User.query.filter(
            db.func.lower(User.email) == db.func.lower(email)
        ).first()
        
        if not user or not user.check_password(password):
            raise ValueError('Invalid email or password')
            
        if not user.is_verified:
            raise ValueError('Please verify your email before logging in')
            
        # Create access and refresh tokens
        access_token = create_access_token(
            identity=user.id,
            additional_claims={
                'email': user.email,
                'roles': [role.name for role in user.roles]
            }
        )
        
        refresh_token = create_refresh_token(
            identity=user.id
        )
        
        return {
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'roles': [role.name for role in user.roles]
                }
            }
        }

    @staticmethod
    def verify_email(token):
        """Verify user email with token"""
        user = User.query.filter_by(verification_token=token).first()
        
        if not user:
            raise ValueError('Invalid verification token')
            
        if user.is_verified:
            raise ValueError('Email already verified')
            
        if user.verification_token_expires < datetime.utcnow():
            raise ValueError('Verification token has expired')
            
        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        user.email_verified_at = datetime.utcnow()
        
        db.session.commit()
        
        return {
            'status': 'success',
            'message': 'Email verified successfully'
        }

    @staticmethod
    def resend_verification(user):
        """Resend verification email"""
        if user.is_verified:
            raise ValueError('Email already verified')
            
        # Generate new verification token
        verification_token = secrets.token_urlsafe(32)
        user.verification_token = verification_token
        user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
        
        db.session.commit()
        
        # Generate verification URL
        verification_url = url_for(
            'api_v1.verify_email',
            token=verification_token,
            _external=True
        )
        
        # Send verification email
        send_verification_email(user, verification_url)
        
        return {
            'status': 'success',
            'message': 'Verification email sent successfully'
        }

    @staticmethod
    def request_password_reset(email):
        """Generate password reset token and send email"""
        user = User.query.filter(
            db.func.lower(User.email) == db.func.lower(email)
        ).first()
        
        if not user:
            raise ValueError('Email not found')
            
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        
        db.session.commit()
        
        # Generate reset URL
        reset_url = url_for(
            'api_v1.reset_password',
            token=reset_token,
            _external=True
        )
        
        # Send reset email
        send_password_reset_email(user, reset_url)
        
        return {
            'status': 'success',
            'message': 'Password reset instructions sent to your email'
        }

    @staticmethod
    def reset_password(token, new_password):
        """Reset user password with token"""
        user = User.query.filter_by(reset_token=token).first()
        
        if not user:
            raise ValueError('Invalid reset token')
            
        if user.reset_token_expires < datetime.utcnow():
            raise ValueError('Reset token has expired')
            
        # Validate new password
        is_valid, message = User.validate_password(new_password)
        if not is_valid:
            raise ValueError(message)
            
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        
        db.session.commit()
        
        # Send password changed notification
        send_password_changed_email(user, "Password reset through reset link")
        
        return {
            'status': 'success',
            'message': 'Password reset successful'
        }

    @staticmethod
    def change_password(user, current_password, new_password):
        """Change user password"""
        if not user.check_password(current_password):
            raise ValueError('Current password is incorrect')
            
        # Validate new password
        is_valid, message = User.validate_password(new_password)
        if not is_valid:
            raise ValueError(message)
            
        user.set_password(new_password)
        db.session.commit()
        
        # Send password changed notification
        send_password_changed_email(user, "Password changed by user")
        
        return {
            'status': 'success',
            'message': 'Password changed successfully'
        }
