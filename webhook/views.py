from datetime import timezone
import json
import hmac
import logging
import hashlib
from django.conf import settings
from django.views import View
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from stripe.error import SignatureVerificationError
from exceptions.custom_apiexception_class import *
from subscription.models import Subscription, SubscriptionPlan
from utils.custom_response import custom_response
from rest_framework.permissions import AllowAny


logger = logging.getLogger(__name__)

class WebhookView(View):
    permission_classes = [AllowAny]
    @method_decorator(csrf_exempt)
    @swagger_auto_schema(
        operation_description="Webhook endpoint to handle incoming data",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'event': openapi.Schema(type=openapi.TYPE_STRING, description='Event type'),
                'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='Event data payload')
            }
        ),
        responses={
            200: openapi.Response(description="Webhook processed successfully"),
            400: openapi.Response(description="Invalid request or verification failure"),
            404: openapi.Response(description="Subscription not found"),
        },
    )

    def post(self, request, *args, **kwargs):
        try:
            # JSON PAYLOAD
            data = json.loads(request.body)
            logger.info(f"Received webhook data: {data}")

            if self.verify_flutterwave_signature(request):
                return self.handle_flutterwave_webhook(data)
            else:
                return CustomAPIException(detail="Invalid Flutterwave signature", status_code=status.HTTP_400_BAD_REQUEST).get_full_details() 

        except json.JSONDecodeError:
            return CustomAPIException(detail="Invalid payload", status_code=status.HTTP_400_BAD_REQUEST).get_full_details()



    # VERIFIES THE SIGNATURE FOR FLUTTERWAVW.
    def verify_flutterwave_signature(self, request):
        signature = request.headers.get("verifi-hash")
        try:
            computed_signature = hmac.new(settings.FLW_WEBHOOK_SECRET.encode(), request.body, hashlib.sha256).hexdigest()
            return hmac.compare_digest(computed_signature, signature)
        except:
            return CustomAPIException(detail="Flutterwave Signature Verification Failed", status_code=status.HTTP_400_BAD_REQUEST).get_full_details()


    # HANDLE THE FLUTTERWAVE WEBHOOK EVENTS.
    def handle_flutterwave_webhook(self, data):
        event_type = data.get("event.type")
        status = data.get("status")

        if event_type == "CARD_TRANSACTION":
            if status == "successful":
                return self.handle_flutterwave_subscription_event(data, is_success=True)
            elif status == "failed":
                return self.handle_flutterwave_subscription_event(data, is_success=False)
        return custom_response(status_code=status.HTTP_200_OK, message="Event ignored", data={"status": "ignored"})


    def handle_flutterwave_subscription_event(self, data, is_success):
        tx_ref = data.get("txRef")
        customer_data = data.get("customer")
        status = data.get("status")
        
        user_id = customer_data.get("id")
        amount = data.get("amount")
        charged_amount = data.get("charged_amount")
        currency = data.get("currency")
        full_name = customer_data.get("fullName")
        email = customer_data.get("email")
        card_last4 = data.get("entity", {}).get("card_last4")
        
        if not user_id or not tx_ref:
            return CustomAPIException(detail="Missing customer ID or transaction reference.", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            plan = SubscriptionPlan.objects.get(plan_id=data.get("paymentPlan")) 
            subscription, created = Subscription.objects.update_or_create(
                tx_ref=tx_ref,
                customer_id=user_id,
                defaults={
                    'plan': plan,
                    'is_active': is_success,
                    'auto_renew': data.get("auto_renew", False),
                    'payment_months': data.get("payment_months", 1),
                }
            )

            # If the transaction is successful, calculate and set expiration date
            if is_success:
                if created:
                    subscription.start_date = timezone.now()
                    subscription.expiration_date = subscription.calculate_expiration_date()
                else:
                    subscription.renew_subscription()
            else:
                # If the transaction failed, deactivate the subscription
                subscription.is_active = False

            subscription.save()

            message = "Subscription created and activated successfully." if created and is_success else "Subscription updated successfully."
            return custom_response(status_code=status.HTTP_200_OK, message=message, data={"status": "success"})

        except SubscriptionPlan.DoesNotExist:
            return CustomAPIException(detail="Subscription plan not found.", status_code=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)