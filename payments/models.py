# filepath: /c:/Users/ADMIN/OneDrive/Desktop/QR Generator/payments/models.py
from django.db import models

class Donor(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    contact = models.CharField(max_length=15)

    def __str__(self):
        return self.name

class DonationType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Payment(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100)
    invoice_pdf = models.FileField(upload_to='invoices/', null=True, blank=True)

    def __str__(self):
        return f"{self.donor.name} - {self.amount}"

class Receipt(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    receipt_pdf = models.FileField(upload_to='receipts/', null=True, blank=True)

    def __str__(self):
        return f"Receipt for {self.payment.donor.name}"