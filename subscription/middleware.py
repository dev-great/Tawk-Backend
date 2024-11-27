from datetime import timedelta
from django.utils import timezone
from rest_framework.response import Response
from .models import Subscription, SubscriptionPlan

class CheckSubscriptionExpirationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_authenticated:
            try:
                subscription = Subscription.objects.get(user=request.user, is_active=True)
                
                if subscription.expiration_date < timezone.now():
                    if timezone.now() - subscription.expiration_date > timedelta(hours=48):
                        subscription.is_active = False
                        free_plan = SubscriptionPlan.objects.filter(plan_id="00000").first()
                        subscription.plan = free_plan
                        subscription.save()

                # Add subscription details to the response
                subscription_data = {
                    'subscription_name': subscription.plan.name,
                    'is_active': subscription.is_active
                }

                # If the response is of type `Response` (from DRF), modify it
                if isinstance(response, Response):
                    response.data['subscription'] = subscription_data
            except Subscription.DoesNotExist:
                # If no active subscription, send default values
                subscription_data = {
                    'subscription_name': 'None',
                    'is_active': False
                }
                if isinstance(response, Response):
                    response.data['subscription'] = subscription_data


        return response
