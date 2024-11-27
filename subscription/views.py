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

import logging

logger = logging.getLogger(__name__)


#
class SubscriptionPlanListView(APIView):
    def get(self, request):
        try:
            subscription_plans = SubscriptionPlan.objects.all()
            serializer = SubscriptionPlanSerializer(subscription_plans, many=True)
            return custom_response(status_code=status.HTTP_200_OK, message="Subscription check completed.", data=serializer.data)  
        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()




class InitiateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # EXTRACT PAYMENT DETAILS FROM THE REQUEST
        cvv = request.data.get("cvv")
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
                        return CustomAPIException(detail= "Unsupported authorization mode", status_code=status.HTTP_400_BAD_REQUEST).get_full_details()


                # Successful payment initiation
                elif response_data["status"] == "success":
                    return  custom_response(status_code=status.HTTP_200_OK, message="Payment initiated successfully.", data=response_data["data"])  

                # Other error handling
                else:
                    return CustomAPIException(detail=str(response_data["message"]), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR).get_full_details() 
    

class ValidateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        flw_ref = request.data.get("flw_ref")
        otp = request.data.get("otp")

        # Prepare payload and headers
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
            # Validate the payment
            response = requests.post(
                'https://api.flutterwave.com/v3/validate-charge',
                json=authorization_payload,
                headers=headers
            )
            response_data = response.json()

            if response_data["status"] == "success":
                data = response_data["data"]
                
                # Save card information
                card_data = data.get("card")
                if card_data:
                    logger.debug(f"Saving card info: {card_data}")
                    Card.objects.create(
                        user=request.user,
                        first_6digits=card_data["first_6digits"],
                        last_4digits=card_data["last_4digits"],
                        issuer=card_data["issuer"],
                        country=card_data["country"],
                        card_type=card_data["type"],
                        expiry_date=card_data["expiry"],
                    )
                    logger.debug("Card info saved successfully.")

                return custom_response(
                    status_code=status.HTTP_200_OK,
                    message="Payment completed and subscription created successfully.",
                    data=data
                )
            else:
                logger.error(f"Payment validation failed: {response_data['message']}")
                return CustomAPIException(
                    detail=str(response_data["message"]),
                    status_code=status.HTTP_400_BAD_REQUEST
                ).get_full_details()

        except SubscriptionPlan.DoesNotExist:
            logger.error("Subscription plan does not exist.")
            return CustomAPIException(
                detail="Invalid subscription plan.",
                status_code=status.HTTP_400_BAD_REQUEST
            ).get_full_details()
        except Exception as e:
            logger.exception("An error occurred during subscription validation")
            return CustomAPIException(detail=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR).get_full_details()
            

class CreateFreePlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get("plan_id")
        try:
            free_plan = SubscriptionPlan.objects.filter(plan_id=plan_id).first()

            if not free_plan:
                return CustomAPIException(detail="Free plan is not available.", status_code=status.HTTP_404_NOT_FOUND).get_full_details()

            active_subscription = Subscription.objects.filter(user=request.user, is_active=True).exists()

            if active_subscription:
                return CustomAPIException(detail="You already have an active subscription.", status_code=status.HTTP_400_BAD_REQUEST).get_full_details()

            # Calculate expiration date based on the plan's duration
            expiration_date = timezone.now() + timedelta(days=free_plan.duration)
            
            # Create a new subscription
            subscription, created  = Subscription.objects.update_or_create(
                user=request.user,
                defaults={
                    'plan': free_plan,
                    "expiration_date": expiration_date,
                    "tx_ref":f"FLW-MOCK-{request.user.email}-{timezone.now()}",
                    "status":"successful",
                    'start_date':timezone.now(),
                    "is_active": False,
                    'auto_renew': False,
                    'payment_months':  300,
                }
                
            )
            
            if created:
                subscription.start_date = timezone.now()
                subscription.expiration_date = subscription.calculate_expiration_date()
            else:
                subscription.renew_subscription()

            return custom_response(
                status_code=status.HTTP_201_CREATED,
                message="Free plan activated successfully.",
                data={
                    "plan_name": free_plan.name,
                    "start_date": subscription.start_date,
                    "expiration_date": subscription.expiration_date,
                },
            ) 
        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR).get_full_details()