import pytest
import uuid
from app.services.book_category_service import BookCategoryService
from app.models.book_category import BookCategory
from app.models.user import User
from app.models.role import Role
from app.extensions import db
from werkzeug.security import generate_password_hash

def create_admin_user(unique_email=None):
    """Create an admin user for testing purposes."""
    # First, create an admin role if it doesn't exist
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin')
        db.session.add(admin_role)
        db.session.commit()

    # Generate a unique email if not provided
    if unique_email is None:
        unique_email = f'admin_test_{uuid.uuid4()}@example.com'

    # Create an admin user
    admin_user = User(
        username=f'admin_test_{uuid.uuid4()}',
        email=unique_email,
        name='Admin Test'
    )
    admin_user.set_password('password123')
    admin_user.roles.append(admin_role)
    
    db.session.add(admin_user)
    db.session.commit()
    
    return admin_user

class TestBookCategoryService:
    def test_create_book_category_success(self, db_session):
        """
        Test successful creation of a book category
        """
        # Create an admin user and category details
        admin_user = create_admin_user()
        category_name = "Science Fiction"
        category_description = "Books about futuristic scenarios"

        # Act
        new_category = BookCategoryService.create_book_category(
            name=category_name,
            description=category_description,
            user=admin_user
        )

        # Assert
        assert new_category is not None
        assert new_category.name == category_name
        assert new_category.description == category_description

    def test_create_duplicate_category_fails(self, db_session):
        """
        Test that creating a category with an existing name raises an error
        """
        # Arrange: Create an admin user
        admin_user = create_admin_user()
        category_name = "Mystery"
        
        # Create first category
        BookCategoryService.create_book_category(
            name=category_name, 
            user=admin_user
        )

        # Act & Assert
        with pytest.raises(ValueError, match=f'Category with name "{category_name}" already exists'):
            BookCategoryService.create_book_category(
                name=category_name, 
                user=admin_user
            )

    def test_get_all_book_categories(self, db_session):
        """
        Test retrieving all book categories
        """
        # Arrange: Create admin user and categories
        admin_user = create_admin_user()
        categories = [
            {"name": "Fantasy", "description": "Magical worlds"},
            {"name": "Romance", "description": "Love stories"},
            {"name": "Thriller", "description": "Suspenseful narratives"}
        ]

        # Create categories
        created_categories = []
        for category in categories:
            created_category = BookCategoryService.create_book_category(
                **category, 
                user=admin_user
            )
            created_categories.append(created_category)

        # Act
        all_categories = BookCategoryService.get_all_book_categories()

        # Assert
        assert len(all_categories) >= len(categories)
        assert all(category in all_categories for category in created_categories)

    def test_update_book_category_success(self, db_session):
        """
        Test updating an existing book category
        """
        # Arrange: Create an original category
        admin_user = create_admin_user()
        original_category = BookCategoryService.create_book_category(
            name="Original Category",
            description="Initial description",
            user=admin_user
        )

        # Act
        updated_category = BookCategoryService.update_book_category(
            category_id=original_category.id, 
            update_data={
                'name': 'Updated Category', 
                'description': 'Updated description'
            }
        )

        # Assert
        assert updated_category is not None
        assert updated_category.name == 'Updated Category'
        assert updated_category.description == 'Updated description'

    def test_update_category_with_existing_name_fails(self, db_session):
        """
        Test that updating a category to a name that already exists fails
        """
        # Arrange
        admin_user = create_admin_user()
        category1 = BookCategoryService.create_book_category(
            name="Category A", 
            user=admin_user
        )
        category2 = BookCategoryService.create_book_category(
            name="Category B", 
            user=admin_user
        )

        # Act & Assert
        with pytest.raises(ValueError, match='Category name must be unique'):
            BookCategoryService.update_book_category(
                category_id=category2.id, 
                update_data={'name': 'Category A'}
            )

    def test_update_nonexistent_category_fails(self, db_session):
        """
        Test that updating a non-existent category fails
        """
        # Act & Assert
        with pytest.raises(ValueError, match='Category with ID "non-existent-uuid" not found'):
            BookCategoryService.update_book_category(
                category_id='non-existent-uuid', 
                update_data={'name': 'New Name'}
            )

    def test_create_category_requires_admin_authorization(self, db_session):
        """
        Test that only admin users can create book categories
        """
        # Arrange: Create a non-admin user
        non_admin_user = User(
            username=f'regular_user_{uuid.uuid4()}', 
            email=f'regular_{uuid.uuid4()}@example.com',
            name='Regular User'
        )
        non_admin_user.set_password('password123')
        db.session.add(non_admin_user)
        db.session.commit()

        # Act & Assert
        with pytest.raises(ValueError, match='Only admin users can create book categories'):
            BookCategoryService.create_book_category(
                name="Test Category", 
                user=non_admin_user
            )

    def test_create_category_by_admin_succeeds(self, db_session):
        """
        Test that admin users can successfully create book categories
        """
        # Arrange: Create an admin user
        admin_user = create_admin_user()
        
        # Act
        new_category = BookCategoryService.create_book_category(
            name="Admin Category", 
            user=admin_user
        )
        
        # Assert
        assert new_category is not None
        assert new_category.name == "Admin Category"
