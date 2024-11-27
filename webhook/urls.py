from django.urls import path
from .views import WebhookView
from django.views.decorators.csrf import csrf_exempt

app_name = 'webhook'

urlpatterns = [
    path('', WebhookView.as_view() , name='webhook'),  
]
