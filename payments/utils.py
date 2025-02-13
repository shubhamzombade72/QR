from io import BytesIO
from reportlab.pdfgen import canvas
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import os

def generate_receipt_pdf(payment):
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    
    # Get the latest receipt
    receipt = payment.receipts.first()  # Using related_name from model
    
    # Add receipt content
    p.drawString(100, 800, f"Receipt Number: {receipt.receipt_number if receipt else 'N/A'}")
    p.drawString(100, 780, f"Donor Name: {payment.donor.name}")
    p.drawString(100, 760, f"Amount: ₹{payment.amount}")
    p.drawString(100, 740, f"Transaction ID: {payment.transaction_id}")
    p.drawString(100, 720, f"Date: {payment.created_at.strftime('%d-%m-%Y')}")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer

def send_receipt_email(payment, pdf_buffer):
    try:
        receipt = payment.receipts.first()
        if not receipt:
            return False

        # Prepare email content
        context = {
            'donor_name': payment.donor.name,
            'amount': payment.amount,
            'receipt_number': receipt.receipt_number,
            'transaction_id': payment.transaction_id,
            'date': payment.created_at.strftime('%d-%m-%Y')
        }
        
        # Create email message
        email = EmailMessage(
            subject='Temple Donation Receipt',
            body=render_to_string('payments/email/receipt_email.html', context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[payment.donor.email],
        )
        email.content_subtype = "html"
        
        # Attach PDF
        email.attach(
            f'receipt_{receipt.receipt_number}.pdf',
            pdf_buffer.getvalue(),
            'application/pdf'
        )
        
        # Send email
        email.send(fail_silently=False)
        
        # Update receipt email status
        receipt.sent_to_email = True
        receipt.email_sent_at = timezone.now()
        receipt.save()
        
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False