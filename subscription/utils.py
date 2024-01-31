
from django.utils import timezone


def default_expiration_date():
    # Calculate the default expiration date based on your requirements
    return timezone.now() + timezone.timedelta(days=30)
