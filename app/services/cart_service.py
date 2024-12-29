from app.models.book import Book
from app.models.cart import Cart
from app.models.cart_item import CartItem
from flask import current_app
from app.extensions import db

class CartService:
    """
    Cart service class for managing cart operations
    """
    
    @staticmethod
    def add_to_cart(user_id, book_id, quantity):
        """
        Add a book to the user's cart
        
        Args:
            user_id (str): User ID
            book_id (str): Book ID
            quantity (int): Quantity of the book to add to the cart
            
        Returns:
            tuple: (cart_data, None) if successful, (None, error_message) if failed
        """
        try:
            # Validate quantity
            if quantity <= 0:
                return None, "Quantity must be greater than 0"
            
            # Check if book exists
            book = Book.query.get(book_id)
            if not book:
                return None, f"Book with ID {book_id} not found"
            
            # Check stock availability
            if book.stock_quantity < quantity:
                return None, f"Book '{book.title}' is out of stock. Only {book.stock_quantity} available."
            
            # Get or create active cart for the user
            cart = Cart.query.filter_by(user_id=user_id, status='active').first()
            if not cart:
                cart = Cart(user_id=user_id, status='active')
                db.session.add(cart)
            
            # check if book already exists in cart
            existing_cart_item = CartItem.query.filter_by(cart_id=cart.id, book_id=book_id).first() 
            
            if existing_cart_item:
                # Update existing cart item
                existing_cart_item.quantity += quantity
                existing_cart_item.subtotal = existing_cart_item.quantity * book.price
            else:
                # Create new cart item
                cart_item = CartItem(
                    cart_id=cart.id,
                    book_id=book_id,
                    quantity=quantity,
                    price_at_addition=book.price,
                    subtotal=quantity * book.price
                )
                db.session.add(cart_item)
            
            # Update cart totals
            cart.total_items = sum(item.quantity for item in cart.cart_items)
            cart.total_price = sum(item.subtotal for item in cart.cart_items)
            
            db.session.commit()
            
            # Refresh the cart to get updated relationships
            db.session.refresh(cart)
            return cart, None
            
        except Exception as e:
            current_app.logger.error(f"Error adding to cart: {str(e)}")
            db.session.rollback()
            return None, str(e)