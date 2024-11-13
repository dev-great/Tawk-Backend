import random
from subscription.models import Subscription, SubscriptionPlan
from wallet.models import WalletModel
from django.core.cache import cache
from .models import *
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.conf import settings
from django_rest_passwordreset.signals import reset_password_token_created
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

User = get_user_model()


@receiver(post_save, sender=User)
def send_order_email_confirmation(sender, instance, created, **kwargs):
    if created:
        tawk_user = instance
        merge_data = {
            'tawk_user':  f"{tawk_user.first_name}",
            'msg': f"My name is Favour and I am very happy to welcome you to Tawk community! You have joined thousands of clients who are already skyrocketing their sales with Tawk by utilising our intuitive and user-friendly platform to showcase and scale their services. Welcome to the community of elite entrepreneurs and have a wonderful experience."
        }
        html_body = render_to_string(
            "emails/welcome_email.html", merge_data)
        msg = EmailMultiAlternatives(subject="Discover more with Tawk Tools", from_email=settings.EMAIL_HOST_USER, to=[
                                     instance.email], body=" ",)
        msg.attach_alternative(html_body, "text/html")
        return msg.send(fail_silently=False)


@receiver(post_save, sender=User)
def create_referral_code(sender, instance, created, **kwargs):
    if created:
        ReferralCode.objects.create(user=instance, code=123)


# USER REFERRAL BONUS
@ receiver(post_save, sender=Referral)
def create_referral_bonus(sender, instance, *args, **kwargs):
    if instance:
        if instance:
            user_obj = WalletModel.objects.get(
                user_id__exact=instance.referred_by)
    new = user_obj.balance + 2
    user_obj.balance = new
    user_obj.save()


# PASSWORD RESET EMAIL
@ receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):

    tawk_user = instance
    merge_data = {
        'tawk_user':  reset_password_token.user.email,
        'otp': reset_password_token.key
    }
    html_body = render_to_string("emails/reset_password_email.html", merge_data)
    msg = EmailMultiAlternatives(subject="Tawk Password Reset Token", from_email=settings.EMAIL_HOST_USER, to=[
                                 reset_password_token.user.email], body=" ",)
    msg.attach_alternative(html_body, "text/html")
    return msg.send(fail_silently=False)


@receiver(post_save, sender=Subscription)
def create_subscription_expiration(sender, instance, created, **kwargs):
    if created:
        plan_id = instance.plan
        payment_months = instance.payment_months
        try:
            subscription = SubscriptionPlan.objects.get(name=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return

        expiration_date = timezone.now(
        ) + timezone.timedelta(days=subscription.duration * payment_months)
        instance.expiration_date = expiration_date.isoformat()
        instance.is_active = True
        instance.save()


@receiver(post_save, sender=User)
def send_email_verification_otp(sender, instance, created, **kwargs):
    if created:  
        email = instance.email
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])

        cache.set(email, otp, timeout=300)

        merge_data = {
            'tawk_user': instance,
            'otp': otp,
        }

        html_body = render_to_string("emails/confirm_email.html", merge_data)
        msg = EmailMultiAlternatives(subject="Tawk Toolkit Email Verification", from_email=settings.EMAIL_HOST_USER, to=[
                                    email], body=" ",)
        msg.attach_alternative(html_body, "text/html")
        return msg.send(fail_silently=False)