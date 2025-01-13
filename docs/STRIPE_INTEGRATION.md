# Stripe Payment Integration Guide

## Setup and Configuration

### Environment Variables
Add the following environment variables:
```
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
```

### Stripe Dashboard Configuration
1. Create a Stripe account at [stripe.com](https://stripe.com)
2. Obtain API keys from Stripe Dashboard
3. Set up Webhook Endpoint:
   - URL: `https://yourdomain.com/api/v1/payments/stripe/webhook`
   - Events to listen:
     - `payment_intent.succeeded`
     - `payment_intent.payment_failed`

### Frontend Integration
Use Stripe.js to create a payment form:
```javascript
const stripe = Stripe(STRIPE_PUBLISHABLE_KEY);
const elements = stripe.elements();

// Create payment intent
const { clientSecret } = await fetch('/api/v1/payments/stripe/create-intent', {
  method: 'POST',
  body: JSON.stringify({ order_id: 'your_order_id' })
});

// Confirm payment
const result = await stripe.confirmCardPayment(clientSecret, {
  payment_method: { card: cardElement }
});
```

### Backend Flow
1. Create Payment Intent
2. Send Client Secret to Frontend
3. Confirm Payment on Client
4. Stripe Webhook Verifies and Updates Order Status

### Currency Conversion

### UGX to USD Conversion
- Fixed exchange rate used for conversion
- Conversion happens server-side before creating Stripe Checkout Session
- Rates are dynamically calculated per transaction

### Checkout Process
1. Order total calculated in UGX
2. Converted to USD for Stripe processing
3. Line items show:
   - Book title
   - Book author
   - Quantity
   - Price in USD

### Example Frontend Flow
```javascript
async function initiateStripeCheckout(orderId) {
  try {
    const response = await fetch('/api/v1/payments/stripe/create-intent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${userToken}`
      },
      body: JSON.stringify({ order_id: orderId })
    });

    const data = await response.json();

    // Stripe Checkout
    const stripe = await loadStripe(STRIPE_PUBLISHABLE_KEY);
    const { error } = await stripe.redirectToCheckout({
      sessionId: data.checkout_session_id
    });

    if (error) {
      console.error('Checkout failed:', error);
    }
  } catch (error) {
    console.error('Payment initiation failed:', error);
  }
}
```

### Response Details
```json
{
  "checkout_session_id": "cs_test_...",
  "total_amount_usd": 25.50,
  "total_amount_ugx": 95000,
  "order_details": {
    "order_id": "order_123",
    "items_count": 2,
    "items": [
      {
        "book_title": "Things Fall Apart",
        "quantity": 1,
        "price_ugx": 45000,
        "price_usd": 12.15
      },
      {
        "book_title": "Purple Hibiscus",
        "quantity": 1,
        "price_ugx": 50000,
        "price_usd": 13.50
      }
    ]
  }
}
```

### Best Practices
- Always show prices in both UGX and USD
- Use real-time exchange rate APIs for more accurate conversion
- Handle currency conversion errors gracefully

### Security Considerations
- Never log full card details
- Use HTTPS
- Validate webhook signatures
- Implement proper error handling

### Troubleshooting
- Check Stripe Dashboard for detailed logs
- Verify webhook endpoint configuration
- Ensure correct API key usage

## Testing
Use Stripe's test card numbers:
- Success: 4242 4242 4242 4242
- Requires Authentication: 4000 0025 0000 3155
- Declined: 4000 0000 0000 0002

## Monitoring
- Set up Stripe Sigma queries
- Use Stripe Radar for fraud detection
- Monitor webhook delivery in Stripe Dashboard
