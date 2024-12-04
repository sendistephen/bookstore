from app.extensions import db
from app.models.user import User
from app.models.role import Role
from flask import current_app

class AdminService:
    @staticmethod
    def create_admin(email, username, name, password):
        """
        Create a new admin user
        
        Args:
            email (str): Admin's email
            username (str): Admin's username
            name (str): Admin's name
            password (str): Admin's password
        
        Returns:
            User: Newly created admin user
        
        Raises:
            ValueError: if validation fails
        """
        
        # Check for existing users
        existing_user = User.query.filter(
            (User.email.ilike(email)) | (User.username.ilike(username))
        ).first()
        
        if existing_user:
            raise ValueError('User with this email or username already exists')
        
        # Ensure admin role exists
        admin_role = Role.query.filter_by(name='admin').first()
        
        if not admin_role:
            admin_role = Role(name='admin', description='Administrator role with full access')
            db.session.add(admin_role)
        
        # Create new admin
        new_admin = User(
            email=email,
            username=username,
            name=name,
            is_verified=True,
            is_active=True
        )
        
        # Set password
        new_admin.set_password(password)
        
        # Assign admin role
        new_admin.roles.append(admin_role)
        
        try:
            db.session.add(new_admin)
            db.session.commit()
            current_app.logger.info(f"Admin user {email} created successfully")
            return new_admin
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating admin user: {str(e)}")
            raise ValueError(f'Failed to create admin user: {str(e)}')

@staticmethod
def get_admin_users():
    """
    Retrieve all admin users
    
    Returns:
        List[User]: List of admin users
    """
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        return []
    return User.query.filter(User.roles.contains(admin_role)).all()

@staticmethod
def deactivate_admin(user_id):
    """
    Deactivate an admin user by user ID
    
    Args:
        user_id (str): ID of the admin user to deactivate
    
    Returns:
        bool: True if deactivation successful
    """
    
    user = User.query.get(user_id)
    if not user:
        raise ValueError('User not found')

    user.is_active = False
    db.session.commit()
    return True