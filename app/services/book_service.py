from app.models.book import Book
from flask import current_app
from app.extensions import db
from datetime import datetime
from app.schemas.book_schema import BookSchema, BookUpdateSchema
from sqlalchemy import desc, or_

class BookService:
    """Book service class"""

    @staticmethod
    def get_all_books(page=1, per_page=10, sort_by='created_at', order='desc', search=None, category_id=None):
        """
        Fetch books with pagination and filtering
        
        Args:
            page (int): Current page number
            per_page (int): Number of items per page
            sort_by (str): Field to sort by
            order (str): Sort order ('asc' or 'desc')
            search (str, optional): Search term for title or description
            category_id (str, optional): Filter by category
        
        Returns:
            dict: Pagination metadata and book list
        """
        try:
            # Build a query
            query = Book.query

            # Apply category filter if provided
            if category_id:
                query = query.filter(Book.category_id == category_id)

            # Apply search filter if provided
            if search:
                # Remove quotes if present
                search = search.strip("'\"")
                
                # Ensure search is not an empty string
                if search:
                    search_term = f"%{search}%"
                    query = query.filter(
                        or_(
                            Book.title.ilike(search_term),
                        )
                    )

            # Determine sort column and order
            sort_column = getattr(Book, sort_by, Book.created_at)
            sort_method = desc(sort_column) if order == 'desc' else sort_column

            # Apply sorting
            query = query.order_by(sort_method)

            # Paginate results
            paginated_books = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )

            # Serialize books
            book_schema = BookSchema(many=True)
            serialized_books = book_schema.dump(paginated_books.items)

            # Prepare pagination metadata
            return {
                'data': serialized_books,
                'pagination': {
                    'total_items': paginated_books.total,
                    'total_pages': paginated_books.pages,
                    'current_page': page,
                    'per_page': per_page,
                    'has_next': paginated_books.has_next,
                    'has_prev': paginated_books.has_prev,
                    'next_page': page + 1 if paginated_books.has_next else None,
                    'prev_page': page - 1 if paginated_books.has_prev else None
                }
            }
        except Exception as e:
            current_app.logger.error(f"Error fetching books: {str(e)}")
            return None, str(e)

    @staticmethod
    def get_book_by_id(book_id):
        """Get book by ID
        
        Args:
            book_id (str): Book ID
        
        Returns:
            tuple: (book_data, error)
            book_data (dict): Book data if found
            error (str): Error message if book not found
        """
        try:
            book = Book.query.get(book_id)
            
            # check if book exists
            if not book:
                return None, f"Book with ID {book_id} not found"
            
            # Serialize the book data
            book_schema = BookSchema()
            serialized_book = book_schema.dump(book)
            return serialized_book, None
        
        except Exception as e:
            current_app.logger.error(f"Error fetching book: {str(e)}")
            return None, str(e)

    @staticmethod
    def check_book_exists(payload):
        """Check if book exists by ISBN"""
        if 'isbn' in payload:
            existing_book = Book.query.filter_by(isbn=payload['isbn']).first()
            if existing_book:
                return True, f"Book with ISBN {payload['isbn']} already exists"
        return False, None

    @staticmethod
    def create_book(payload):
        """Create a new book"""
        try:
            # Initialize schema
            book_schema = BookSchema()
            
            # Validate and deserialize input
            book = book_schema.load(payload)
            
            # Add to database
            db.session.add(book)
            db.session.commit()
            
            # Return serialized book
            return book_schema.dump(book), None
            
        except Exception as e:
            current_app.logger.error(f"Error creating book: {str(e)}")
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def update_book(book_id, payload,partial=False):
        """
        Update an existing book
        
        Args:
            book_id (str): Unique identifier of the book to update
            payload (dict): Book update data
        
        Returns:
            tuple: (updated_book, error)
        """
        try:
            # Find the book
            book = Book.query.get(book_id)
            if not book:
                return None, f"Book with ID {book_id} not found"

            # Validate and deserialize update payload
            book_update_schema = BookUpdateSchema(partial=partial)
            update_data = book_update_schema.load(payload, instance=book, session=db.session)

            # Update timestamps
            update_data.updated_at = datetime.utcnow()

            # Commit changes
            db.session.commit()

            # Serialize and return updated book
            book_schema = BookSchema()
            return book_schema.dump(update_data), None

        except Exception as e:
            # Rollback in case of error
            db.session.rollback()
            current_app.logger.error(f"Error updating book {book_id}: {str(e)}")
            return None, str(e)

    @staticmethod
    def delete_book(book_id):
        """
        Delete a book
        
        Args:
            book_id (str): Unique identifier of the book to delete
        
        Returns: 
            None, error message if book not found
        """
        try:
            # find the book
            book = Book.query.get(book_id)
            if not book:
                return None, f"Book with ID {book_id} not found"
            
            # delete the book
            db.session.delete(book)
            db.session.commit()
            return None, None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting book {book_id}: {str(e)}")
            return None, str(e)

    @staticmethod
    def search_books(query):
        """Search for books by title, author, or genre"""
        pass

    @staticmethod
    def get_books_by_category(category_id):
        """Get books by category"""
        pass

    @staticmethod
    def get_books_by_author(author_id):
        """Get books by author"""
        pass

    @staticmethod
    def get_books_by_genre(genre_id):
        """Get books by genre"""
        pass

    @staticmethod
    def get_books_by_publisher(publisher_id):
        """Get books by publisher"""
        pass

    @staticmethod
    def get_books_by_language(language_id):
        """Get books by language"""
        pass

    @staticmethod
    def get_books_by_price_range(min_price, max_price):
        """Get books by price range"""
        pass

    @staticmethod
    def get_books_by_publication_date_range(start_date, end_date):
        """Get books by publication date range"""
        pass

    @staticmethod
    def get_books_by_edition(edition):
        """Get books by edition"""
        pass

    @staticmethod
    def get_books_by_isbn(isbn):
        """Get books by ISBN"""
        pass

    @staticmethod
    def get_books_by_title(title):
        """Get books by title"""
        pass
