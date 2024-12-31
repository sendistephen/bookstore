from abc import ABC, abstractmethod
from enum import Enum
import uuid
from typing import Dict, Any, Tuple

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
