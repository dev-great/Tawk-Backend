from subscription.models import Subscription, SubscriptionPlan
from wallet.models import WalletModel
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
        tawq_user = instance
        merge_data = {
            'tawq_user':  f"{tawq_user.email}",
            'msg': f" Hi {tawq_user.email} My name is Great and I am very happy to welcome you to Tawq community! You have joined thousands of clients who are already skyrocketing their sales with Tawq by utilising our intuitive and user-friendly platform to showcase and sell their products. They also have access to social media integration, AI shop assistant and associated support and guidance resources. To enjoy all this and more, complete your registration and kyc process now. Welcome to the community of elite entrepreneurs and have a wonderful experience."
        }
        html_body = render_to_string(
            "emails/congratulation_mail.html", merge_data)
        msg = EmailMultiAlternatives(subject="Discover more with Tawq", from_email=settings.EMAIL_HOST_USER, to=[
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

    tawq_user = instance
    merge_data = {
        'tawq_user':  f"{tawq_user.email}",
        'msg': f" Hi { reset_password_token.user.first_name} { reset_password_token.user.last_name } here is your password reset token: {reset_password_token.key} Copy and past in your app to continue with your password reset."
    }
    html_body = render_to_string("emails/congratulation_mail.html", merge_data)
    msg = EmailMultiAlternatives(subject="Tawq Password Reset Token", from_email=settings.EMAIL_HOST_USER, to=[
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
