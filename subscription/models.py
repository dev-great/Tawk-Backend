import uuid
from datetime import timedelta
from django.db import models
from django.utils import timezone
from subscription.choices import PROVIDER_CHOICES
from django.contrib.auth import get_user_model

# CREATE YOUR MODELS HERE.
CustomUser = get_user_model()

class SubscriptionPlan(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration = models.IntegerField(help_text="Duration in days")
    description = models.TextField(blank=True, null=True)
    currency = models.CharField(max_length=3, default='USD')
    created_on = models.DateTimeField(auto_now_add=True)
    gateway = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='Flutterwave')
    plan_id = models.CharField(max_length=100, blank=True, null=True, help_text="Plan ID from the payment provider")

    def __str__(self):
        return self.name

class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField()
    payment_months = models.PositiveIntegerField(default=1)
    tx_ref = models.CharField(max_length=250, blank=True, null=True)
    status = models.CharField(max_length=250, blank=True, null=True)
    customer_id = models.CharField(max_length=250, blank=True, null=True)
    auto_renew = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.plan.name}"

    def calculate_expiration_date(self):
        return self.start_date + timedelta(days=self.plan.duration * self.payment_months)

    def save(self, *args, **kwargs):
        if not self.expiration_date:
            self.expiration_date = self.calculate_expiration_date()
        super().save(*args, **kwargs)

    def is_subscription_active(self):
        return self.expiration_date > timezone.now()

    def renew_subscription(self):
        self.expiration_date = self.expiration_date + timedelta(days=self.plan.duration)
        self.is_active = True
        self.save()

        # CREATE A NEW BILLING DETAIL RECORD FOR THIS RENEWAL
        Billing.objects.create(
            amount=self.plan.price,       
            currency=self.plan.currency,
            payment_date=timezone.now(),  
            gateway=self.plan.gateway,
            plan_name=self.plan.name, 
            plan_duration=self.plan.duration, 
            plan_price=self.plan.price,
            status = self.status,
            user=self.user,
            customer_id=self.customer_id,
            start_date = self.start_date,
            tx_ref = self.tx_ref,
            expiration_date =self.expiration_date
        )


    def cancel_subscription(self):
        """Cancels the subscription by setting is_active to False."""
        self.is_active = False
        self.save()



class Billing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_date = models.DateTimeField(auto_now_add=True)
    tx_ref = models.CharField(max_length=100, blank=True, null=True)
    expiration_date = models.DateTimeField()
    gateway = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='Flutterwave')
    status = models.CharField(max_length=250, blank=True, null=True)
    plan_name = models.CharField(max_length=100)
    customer_id = models.CharField(max_length=250, blank=True, null=True)
    plan_duration = models.IntegerField()
    plan_price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.user_id} - {self.amount} {self.currency} on {self.payment_date}"


class Card(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    subscription = models.ForeignKey('Subscription', on_delete=models.CASCADE, related_name='cards')
    first_6digits = models.CharField(max_length=6)
    last_4digits = models.CharField(max_length=4)
    issuer = models.CharField(max_length=50)
    country = models.CharField(max_length=2)
    card_type = models.CharField(max_length=20)
    expiry_date = models.CharField(max_length=5)  # Format MM/YY
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.issuer} - {self.first_6digits}******{self.last_4digits}"