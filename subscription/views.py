import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Card, SubscriptionPlan, Subscription
from .serializers import SubscriptionPlanSerializer, SubscriptionSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from django.db import transaction
from .utils import encrypt_data, generate_tx_ref
from rest_framework import status
from django.contrib.auth import get_user_model
from exceptions.custom_apiexception_class import *
from utils.custom_response import custom_response
User = get_user_model()


#
class SubscriptionPlanListView(APIView):
    def get(self, request):
        try:
            subscription_plans = SubscriptionPlan.objects.all()
            serializer = SubscriptionPlanSerializer(subscription_plans, many=True)
            return custom_response(status_code=status.HTTP_200_OK, message="Subscription check completed.", data=serializer.data)  
        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST) 




class InitiateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # EXTRACT PAYMENT DETAILS FROM THE REQUEST
        cvv = request.data.get("cvv")
        pin = request.data.get("pin")
        tx_ref = request.data.get("tx_ref")
        amount = request.data.get("amount")
        payment_plan = request.data.get("payment_plan")
        expiry_year = request.data.get("expiry_year")
        card_number = request.data.get("card_number")
        currency = request.data.get("currency", "NGN")
        expiry_month = request.data.get("expiry_month")
        
        # SYSTEM GENERATED
        fullname = f"{request.user.first_name} {request.user.last_name}"
        email = request.user.email

        # PREPARE PAYMENT DATA
        payment_data = {
            "card_number": card_number,
            "cvv": cvv,
            "expiry_month": expiry_month,
            "expiry_year": expiry_year,
            "currency": currency,
            "amount": amount,
            "fullname": fullname,
            "payment_plan": payment_plan,
            "email": email,
            "tx_ref": tx_ref,
        }
        
        
        encryption_key = "FLWSECK_TEST44a081d6c747" 
        encrypted_payload = encrypt_data(encryption_key, payment_data)

        headers = {
            "Authorization": "Bearer FLWSECK_TEST-d715f2b61ac64d86cc7e0582391895f7-X",
            "Content-Type": "application/json",
        }

        try:
                # Initial charge request
                response = requests.post('https://api.flutterwave.com/v3/charges?type=card', json={"client": encrypted_payload}, headers=headers)
                response_data = response.json()
                print(response_data)
                # Check if further authorization is needed
                if response_data["status"] == "success" and response_data["message"] == "Charge authorization data required":
                    auth_mode = response_data.get("meta", {}).get("authorization", {}).get("mode")
                    
                    # Handle PIN authorization mode
                    if auth_mode == "pin":
                        return custom_response(status_code=status.HTTP_202_ACCEPTED, message="PIN required to complete the payment", data={
                        
                            "mode": "pin",
                            "fields": ["pin"],
                            "tx_ref": tx_ref
                        })  

                    # Handle AVS authorization mode
                    elif auth_mode == "avs_noauth":
                        return  custom_response(status_code=status.HTTP_202_ACCEPTED, message="Billing details required to complete the payment", data={
                            "mode": "avs_noauth",
                            "fields": ["city", "address", "state", "country", "zipcode"],
                            "tx_ref": tx_ref
                        })  

                    # Handle any other authorization modes if needed
                    else:
                        return CustomAPIException(detail= "Unsupported authorization mode", status_code=status.HTTP_400_BAD_REQUEST)


                # Successful payment initiation
                elif response_data["status"] == "success":
                    return  custom_response(status_code=status.HTTP_200_OK, message="Payment initiated successfully.", data=response_data["data"])  

                # Other error handling
                else:
                    return CustomAPIException(detail=str(response_data["message"]), status_code=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) 
    

class ValidateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        flw_ref = request.data.get("flw_ref")
        otp = request.data.get("otp")

        authorization_payload = {
            "flw_ref": flw_ref,
            "otp": otp,
            "type": "card"
        }

        headers = {
            "Authorization": "Bearer FLWSECK_TEST-d715f2b61ac64d86cc7e0582391895f7-X",
            "Content-Type": "application/json",
        }

        try:
            response_data = self._validate_payment(authorization_payload, headers)
            if response_data["status"] == "success":
                subscription, card_data = self._process_subscription(request.user, response_data["data"])
                self._save_card_info(subscription, card_data)
                
                return custom_response(
                    status_code=status.HTTP_200_OK,
                    message="Payment completed and subscription created successfully.",
                    data=response_data["data"]
                )
            else:
                raise CustomAPIException(
                    detail=str(response_data["message"]),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            raise CustomAPIException(detail=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _validate_payment(self, payload, headers):
        """Helper function to handle payment validation."""
        response = requests.post(
            'https://api.flutterwave.com/v3/validate-charge',
            json=payload,
            headers=headers
        )
        return response.json()

    @transaction.atomic
    def _process_subscription(self, user, data):
        """Creates or updates a subscription and returns the subscription and card data."""
        tx_ref = data.get("tx_ref")
        customer_id = data.get("customer")
        plan_id = data.get("plan")

        # Get or create subscription plan and expiration date
        plan = SubscriptionPlan.objects.get(plan_id=plan_id)
        expiration_date = timezone.now() + timedelta(days=plan.duration)

        # Update or create subscription atomically
        subscription, _ = Subscription.objects.update_or_create(
            user=user,
            defaults={
                "plan": plan,
                "start_date": timezone.now(),
                "status": data.get("processor_response"),
                "expiration_date": expiration_date,
                "tx_ref": tx_ref,
                "customer_id": customer_id.get("id"),
                "is_active": True,
            }
        )
        return subscription, data.get("card")

    def _save_card_info(self, subscription, card_data):
        """Saves card information if available."""
        if card_data:
            Card.objects.create(
                subscription=subscription,
                first_6digits=card_data["first_6digits"],
                last_4digits=card_data["last_4digits"],
                issuer=card_data["issuer"],
                country=card_data["country"],
                card_type=card_data["type"],
                expiry_date=card_data["expiry"]
            )
