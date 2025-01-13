from flask import Blueprint, jsonify, request, current_app
from app.services.currency_service import CurrencyService

from app.api.v1 import bp

@bp.route('/currency/convert', methods=['GET', 'POST'])
def convert_currency():
    """
    Currency conversion endpoint supporting GET and POST
    
    Query/Form Parameters:
    - amount: float, amount to convert
    - base_currency: str, source currency code
    - target_currency: str, target currency code
    """
    try:
        # Log incoming request details
        current_app.logger.info(f"Currency conversion request received: {request.method}, {request.args or request.form}")
        
        # Get parameters from query string or form data
        if request.method == 'POST':
            amount = float(request.form.get('amount', request.json.get('amount', 1.0)))
            base_currency = (request.form.get('base_currency') or request.json.get('base_currency') or 'USD').upper()
            target_currency = (request.form.get('target_currency') or request.json.get('target_currency') or 'UGX').upper()
        else:
            amount = float(request.args.get('amount', 1.0))
            base_currency = request.args.get('base_currency', 'USD').upper()
            target_currency = request.args.get('target_currency', 'UGX').upper()
        
        # Perform conversion
        converted_amount = CurrencyService.convert_currency(
            amount=amount, 
            base_currency=base_currency, 
            target_currency=target_currency
        )
        
        # Log successful conversion
        current_app.logger.info(
            f"Conversion successful: {amount} {base_currency} -> {converted_amount} {target_currency}"
        )
        
        # Return conversion result
        return jsonify({
            'original_amount': amount,
            'base_currency': base_currency,
            'target_currency': target_currency,
            'converted_amount': converted_amount,
            'status': 'success'
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Currency conversion error: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 400
