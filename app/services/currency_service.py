import requests
from flask import current_app
from functools import lru_cache
from datetime import datetime, timedelta
import logging
import os

class CurrencyService:
    """
    Service for handling currency conversions with caching and external API support
    using Free Currency API
    """
    _rate_cache = {}
    
    # Hardcoded fallback rates (as of early 2025)
    _FALLBACK_RATES = {
        ('USD', 'UGX'): 3750.0,  # 1 USD = 3750 UGX (approximate)
        ('UGX', 'USD'): 1/3750.0  # 1 UGX = 0.000267 USD
    }

    @classmethod
    @lru_cache(maxsize=128)
    def get_exchange_rate(
        cls, 
        base_currency: str = 'USD', 
        target_currency: str = 'UGX', 
        force_refresh: bool = False
    ) -> float:
        """
        Retrieve the current exchange rate with intelligent caching
        
        Args:
            base_currency (str): Base currency code. Defaults to 'USD'
            target_currency (str): Target currency code. Defaults to 'UGX'
            force_refresh (bool): Force fetching a new rate
        
        Returns:
            float: Exchange rate
        """
        # Normalize currencies
        base_currency = base_currency.upper()
        target_currency = target_currency.upper()
        
        # Create a unique cache key
        cache_key = f"{base_currency}_{target_currency}"
        
        # Check cache first
        cached_rate = cls._rate_cache.get(cache_key)
        current_time = datetime.utcnow()
        
        # Return cached rate if it's fresh and not forced to refresh
        if cached_rate and not force_refresh:
            if current_time - cached_rate['timestamp'] < timedelta(hours=1):
                return cached_rate['rate']
        
        try:
            # Fetch API key from environment
            api_key = os.getenv('EXCHANGE_RATES_API_KEY')
            
            # Debug logging for API key
            current_app.logger.info(f"Attempting to fetch exchange rate. API Key present: {bool(api_key)}")
            
            # If no API key, use fallback rate
            if not api_key:
                current_app.logger.warning(
                    f"No API key found for currency conversion. "
                    f"Using fallback rate for {base_currency} to {target_currency}"
                )
                return cls._FALLBACK_RATES.get((base_currency, target_currency), 1.0)
            
            # Always convert via USD for non-standard currencies
            if base_currency not in ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD']:
                current_app.logger.info(f"Converting {base_currency} via USD")
                
                # First get USD rate
                usd_rate = 1.0  # Default to 1
                
                # Construct API URL for USD conversion
                usd_url = f"https://api.freecurrencyapi.com/v1/latest?apikey={api_key}&base_currency=USD&currencies={base_currency}"
                
                try:
                    usd_response = requests.get(usd_url, timeout=10)
                    usd_response.raise_for_status()
                    usd_data = usd_response.json()
                    
                    # If we have a valid rate, use it
                    if 'data' in usd_data and base_currency in usd_data['data']:
                        usd_rate = 1 / usd_data['data'][base_currency]
                        current_app.logger.info(f"USD to {base_currency} rate: {usd_rate}")
                except Exception as usd_error:
                    current_app.logger.warning(f"USD conversion error: {usd_error}")
                
                # Construct API URL for final conversion
                url = f"https://api.freecurrencyapi.com/v1/latest?apikey={api_key}&base_currency=USD&currencies={target_currency}"
            else:
                # Standard currencies can use direct conversion
                url = f"https://api.freecurrencyapi.com/v1/latest?apikey={api_key}&base_currency={base_currency}&currencies={target_currency}"
            
            # Debug logging for API request
            current_app.logger.info(f"Making API request to: {url}")
            
            # Make API request
            response = requests.get(url, timeout=10)
            
            # Log full response details
            current_app.logger.info(f"API Response Status Code: {response.status_code}")
            current_app.logger.info(f"API Response Headers: {response.headers}")
            current_app.logger.info(f"API Response Content: {response.text}")
            
            # Raise exception for bad responses
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Log parsed data
            current_app.logger.info(f"Parsed API Response: {data}")
            
            # Extract exchange rate
            if 'data' in data and target_currency in data['data']:
                rate = data['data'][target_currency]
                
                # If rate is 1 or 0, use fallback
                if rate in (0, 1):
                    current_app.logger.warning(
                        f"Received invalid rate ({rate}) for {base_currency} to {target_currency}. "
                        f"Using fallback rate."
                    )
                    rate = cls._FALLBACK_RATES.get((base_currency, target_currency), 1.0)
                
                # Cache the rate
                cls._rate_cache[cache_key] = {
                    'rate': rate,
                    'timestamp': current_time
                }
                
                current_app.logger.info(f"Successfully retrieved rate: {rate}")
                return rate
            
            # If parsing fails, use fallback rate
            current_app.logger.warning(
                f"Failed to parse exchange rate from API response. "
                f"Using fallback rate for {base_currency} to {target_currency}"
            )
            return cls._FALLBACK_RATES.get((base_currency, target_currency), 1.0)
        
        except requests.RequestException as e:
            current_app.logger.error(f"API request error: {e}")
            
            # Use fallback rate
            fallback_rate = cls._FALLBACK_RATES.get((base_currency, target_currency), 1.0)
            current_app.logger.warning(
                f"Using fallback rate due to API request error: "
                f"{base_currency} to {target_currency} = {fallback_rate}"
            )
            return fallback_rate
        except Exception as e:
            current_app.logger.error(f"Unexpected error in get_exchange_rate: {e}")
            
            # Use fallback rate
            fallback_rate = cls._FALLBACK_RATES.get((base_currency, target_currency), 1.0)
            current_app.logger.warning(
                f"Using fallback rate due to unexpected error: "
                f"{base_currency} to {target_currency} = {fallback_rate}"
            )
            return fallback_rate

    @classmethod
    def convert_currency(
        cls, 
        amount: float, 
        base_currency: str = 'USD', 
        target_currency: str = 'UGX'
    ) -> float:
        """
        Convert an amount between currencies
        
        Args:
            amount (float): Amount to convert
            base_currency (str): Source currency code (default: USD)
            target_currency (str): Target currency code (default: UGX)
        
        Returns:
            float: Converted amount
        """
        try:
            # Normalize currency codes
            base_currency = base_currency.upper()
            target_currency = target_currency.upper()
            
            # Log input parameters with more detail
            current_app.logger.info(
                f"Currency Conversion Attempt: "
                f"Amount: {amount}, "
                f"Base Currency: {base_currency}, "
                f"Target Currency: {target_currency}"
            )
            
            # Ensure positive amount
            amount = max(0, float(amount))
            
            # If currencies are the same, return the original amount
            if base_currency == target_currency:
                current_app.logger.info(f"Same currency conversion: {amount}")
                return amount
            
            # Always convert via USD
            if base_currency != 'USD':
                # First convert base currency to USD
                usd_rate = cls.get_exchange_rate(base_currency, 'USD')
                amount_in_usd = amount / usd_rate
                current_app.logger.info(
                    f"Converted {amount} {base_currency} to {amount_in_usd} USD "
                    f"(rate: {usd_rate}, calculation: {amount} / {usd_rate})"
                )
            else:
                amount_in_usd = amount
            
            # Then convert USD to target currency
            rate = cls.get_exchange_rate('USD', target_currency)
            
            # Perform conversion
            converted_amount = amount_in_usd * rate
            
            # Log conversion details with more precision
            current_app.logger.info(
                f"Final Conversion: "
                f"{amount_in_usd} USD = {converted_amount} {target_currency} "
                f"(rate: {rate}, calculation: {amount_in_usd} * {rate})"
            )
            
            # Round to 2 decimal places
            return round(converted_amount, 2)
        
        except Exception as e:
            current_app.logger.error(
                f"Currency conversion error: {e}. "
                f"Details - Amount: {amount}, "
                f"Base Currency: {base_currency}, "
                f"Target Currency: {target_currency}"
            )
            
            # Fallback to hardcoded rate if all else fails
            try:
                # Use a more precise fallback rate
                fallback_rate = cls._FALLBACK_RATES.get((base_currency, target_currency), 1/3750.0)
                converted_amount = amount * fallback_rate
                current_app.logger.warning(
                    f"Using hardcoded fallback rate: "
                    f"{amount} {base_currency} = {converted_amount} {target_currency} "
                    f"(fallback rate: {fallback_rate})"
                )
                return round(converted_amount, 2)
            except Exception as fallback_error:
                current_app.logger.error(
                    f"Fallback conversion failed: {fallback_error}. "
                    f"Original error: {e}"
                )
                return 0.0
