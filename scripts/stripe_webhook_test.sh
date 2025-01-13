#!/bin/bash

# Stripe Webhook Local Testing Script

# Ensure Stripe CLI is logged in
echo "Checking Stripe CLI login status..."
stripe login

# Forward webhooks to local Flask server
echo "Forwarding Stripe webhooks to local server..."
stripe listen \
    --forward-to localhost:5000/api/v1/payments/stripe/webhook \
    --events payment_intent.succeeded,payment_intent.payment_failed,checkout.session.completed

# Optional: Create test webhook events
echo "To create test events, use:"
echo "stripe trigger payment_intent.succeeded"
echo "stripe trigger payment_intent.payment_failed"
