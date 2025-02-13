from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
	path('', views.payment_form, name='payment_form'),
	path('webhook/payment/', views.payment_webhook, name='payment_webhook'),
]
