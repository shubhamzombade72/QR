from io import BytesIO
from reportlab.pdfgen import canvas
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import os

def generate_receipt_pdf(payment):
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    
    # Add receipt content
    p.drawString(100, 800, f"Receipt Number: {payment.receipt_set.first().receipt_number}")
    p.drawString(100, 780, f"Donor Name: {payment.donor.name}")
    p.drawString(100, 760, f"Amount: ₹{payment.amount}")
    p.drawString(100, 740, f"Transaction ID: {payment.transaction_id}")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer

def send_receipt_email(payment, pdf_buffer):
    try:
        # Prepare email content
        context = {
            'donor_name': payment.donor.name,
            'amount': payment.amount,
            'receipt_number': payment.receipt_set.first().receipt_number,
            'transaction_id': payment.transaction_id
        }
        
        # Create email message
        email = EmailMessage(
            subject='Temple Donation Receipt',
            body=render_to_string('payments/email/receipt_email.html', context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[payment.donor.email],
        )
        email.content_subtype = "html"  # Set content type to HTML
        
        # Attach PDF
        email.attach(
            f'receipt_{payment.receipt_set.first().receipt_number}.pdf',
            pdf_buffer.getvalue(),
            'application/pdf'
        )
        
        # Send email
        email.send(fail_silently=False)
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False