# urls.py
from django.urls import path
from .views import WebhookView

urlpatterns = [
    path('', WebhookView.as_view(), name='webhook_view'),
]
