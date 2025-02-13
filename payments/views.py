from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile
from .models import Donor, DonationType, Payment, Receipt, PaymentHistory
from .utils import generate_receipt_pdf, send_receipt_email
import json
import requests
import hmac
import hashlib

def create_payment_history(payment, status, notes=None):
	PaymentHistory.objects.create(
		payment=payment,
		status=status,
		notes=notes
	)

def create_razorpay_order(amount, receipt):
	url = "https://api.razorpay.com/v1/orders"
	auth = (settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
	data = {
		"amount": amount,
		"currency": "INR",
		"receipt": receipt,
		"notes": {
			"payment_for": "Temple Donation"
		}
	}
	try:
		response = requests.post(url, json=data, auth=auth)
		response.raise_for_status()  # Raises an HTTPError for bad responses
		return response.json()
	except requests.exceptions.RequestException as e:
		print(f"Error creating Razorpay order: {str(e)}")
		raise Exception(f"Error creating Razorpay order: {str(e)}")

def verify_razorpay_signature(params_dict):
	msg = f"{params_dict['razorpay_order_id']}|{params_dict['razorpay_payment_id']}"
	generated_signature = hmac.new(
		settings.RAZORPAY_KEY_SECRET.encode(),
		msg.encode(),
		hashlib.sha256
	).hexdigest()
	return hmac.compare_digest(generated_signature, params_dict['razorpay_signature'])

def payment_form(request):
	if request.method == 'POST':
		try:
			name = request.POST.get('name')
			mobile = request.POST.get('mobile')
			email = request.POST.get('email')
			amount = request.POST.get('amount')
			
			if not all([name, mobile, amount]):
				messages.error(request, 'Please fill all the required fields')
				return render(request, 'payments/payment_form.html', {'show_qr': False})
			
			# Create or get donor
			donor, created = Donor.objects.get_or_create(
				contact=mobile,
				defaults={
					'name': name,
					'email': email
				}
			)
			
			# Update email if provided
			if not created and email:
				donor.email = email
				donor.save()
			
			# Get default donation type
			donation_type, _ = DonationType.objects.get_or_create(
				name='General Donation',
				defaults={'minimum_amount': 0}
			)
			
			# Create payment record
			payment = Payment.objects.create(
				donor=donor,
				donation_type=donation_type,
				amount=amount,
				transaction_id='',  # Will be updated with Razorpay order ID
				payment_status='PENDING'
			)
			create_payment_history(payment, 'PENDING', 'Payment initiated')

			# Create Razorpay order
			razorpay_order = create_razorpay_order(
				int(float(amount) * 100),  # Amount in paise
				str(payment.id)
			)
			
			if 'error' in razorpay_order:
				messages.error(request, f"Razorpay Error: {razorpay_order['error']['description']}")
				return render(request, 'payments/payment_form.html', {'show_qr': False})
				
			payment.transaction_id = razorpay_order['id']
			payment.save()

			context = {
				'payment': payment,
				'show_qr': True,
				'razorpay_order_id': razorpay_order['id'],
				'razorpay_key_id': settings.RAZORPAY_KEY_ID,
				'donor_name': donor.name,
				'donor_email': email if email else '',  # Add email to context
				'donor_contact': mobile,
				'amount': int(float(amount) * 100),  # Amount in paise
			}
			
			messages.success(request, 'Please complete the payment')
			return render(request, 'payments/payment_form.html', context)
			
		except Exception as e:
			messages.error(request, f'Error creating Razorpay order: {str(e)}')
			return render(request, 'payments/payment_form.html', {'show_qr': False})
	else:
		try:
			amount = 100
			razorpay_order = create_razorpay_order(
				int(float(amount) * 100),
				"test_receipt"
			)

			context = {
				'show_qr': False,
				'razorpay_order_id': razorpay_order['id'],
				'razorpay_key_id': settings.RAZORPAY_KEY_ID,
				'amount': amount
			}
			return render(request, 'payments/payment_form.html', context)
		except Exception as e:
			messages.error(request, f'Error creating Razorpay order: {str(e)}')
			return render(request, 'payments/payment_form.html', {'show_qr': False})


@csrf_exempt
def payment_webhook(request):
	print("\n=== Payment Webhook Called ===")
	if request.method == 'POST':
		try:
			data = json.loads(request.body.decode('utf-8'))
			razorpay_payment_id = data.get('razorpay_payment_id')
			razorpay_order_id = data.get('razorpay_order_id')
			razorpay_signature = data.get('razorpay_signature')
			
			if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
				return JsonResponse({'status': 'error', 'message': 'Missing payment parameters'})
			
			try:
				payment = Payment.objects.get(transaction_id=razorpay_order_id)
				
				params_dict = {
					'razorpay_order_id': razorpay_order_id,
					'razorpay_payment_id': razorpay_payment_id,
					'razorpay_signature': razorpay_signature
				}
				
				if not verify_razorpay_signature(params_dict):
					payment.payment_status = 'FAILED'
					payment.save()
					create_payment_history(payment, 'FAILED', 'Invalid signature')
					return JsonResponse({'status': 'error', 'message': 'Invalid signature'})
				
				payment.payment_status = 'SUCCESS'
				payment.save()
				create_payment_history(payment, 'SUCCESS', f'Payment completed with ID: {razorpay_payment_id}')
				
				# Create receipt
				receipt = Receipt.objects.create(payment=payment)
				receipt.save()  # This will trigger the auto-generation of receipt number
				
				# Generate and save PDF
				pdf_buffer = generate_receipt_pdf(payment)
				payment.invoice_pdf.save(
					f'receipt_{receipt.receipt_number}.pdf',
					ContentFile(pdf_buffer.getvalue()),
					save=True
				)
				
				# Send email if email address exists
				if payment.donor.email:
					email_sent = send_receipt_email(payment, pdf_buffer)
					if email_sent:
						receipt.sent_to_email = True
						receipt.save()
				
				return JsonResponse({'status': 'SUCCESS'})
				
			except Payment.DoesNotExist:
				return JsonResponse({'status': 'error', 'message': 'Payment not found'})
			except Exception as e:
				if 'payment' in locals():
					payment.payment_status = 'FAILED'
					payment.save()
					create_payment_history(payment, 'FAILED', f'Error: {str(e)}')
				return JsonResponse({'status': 'error', 'message': str(e)})
				
		except json.JSONDecodeError:
			return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
		except Exception as e:
			return JsonResponse({'status': 'error', 'message': str(e)})
	
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


def initiate_payment(request):

    if request.method == "POST":
        amount = request.POST.get("amount")
        order = create_order(amount)
        return JsonResponse(order)
    return render(request, "initiate_payment.html")

def payment_callback(request):
	if request.method == "POST":
		response_data = request.POST
		try:
			verify_payment_signature(response_data)
			# Payment is successful
			return JsonResponse({"status": "Payment successful"})
		except:
			# Payment verification failed
			return JsonResponse({"status": "Payment verification failed"})
	return JsonResponse({"status": "Invalid request"})
