from datetime import timezone
import json
import stripe
import hmac
import hashlib
from django.conf import settings
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from stripe.error import SignatureVerificationError
from exceptions.custom_apiexception_class import *
from subscription.models import Subscription
from utils.custom_response import custom_response



stripe.api_key = settings.STRIPE_SECRET_KEY


class WebhookView(View):
    # DISBABLE CSRF FOR WEBHOOK REQUESTS
    @method_decorator(csrf_exempt)  
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            # JSON PAYLOAD
            data = json.loads(request.body)

            # Determine which provider the webhook came from
            if "verifi-hash" in request.headers:
                # Handle Flutterwave
                if self.verify_flutterwave_signature(request):
                    return self.handle_flutterwave_webhook(data)
                else:
                    return CustomAPIException(detail="Invalid Flutterwave signature", status_code=status.HTTP_400_BAD_REQUEST).get_full_details() 

            elif "Stripe-Signature" in request.headers:
                # Handle Stripe
                if self.verify_stripe_signature(request):
                    return  self.handle_stripe_webhook(data)
                else:
                    return CustomAPIException(detail="Invalid Stripe signature", status_code=status.HTTP_400_BAD_REQUEST).get_full_details()

            else:
                return CustomAPIException(detail="Unknown provider", status_code=status.HTTP_400_BAD_REQUEST).get_full_details() 

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



    # VERIFIES THE SIGNATURE FOR STRIPE.
    def verify_stripe_signature(self, request):
        signature_header = request.headers.get("Stripe-Signature")
        try:
            event = stripe.Webhook.construct_event(request.body, signature_header, settings.STRIPE_WEBHOOK_SECRET )
            return event  
        except stripe.error.SignatureVerificationError:
            return CustomAPIException(detail="Stripe Signature Verification Failed", status_code=status.HTTP_400_BAD_REQUEST).get_full_details()


    # HANDLE THE FLUTTERWAVE WEBHOOK EVENTS.
    def handle_flutterwave_webhook(self, data):
        event_type = data.get("event")
        event_data = data.get("data")
        print("------------ HANDLING FLUTTERWAVE WEBHOOK---------------")
        if event_type == "charge.completed":
            self.handle_flutterwave_subscription_event(event_data)
        return custom_response(status_code=status.HTTP_200_OK, message="Success", data=({"status": "success"}))


    # HANDLE THE STRIPE WEBHOOK EVENTS.
    def handle_stripe_webhook(self, event):
        event_type = event["type"]
        event_data = event["data"]["object"]
        print("------------ HANDLING STRIPE WEBHOOK---------------")
        if event_type == "invoice.payment_succeeded":
            self.handle_stripe_subscription_event(event_data)
        return custom_response(status_code=status.HTTP_200_OK, message="Success", data=({"status": "success"}))


    def handle_flutterwave_subscription_event(self, data):
        user_id = data.get("customer_id")
        tx_ref = data.get("tx_ref")

        if not user_id or not tx_ref:
            return CustomAPIException(detail="Missing customer ID or transaction reference.", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            if data.get("status") == "successful":
                try:
                    subscription = Subscription.objects.get(tx_ref=tx_ref, customer_id=user_id)
                except Subscription.DoesNotExist:
                    return CustomAPIException(detail="Subscription not found.", status_code=status.HTTP_400_BAD_REQUEST)

                subscription.renew_subscription()
                
            elif data.get("status") == "cancelled":
                try:
                    subscription = Subscription.objects.get(tx_ref=tx_ref, customer_id=user_id)
                except Subscription.DoesNotExist:
                    return CustomAPIException(detail="Subscription not found.", status_code=status.HTTP_400_BAD_REQUEST)

                subscription.is_active = False 
                subscription.save()

            return custom_response(status_code=status.HTTP_200_OK, message="Success", data=({"status": "success"}))

        except Subscription.DoesNotExist:
            return CustomAPIException(detail="Subscription not found.", status_code=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def handle_stripe_subscription_event(self, data):
        subscription_id = data.get("data", {}).get("object", {}).get("id")
        user_id = data.get("data", {}).get("object", {}).get("customer")

        if not user_id or not subscription_id:
            return CustomAPIException(detail="Missing customer ID or subscription ID.", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            event_type = data.get("type")
            
            if event_type in ["customer.subscription.created", "customer.subscription.updated"]:
                try:
                    subscription = Subscription.objects.get(tx_ref=subscription_id, customer_id=user_id)
                except Subscription.DoesNotExist:
                    return CustomAPIException(detail="Subscription not found.", status_code=status.HTTP_400_BAD_REQUEST)
                subscription.renew_subscription()  

            elif event_type == "customer.subscription.deleted":
                try:
                    subscription = Subscription.objects.get(tx_ref=subscription_id, customer_id=user_id)
                except Subscription.DoesNotExist:
                    return CustomAPIException(detail="Subscription not found.", status_code=status.HTTP_400_BAD_REQUEST)

                subscription.is_active = False  
                subscription.save()

            return custom_response(status_code=status.HTTP_200_OK, message="Success", data=({"status": "success"}))

        except Subscription.DoesNotExist:
            return CustomAPIException(detail="Subscription not found.", status_code=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
