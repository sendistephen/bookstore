from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String
import uuid
import os
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Define function to get database URL
def get_database_url():
    """Get the database URL based on environment."""
    return os.environ.get("DATABASE_URL")

# Create engine
engine = create_engine(get_database_url())

# Create session
Session = sessionmaker(bind=engine)
session = Session()

# Define Role class
Base = declarative_base()

class Role(Base):
    __tablename__ = 'roles'
    id = Column(String(36), primary_key=True)
    name = Column(String(32), unique=True, nullable=False)

def seed_roles():
    """Seed roles table with default roles"""
    roles = ['admin', 'customer']
    
    for role_name in roles:
        # Check if role exists
        role = session.query(Role).filter_by(name=role_name).first()
        if not role:
            role = Role(id=str(uuid.uuid4()), name=role_name)
            session.add(role)
    
    session.commit()
    print("Roles seeded successfully!")

if __name__ == '__main__':
    seed_roles()
