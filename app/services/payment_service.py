from abc import ABC, abstractmethod
from enum import Enum
import uuid
from typing import Dict, Any, Tuple, Optional
import os
import logging
import stripe
from flask import current_app

class PaymentStatus(Enum):
    PENDING = 'pending'
    SUCCESS = 'success'
    FAILED = 'failed'
    REFUNDED = 'refunded'

class BasePaymentService(ABC):
    """
    Abstract base class for payment services
    Defines common interface for payment processing
    """
    
    @abstractmethod
    def initialize_payment(
        self, 
        amount: float, 
        currency: str, 
        order_id: str = None, 
        **kwargs
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Initialize a payment transaction
        
        Args:
            amount (float): Transaction amount
            currency (str): Transaction currency
            order_id (str, optional): Unique order identifier
            **kwargs: Additional payment method specific parameters
        
        Returns:
            Tuple of (success_status, transaction_details)
        """
        pass
    
    @abstractmethod
    def verify_payment(self, transaction_id: str) -> PaymentStatus:
        """
        Verify the status of a payment transaction
        
        Args:
            transaction_id (str): Unique transaction identifier
        
        Returns:
            PaymentStatus: Current status of the transaction
        """
        pass
    
    @abstractmethod
    def refund_payment(self, transaction_id: str) -> bool:
        """
        Refund a completed payment transaction
        
        Args:
            transaction_id (str): Unique transaction identifier
        
        Returns:
            bool: Whether refund was successful
        """
        pass
    
    def generate_transaction_id(self) -> str:
        """
        Generate a unique transaction identifier
        
        Returns:
            str: Unique transaction ID
        """
        return str(uuid.uuid4())
    
    def validate_payment_parameters(
        self, 
        amount: float, 
        currency: str, 
        min_amount: float = 0, 
        max_amount: float = float('inf')
    ) -> bool:
        """
        Validate basic payment parameters
        
        Args:
            amount (float): Transaction amount
            currency (str): Transaction currency
            min_amount (float, optional): Minimum allowed amount
            max_amount (float, optional): Maximum allowed amount
        
        Returns:
            bool: Whether parameters are valid
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if amount < min_amount:
            raise ValueError(f"Amount must be at least {min_amount}")
        
        if amount > max_amount:
            raise ValueError(f"Amount cannot exceed {max_amount}")
        
        return True

class StripePaymentService(BasePaymentService):
    """
    Stripe-specific payment service implementation
    """
    def __init__(self):
        """
        Initialize Stripe configuration
        
        Raises:
            ValueError: If Stripe Secret Key is not configured
        """
        # Explicitly set Stripe API key
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
        
        # More robust configuration check
        if not stripe.api_key:
            current_app.logger.error("Stripe Secret Key is missing from configuration")
            raise ValueError(
                "Stripe Secret Key is not configured. "
                "Please set STRIPE_SECRET_KEY in your environment or configuration."
            )
        
        # Set webhook secret
        self.webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
        
        # Validate additional configuration
        if not self.webhook_secret:
            current_app.logger.warning("Stripe Webhook Secret is not configured")
    
    def initialize_payment(
        self, 
        amount: float, 
        currency: str = 'usd', 
        order_id: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Create a Stripe Payment Intent
        
        Args:
            amount (float): Transaction amount
            currency (str, optional): Transaction currency. Defaults to 'usd'.
            order_id (str, optional): Unique order identifier
        
        Returns:
            Tuple of (success_status, transaction_details)
        """
        try:
            # Create Payment Intent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                metadata={'order_id': order_id} if order_id else {}
            )
            
            return True, {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id
            }
        
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe Payment Intent Error: {str(e)}")
            return False, {
                'error': str(e),
                'type': type(e).__name__
            }
    
    def verify_payment(self, transaction_id: str) -> PaymentStatus:
        """
        Verify the status of a Stripe Payment Intent
        
        Args:
            transaction_id (str): Stripe Payment Intent ID
        
        Returns:
            PaymentStatus: Current status of the transaction
        """
        try:
            # Retrieve Payment Intent
            intent = stripe.PaymentIntent.retrieve(transaction_id)
            
            # Map Stripe status to our PaymentStatus
            status_mapping = {
                'succeeded': PaymentStatus.SUCCESS,
                'requires_payment_method': PaymentStatus.PENDING,
                'requires_confirmation': PaymentStatus.PENDING,
                'requires_action': PaymentStatus.PENDING,
                'canceled': PaymentStatus.FAILED,
                'processing': PaymentStatus.PENDING
            }
            
            return status_mapping.get(intent.status, PaymentStatus.FAILED)
        
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe Payment Verification Error: {str(e)}")
            return PaymentStatus.FAILED
    
    def refund_payment(self, transaction_id: str) -> bool:
        """
        Refund a Stripe Payment Intent
        
        Args:
            transaction_id (str): Stripe Payment Intent ID
        
        Returns:
            bool: Whether refund was successful
        """
        try:
            refund = stripe.Refund.create(payment_intent=transaction_id)
            return refund.status == 'succeeded'
        
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe Refund Error: {str(e)}")
            return False

    def handle_webhook(self, payload: str, sig_header: str) -> Dict[str, Any]:
        """
        Handle incoming Stripe webhook events
        
        Args:
            payload (str): Raw webhook payload
            sig_header (str): Signature header for verification
        
        Returns:
            Dict of processed webhook event details
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            
            # Process different event types
            if event.type == 'payment_intent.succeeded':
                payment_intent = event.data.object
                return {
                    'event_type': 'payment_success',
                    'order_id': payment_intent.metadata.get('order_id'),
                    'payment_intent_id': payment_intent.id
                }
            
            elif event.type == 'payment_intent.payment_failed':
                payment_intent = event.data.object
                return {
                    'event_type': 'payment_failed',
                    'order_id': payment_intent.metadata.get('order_id'),
                    'payment_intent_id': payment_intent.id
                }
            
            return {'event_type': 'unhandled', 'raw_event': event.type}
        
        except ValueError as e:
            # Invalid payload
            logging.error(f"Invalid Stripe webhook payload: {str(e)}")
            raise
        
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            logging.error(f"Invalid Stripe webhook signature: {str(e)}")
            raise
