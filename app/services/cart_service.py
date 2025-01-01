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
            
            # Get or create active cart for the user
            cart = Cart.query.filter_by(user_id=user_id, status='active').first()
            if not cart:
                cart = Cart(user_id=user_id, status='active')
                db.session.add(cart)
            
            # Check existing cart item for this book
            existing_cart_item = CartItem.query.filter_by(cart_id=cart.id, book_id=book_id).first()
            
            # Calculate total quantity in cart and proposed new quantity
            total_cart_quantity = quantity
            if existing_cart_item:
                total_cart_quantity += existing_cart_item.quantity
            
            # Check stock availability
            if book.stock_quantity < total_cart_quantity:
                return None, f"Insufficient stock for book '{book.title}'. " \
                              f"Available: {book.stock_quantity}, " \
                              f"Requested: {total_cart_quantity}"
            
            if existing_cart_item:
                # Update existing cart item
                existing_cart_item.quantity += quantity
                existing_cart_item.subtotal = round(existing_cart_item.quantity * book.price, 2)
            else:
                # Create new cart item
                cart_item = CartItem(
                    cart_id=cart.id,
                    book_id=book_id,
                    quantity=quantity,
                    price_at_addition=book.price,
                    subtotal=round(quantity * book.price, 2)
                )
                db.session.add(cart_item)
            
            # Recalculate cart totals
            cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
            
            # Update cart totals
            cart.total_items = len(cart_items)  # Number of unique items
            cart.total_price = round(sum(item.subtotal for item in cart_items), 2)
            
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
            
            # Check stock availability
            if book.stock_quantity < quantity:
                return None, f"Insufficient stock for book '{book.title}'. " \
                              f"Available: {book.stock_quantity}, " \
                              f"Requested: {quantity}"
            
            # Update quantity and subtotal
            if quantity == 0:
                # Remove item if quantity is 0
                db.session.delete(cart_item)
            else:
                cart_item.quantity = quantity
                cart_item.subtotal = round(quantity * book.price, 2)
            
            # Refresh cart items
            db.session.flush()
            
            # Recalculate cart totals
            remaining_items = CartItem.query.filter_by(cart_id=cart.id).all()
            
            if not remaining_items:
                # If no items left, reset cart totals
                cart.total_items = 0
                cart.total_price = 0.0
            else:
                # Update cart totals
                cart.total_items = len(remaining_items)
                cart.total_price = round(sum(item.subtotal for item in remaining_items), 2)
            
            db.session.commit()
            
            # If no items left, return cart with zero totals
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
    def remove_cart_item(user_id, book_id):
        """
        Remove a specific item from the user's cart
        If quantity > 1, reduce quantity by 1
        If quantity is 1, remove the entire cart item
        
        Args:
            user_id (str): User ID
            book_id (str): Book ID to remove
            
        Returns:
            tuple: (cart_data, removed_item_info, None) if successful, 
                   (None, None, error_message) if failed
        """
        try:
            # Get active cart for the user
            cart = Cart.query.filter_by(user_id=user_id, status='active').first()
            if not cart:
                return None, None, "No active cart found"
            
            # Find the cart item to remove
            cart_item = CartItem.query.filter_by(cart_id=cart.id, book_id=book_id).first()
            if not cart_item:
                return None, None, f"Book {book_id} not found in cart"
            
            # Prepare removal information
            removed_item_info = {
                'book_id': book_id,
                'book_title': cart_item.book.title,
                'previous_quantity': cart_item.quantity,
                'removed_completely': False
            }
            
            # If quantity is 1, remove the entire cart item
            if cart_item.quantity <= 1:
                db.session.delete(cart_item)
                removed_item_info['removed_completely'] = True
            else:
                # Reduce quantity by 1
                cart_item.quantity -= 1
                # Recalculate subtotal
                cart_item.subtotal = round(cart_item.quantity * cart_item.price_at_addition, 2)
                removed_item_info['remaining_quantity'] = cart_item.quantity
            
            # Refresh cart items
            db.session.flush()
            
            # Recalculate cart totals
            remaining_items = CartItem.query.filter_by(cart_id=cart.id).all()
            
            if not remaining_items:
                # If no items left, reset cart totals
                cart.total_items = 0
                cart.total_price = 0.0
            else:
                # Update cart totals
                cart.total_items = len(remaining_items)
                cart.total_price = round(sum(item.subtotal for item in remaining_items), 2)
            
            db.session.commit()
            
            return cart, removed_item_info, None
            
        except Exception as e:
            current_app.logger.error(f"Error removing cart item: {str(e)}")
            db.session.rollback()
            return None, None, str(e)

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
            
            db.session.commit()
            
            return cart, None
            
        except Exception as e:
            current_app.logger.error(f"Error clearing cart: {str(e)}")
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_user_cart_items_by_cart_id(user_id, cart_id):
        """
        Get cart items for a specific cart belonging to the user
        
        Args:
            user_id (str): User ID
            cart_id (str): Cart ID
            
        Returns:
            list: List of cart items or empty list
        """
        try:
            # Find the cart that belongs to the user and matches the cart_id
            cart = Cart.query.filter_by(
                id=cart_id,
                user_id=user_id,
                status='active'
            ).first()
            
            if not cart:
                return []
            
            # Return cart items
            return cart.cart_items
            
        except Exception as e:
            current_app.logger.error(f"Error fetching cart items: {str(e)}")
            return []