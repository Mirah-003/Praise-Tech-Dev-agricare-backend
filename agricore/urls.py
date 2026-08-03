from django.urls import path
from .views import WhatsAppWebhookView, SMSWebhookView, USSDWebhookView, USSDSimulatorView

urlpatterns = [
    path('whatsapp/webhook/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    path('sms/webhook/', SMSWebhookView.as_view(), name='sms_webhook'),
    path('ussd/webhook/', USSDWebhookView.as_view(), name='ussd_webhook'),
    path('ussd/simulator/', USSDSimulatorView.as_view(), name='ussd_simulator_agricore'),
]