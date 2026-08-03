"""
URL configuration for core project.
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from agricore.views import WhatsAppWebhookView, SMSWebhookView, USSDWebhookView, USSDSimulatorView

schema_view = get_schema_view(
    openapi.Info(
        title="Agricare AI API & USSD Backend",
        default_version='v1',
        description="Production REST, WhatsApp Webhook, and GSM USSD gateway for the Agricare AI poultry veterinary system.",
        contact=openapi.Contact(email="support@agricare.ai"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

def home(request):
    return HttpResponse(
        "<h1>Agricare AI Gateway is Running</h1>"
        "<p>Access the <a href='/swagger/'>Swagger API Docs</a> or test the <a href='/ussd/simulator/'>GSM USSD Feature Phone Simulator</a>.</p>"
    )

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('agricore/', include('agricore.urls')),

    # Direct Webhook Paths for Twilio & African Telcos
    path('webhook/whatsapp/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook_direct'),
    path('webhook/sms/', SMSWebhookView.as_view(), name='sms_webhook_direct'),
    path('webhook/ussd/', USSDWebhookView.as_view(), name='ussd_webhook_direct'),
    path('ussd/', USSDWebhookView.as_view(), name='ussd_direct'),
    path('ussd/simulator/', USSDSimulatorView.as_view(), name='ussd_simulator'),

    # Swagger / OpenAPI Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
