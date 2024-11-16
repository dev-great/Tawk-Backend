from datetime import timedelta
from django.utils.timezone import now
from .models import Subscription

def transition_from_trial():
    trial_subscriptions = Subscription.objects.filter(
        is_trial=True,
        expiration_date__lte=now(),
        is_active=True
    )
    for subscription in trial_subscriptions:
        subscription.is_trial = False
        subscription.expiration_date = subscription.start_date + timedelta(days=subscription.plan.duration)
        subscription.save()
