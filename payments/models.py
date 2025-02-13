# filepath: /c:/Users/ADMIN/OneDrive/Desktop/QR Generator/payments/models.py
from django.db import models
from django.utils import timezone

class Donor(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    contact = models.CharField(max_length=15)
    address = models.TextField(blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

class DonationType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Payment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='payments')
    donation_type = models.ForeignKey(DonationType, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=50, default='Razorpay')
    invoice_pdf = models.FileField(upload_to='invoices/', null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.donor.name} - ₹{self.amount} - {self.payment_status}"

    class Meta:
        ordering = ['-created_at']

class Receipt(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='receipts')
    receipt_number = models.CharField(max_length=20, unique=True)
    receipt_pdf = models.FileField(upload_to='receipts/', null=True, blank=True)
    sent_to_email = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_receipt_number(self):
        from datetime import datetime
        prefix = 'TR'
        date_part = datetime.now().strftime('%y%m')
        last_receipt = Receipt.objects.filter(receipt_number__startswith=f'{prefix}{date_part}').order_by('-receipt_number').first()
        
        if last_receipt:
            sequence = int(last_receipt.receipt_number[-4:]) + 1
        else:
            sequence = 1
            
        return f'{prefix}{date_part}{sequence:04d}'

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = self.generate_receipt_number()
        if self.sent_to_email and not self.email_sent_at:
            self.email_sent_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Receipt {self.receipt_number} for {self.payment.donor.name}"

    class Meta:
        ordering = ['-created_at']

class PaymentHistory(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=20)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.payment.donor.name} - {self.status} at {self.created_at}"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Payment histories'