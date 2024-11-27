from django.utils import timezone
import json
import logging
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from authorization.models import CustomUser
from exceptions.custom_apiexception_class import *
from subscription.models import Subscription, SubscriptionPlan
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView



logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            # JSON PAYLOAD
            print(request.headers)
            data = request.data
            print(f"Received webhook data: {data}")

            if self.verify_flutterwave_signature(request):
                print("pass 1")
                result = self.handle_flutterwave_webhook(data)
                return Response(result, status=status.HTTP_200_OK)
            else:
                print("Invalid Flutterwave signature")
                return Response({"detail": "Invalid Flutterwave signature"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




    # VERIFIES THE SIGNATURE FOR FLUTTERWAVW.
    def verify_flutterwave_signature(self, request):
        signature = request.headers.get("Verif-Hash")
        secret_hash = "a3c1d5b6f7e8d9a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8g9h0i1j2k3l4m5"
        if not signature or signature != secret_hash:
            print("Signature verification failed.")
            return False
        print("Signature verified successfully.")
        return True


    # HANDLE THE FLUTTERWAVE WEBHOOK EVENTS.
    def handle_flutterwave_webhook(self, data):
        event = data.get("event.type")
        transaction_data = data
        status = transaction_data.get("status")

        if event == "CARD_TRANSACTION":
            print("pass 2")
            is_success = status == "successful"
            print("pass 3")
            return self.handle_flutterwave_subscription_event(transaction_data, is_success)

        return {"detail": "Process ignored"}

        
    def handle_flutterwave_subscription_event(self, data, is_success):
        tx_ref = data.get("txRef")
        customer_data = data.get("customer", {})
        plan_id = data.get("paymentPlan")  # Ensure paymentPlan exists in the webhook data
        
        if not tx_ref or not customer_data:
            
            print("Missing customer ID or transaction reference.")
            return {"detail": "Missing customer ID or transaction reference"}, status.HTTP_400_BAD_REQUEST

        try:
            
            user_id = customer_data.get("id")
            user_email = customer_data.get("email")
            customer = CustomUser.objects.get(email=user_email)
            plan = SubscriptionPlan.objects.get(plan_id=plan_id)
            print("pass 4") 
            
            subscription, created = Subscription.objects.update_or_create(
                user=customer,
                defaults={
                    'plan': plan,
                    "tx_ref":tx_ref,
                    "customer_id":user_id,
                    "status": data.get("status"),
                    'is_active': is_success,
                    'start_date':timezone.now(),
                    'auto_renew': data.get("auto_renew", False),
                    'payment_months': data.get("payment_months", 1),
                }
            )

            # If the transaction is successful, calculate and set expiration date
            if is_success:
                print("pass 5")
                if created:
                    print("pass 6")
                    subscription.expiration_date = subscription.calculate_expiration_date()
                else:
                    print("pass 7")
                    subscription.renew_subscription()
            else:
                print("Fail")
                # If the transaction failed, deactivate the subscription
                subscription.is_active = False

            subscription.save()

            message = (
                "Subscription created and activated successfully." if created and is_success else
                "Subscription updated successfully."
            )
            print("pass 8")
            return {"message": message, "status": "Subscription success"}

        except SubscriptionPlan.DoesNotExist:
            print("Subscription plan not found.")
            print("pass 9")
            return {"detail": "Subscription plan not found"}, status.HTTP_404_NOT_FOUND

        except Exception as e:
            print(e)
            print("fail 1")
            return {"detail": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR