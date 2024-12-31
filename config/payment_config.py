from enum import Enum, auto

class PaymentMethod(Enum):
    """
    Enumeration of supported payment methods
    """
    MOBILE_MONEY_MTN = "mobile_money_mtn"
    MOBILE_MONEY_AIRTEL = "mobile_money_airtel"
    CREDIT_CARD = "credit_card"  # For future Stripe/Link integration
    CASH_ON_DELIVERY = "cash_on_delivery"

class PaymentConfiguration:
    """
    Central configuration for payment methods and providers
    """
    SUPPORTED_METHODS = {
        PaymentMethod.MOBILE_MONEY_MTN: {
            "name": "MTN Mobile Money",
            "type": "mobile_money",
            "provider": "MTN Uganda",
            "requires_phone_number": True,
            "currency": "UGX",
            "min_amount": 500,
            "max_amount": 5000000,
            "is_online_payment": True
        },
        PaymentMethod.MOBILE_MONEY_AIRTEL: {
            "name": "Airtel Money",
            "type": "mobile_money", 
            "provider": "Airtel Uganda",
            "requires_phone_number": True,
            "currency": "UGX",
            "min_amount": 500,
            "max_amount": 5000000,
            "is_online_payment": True
        },
        PaymentMethod.CREDIT_CARD: {
            "name": "Credit Card",
            "type": "card",
            "provider": "Stripe",
            "requires_phone_number": False,
            "currency": "USD",
            "min_amount": 1,
            "max_amount": 1000,
            "is_online_payment": True
        },
        PaymentMethod.CASH_ON_DELIVERY: {
            "name": "Cash on Delivery",
            "type": "offline",
            "provider": "Local Delivery",
            "requires_phone_number": True,
            "currency": "UGX",
            "min_amount": 1000,
            "max_amount": 1000000,
            "is_online_payment": False,
            "additional_fees": 5000  # Delivery fee
        }
    }

    @classmethod
    def get_payment_method_details(cls, method):
        """
        Retrieve details for a specific payment method
        
        Args:
            method (PaymentMethod): Payment method to retrieve details for
        
        Returns:
            dict: Payment method configuration
        """
        return cls.SUPPORTED_METHODS.get(method)

    @classmethod
    def is_method_supported(cls, method):
        """
        Check if a payment method is supported
        
        Args:
            method (str): Payment method to check
        
        Returns:
            bool: Whether the method is supported
        """
        return method in [m.value for m in PaymentMethod]

    @classmethod
    def get_supported_methods(cls):
        """
        Get all supported payment methods
        
        Returns:
            list: List of supported payment methods
        """
        return list(cls.SUPPORTED_METHODS.keys())
