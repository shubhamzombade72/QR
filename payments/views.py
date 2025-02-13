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
from .models import Donor, DonationType, Payment, Receipt
from .utils import generate_receipt_pdf, send_receipt_email
import razorpay
import json

# Initialize Razorpay client
razorpay_client = razorpay.Client(
	auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

def payment_form(request):
	if request.method == 'POST':
		try:
			name = request.POST.get('name')
			mobile = request.POST.get('mobile')
			email = request.POST.get('email')
			amount = request.POST.get('amount')
			
			if not all([name, mobile, amount]):
				messages.error(request, 'Please fill all the required fields')
				return redirect('payments:payment_form')
			
			# Create or get donor
			donor, created = Donor.objects.get_or_create(
				mobile_number=mobile,
				defaults={
					'full_name': name,
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

			# Create Razorpay order
			data = {
				"amount": int(float(amount) * 100),  # Amount in paise
				"currency": "INR",
				"receipt": str(payment.id) # Use payment ID as receipt
			}
			razorpay_order = razorpay_client.order.create(data=data)
			payment.transaction_id = razorpay_order['id']
			payment.save()

			context = {
				'payment': payment,
				'show_qr': True,
				'razorpay_order_id': razorpay_order['id'],
				'razorpay_key_id': settings.RAZORPAY_KEY_ID,
				'donor_name': name,
				'donor_email': email if email else '',  # Add email to context
				'donor_contact': mobile,
				'amount': int(float(amount) * 100),  # Amount in paise
			}
			
			messages.success(request, 'Please complete the payment')
			return render(request, 'payments/payment_form.html', context)
			
		except Exception as e:
			messages.error(request, f'Error creating Razorpay order: {str(e)}')
			return redirect('payments:payment_form')
	else:
		# Create Razorpay order before rendering the form
		try:
			# Placeholder amount - replace with logic to get default amount
			amount = 100
			data = {
				"amount": int(float(amount) * 100),  # Amount in paise
				"currency": "INR",
				"receipt": "test_receipt" # Placeholder receipt - will be updated later
			}
			razorpay_order = razorpay_client.order.create(data=data)
			context = {
				'show_qr': False,
				'razorpay_order_id': razorpay_order['id'],
				'razorpay_key_id': settings.RAZORPAY_KEY_ID,
				'amount': amount
			}
			return render(request, 'payments/payment_form.html', context)
		except Exception as e:
			messages.error(request, f'Error creating Razorpay order: {str(e)}')
			return redirect('payments:payment_form')

@csrf_exempt
def payment_webhook(request):
	print("\n=== Payment Webhook Called ===")
	print(f"Request Method: {request.method}")
	if request.method == 'POST':
		try:
			print("Parsing request body...")
			request_body = request.body.decode('utf-8')
			print(f"Request Body: {request_body}")
			data = json.loads(request_body)
			print(f"Parsed Data: {data}")
			
			razorpay_payment_id = data.get('razorpay_payment_id')
			razorpay_order_id = data.get('razorpay_order_id')
			razorpay_signature = data.get('razorpay_signature')
			
			print(f"Payment ID: {razorpay_payment_id}")
			print(f"Order ID: {razorpay_order_id}")
			print(f"Signature: {razorpay_signature}")
			
			if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
				print("Missing payment parameters")
				return JsonResponse({'status': 'error', 'message': 'Missing payment parameters'})
			
			try:
				print("Finding payment record...")
				payment = Payment.objects.get(transaction_id=razorpay_order_id)
				print(f"Found payment for donor: {payment.donor.full_name}")
				
				print("Verifying payment signature...")
				client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
				params_dict = {
					'razorpay_order_id': razorpay_order_id,
					'razorpay_payment_id': razorpay_payment_id,
					'razorpay_signature': razorpay_signature
				}
				client.utility.verify_payment_signature(params_dict)
				print("Payment signature verified")
				
				payment.payment_status = 'SUCCESS'
				payment.save()
				print("Payment status updated to SUCCESS")
				
				print("Generating receipt...")
				receipt = Receipt.objects.create(payment=payment)
				receipt.receipt_number = receipt.generate_receipt_number()
				receipt.save()
				print(f"Receipt generated with number: {receipt.receipt_number}")
				
				print("Generating PDF receipt...")
				pdf_buffer = generate_receipt_pdf(payment)
				
				print("Saving PDF to invoice_pdf field...")
				payment.invoice_pdf.save(
					f'receipt_{receipt.receipt_number}.pdf',
					ContentFile(pdf_buffer.getvalue()),
					save=True
				)
				print("PDF saved successfully")
				
				if payment.donor.email:
					print(f"Sending email to: {payment.donor.email}")
					email_sent = send_receipt_email(payment, pdf_buffer)
					if email_sent:
						receipt.sent_to_email = True
						receipt.save()
						print("Email sent successfully")
					else:
						print("Failed to send email")
				else:
					print("No email address provided for donor")
				
				return JsonResponse({'status': 'SUCCESS'})
				
			except Payment.DoesNotExist:
				print(f"Payment not found with order ID: {razorpay_order_id}")
				return JsonResponse({'status': 'error', 'message': 'Payment not found'})
			except Exception as e:
				print(f"Error processing payment: {str(e)}")
				return JsonResponse({'status': 'error', 'message': str(e)})
				
		except json.JSONDecodeError as e:
			print(f"Invalid JSON data: {str(e)}")
			return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
		except Exception as e:
			print(f"Webhook error: {str(e)}")
			return JsonResponse({'status': 'error', 'message': str(e)})
	
	return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def dashboard(request):
    # Your view logic here
    pass