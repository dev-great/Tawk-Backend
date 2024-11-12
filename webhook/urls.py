from django.urls import path
from .views import WebhookView

app_name = 'webhook'

urlpatterns = [
    path('', WebhookView.as_view(), name='web-hook'),  
]
