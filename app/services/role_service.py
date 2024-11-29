from app.models.role import Role
from app.extensions import db
import uuid

class RoleService:
    @staticmethod
    def ensure_default_roles():
        """
        Ensure default roles exist in the database
        Returns the customer role
        """
        roles = {
            'admin': 'Administrator role with full access',
            'customer': 'Default customer role'
        }
        
        customer_role = None
        for role_name, description in roles.items():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(id=str(uuid.uuid4()), name=role_name)
                db.session.add(role)
                db.session.flush()
            
            if role_name == 'customer':
                customer_role = role
        
        db.session.commit()
        return customer_role

    @staticmethod
    def get_customer_role():
        """Get or create the customer role"""
        role = Role.query.filter_by(name='customer').first()
        if not role:
            return RoleService.ensure_default_roles()
        return role
