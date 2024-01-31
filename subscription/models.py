import uuid
from django.db import models
from subscription.utils import default_expiration_date

from django.contrib.auth import get_user_model

# Create your models here.
CustomUser = get_user_model()


class SubscriptionPlan(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration = models.IntegerField(help_text="Duration in days")
    created_on = models.DateTimeField(auto_now_add=True)

    # Add more fields as per your requirements
    def __str__(self):
        return self.name


class Subscription(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE)
    plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.CASCADE)
    expiration_date = models.DateTimeField(
        default=default_expiration_date)
    payment_months = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField()
    created_on = models.DateTimeField(auto_now_add=True)
