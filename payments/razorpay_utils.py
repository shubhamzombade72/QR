import requests
import hmac
import hashlib
from django.conf import settings

def create_order(amount, currency="INR", receipt=None, notes=None):
    url = "https://api.razorpay.com/v1/orders"
    auth = (settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    data = {
        "amount": amount,
        "currency": currency,
        "receipt": receipt,
        "notes": notes
    }
    response = requests.post(url, json=data, auth=auth)
    return response.json()

def verify_payment_signature(response_data):
    msg = f"{response_data['razorpay_order_id']}|{response_data['razorpay_payment_id']}"
    generated_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        msg.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(generated_signature, response_data['razorpay_signature'])
