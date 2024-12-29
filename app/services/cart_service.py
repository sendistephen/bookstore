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
    def get_active_cart(user_id):
        """
        Get the user's active cart with all items
        
        Args:
            user_id (str): User ID
            
        Returns:
            tuple: (cart_data, None) if successful, (None, error_message) if failed
        """
        try:
            # Get active cart with items
            cart = Cart.query.filter_by(
                user_id=user_id,
                status='active'
            ).first()
            
            if not cart:
                return None, "No active cart found"
                
            return cart, None
            
        except Exception as e:
            current_app.logger.error(f"Error fetching cart: {str(e)}")
            return None, str(e)
    
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
            # total_items is the number of unique items in cart
            cart.total_items = len(cart.cart_items)
            # total_price is the sum of all item subtotals
            cart.total_price = sum(item.subtotal for item in cart.cart_items)
            
            db.session.commit()
            
            # Refresh the cart to get updated relationships
            db.session.refresh(cart)
            return cart, None
            
        except Exception as e:
            current_app.logger.error(f"Error adding to cart: {str(e)}")
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def update_cart_item(user_id, book_id, quantity):
        """
        Update the quantity of a specific book in the user's cart
        
        Args:
            user_id (str): User ID
            book_id (str): Book ID
            quantity (int): New quantity of the book
            
        Returns:
            tuple: (cart_data, None) if successful, (None, error_message) if failed
        """
        try:
            # Validate quantity
            if quantity < 0:
                return None, "Quantity cannot be negative"
            
            # Check if book exists
            book = Book.query.get(book_id)
            if not book:
                return None, f"Book with ID {book_id} not found"
            
            # Get active cart for the user
            cart = Cart.query.filter_by(user_id=user_id, status='active').first()
            if not cart:
                return None, "No active cart found"
            
            # Find the cart item
            cart_item = CartItem.query.filter_by(cart_id=cart.id, book_id=book_id).first()
            if not cart_item:
                return None, f"Book {book_id} not in cart"
            
            # Check stock availability if increasing quantity
            if quantity > cart_item.quantity:
                additional_quantity = quantity - cart_item.quantity
                if book.stock_quantity < additional_quantity:
                    return None, f"Book '{book.title}' is out of stock. Only {book.stock_quantity} additional can be added."
            
            # Update quantity and subtotal
            if quantity == 0:
                # Remove item if quantity is 0
                db.session.delete(cart_item)
            else:
                cart_item.quantity = quantity
                cart_item.subtotal = quantity * book.price
            
            # Refresh cart items
            db.session.flush()
            
            # Recalculate cart totals
            remaining_items = CartItem.query.filter_by(cart_id=cart.id).all()
            
            if not remaining_items:
                # If no items left, mark cart as empty but don't delete
                cart.total_items = 0
                cart.total_price = 0.0
                cart.status = 'empty'
            else:
                # Update cart totals
                cart.total_items = len(remaining_items)
                cart.total_price = sum(item.subtotal for item in remaining_items)
                cart.status = 'active'
            
            db.session.commit()
            
            # If no items left, return cart with empty status
            if not remaining_items:
                return cart, None
            
            # Refresh the cart to get updated relationships
            db.session.refresh(cart)
            return cart, None
            
        except Exception as e:
            current_app.logger.error(f"Error updating cart item: {str(e)}")
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def clear_cart(user_id):
        """
        Clear all items from the user's active cart
        
        Args:
            user_id (str): User ID
            
        Returns:
            tuple: (cart_data, None) if successful, (None, error_message) if failed
        """
        try:
            # Get active cart for the user
            cart = Cart.query.filter_by(user_id=user_id, status='active').first()
            if not cart:
                return None, "No active cart found"
            
            # Delete all cart items
            CartItem.query.filter_by(cart_id=cart.id).delete()
            
            # Update cart status and totals
            cart.total_items = 0
            cart.total_price = 0.0
            # Keep status as 'active', but with zero items
            cart.status = 'active'
            
            db.session.commit()
            
            return cart, None
            
        except Exception as e:
            current_app.logger.error(f"Error clearing cart: {str(e)}")
            db.session.rollback()
            return None, str(e)