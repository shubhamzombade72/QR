from django.contrib import admin
from .models import Donor, DonationType, Payment, Receipt, PaymentHistory

@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
	list_display = ('name', 'contact', 'email', 'created_at')
	search_fields = ('name', 'contact', 'email', 'pan_number')
	list_filter = ('created_at',)

@admin.register(DonationType)
class DonationTypeAdmin(admin.ModelAdmin):
	list_display = ('name', 'minimum_amount', 'is_active')
	list_filter = ('is_active',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = ('donor', 'amount', 'payment_status', 'transaction_id', 'created_at')
	list_filter = ('payment_status', 'payment_method', 'created_at')
	search_fields = ('donor__name', 'transaction_id')
	readonly_fields = ('created_at', 'updated_at')

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
	list_display = ('receipt_number', 'payment', 'sent_to_email', 'created_at')
	list_filter = ('sent_to_email', 'created_at')
	search_fields = ('receipt_number', 'payment__donor__name')
	readonly_fields = ('created_at', 'email_sent_at')

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
	list_display = ('payment', 'status', 'created_at')
	list_filter = ('status', 'created_at')
	search_fields = ('payment__donor__name', 'notes')
	readonly_fields = ('created_at',)