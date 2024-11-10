
from datetime import timezone
import requests
from django.conf import settings
from .models import SubscriptionPlan, Subscription
from .serializers import SubscriptionPlanSerializer, SubscriptionSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
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
            "authorization": {
                "mode": "pin",
                "pin": pin
            }
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
                        return Response({
                            "status": "authorization_required",
                            "message": "PIN required to complete the payment",
                            "mode": "pin",
                            "fields": ["pin"],
                            "tx_ref": tx_ref
                        }, status=status.HTTP_200_OK)

                    # Handle AVS authorization mode
                    elif auth_mode == "avs_noauth":
                        return Response({
                            "status": "authorization_required",
                            "message": "Billing details required to complete the payment",
                            "mode": "avs_noauth",
                            "fields": ["city", "address", "state", "country", "zipcode"],
                            "tx_ref": tx_ref
                        }, status=status.HTTP_200_OK)

                    # Handle any other authorization modes if needed
                    else:
                        return Response({
                            "status": "error",
                            "message": "Unsupported authorization mode",
                            "mode": auth_mode,
                        }, status=status.HTTP_400_BAD_REQUEST)

                # Successful payment initiation
                elif response_data["status"] == "success":
                    return Response({
                        "status": "success",
                        "message": "Payment initiated successfully.",
                        "data": response_data["data"]
                    }, status=status.HTTP_200_OK)

                # Other error handling
                else:
                    return Response({
                        "status": "error",
                        "message": response_data["message"]
                    }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    

class ValidateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        flw_ref = request.data.get("flw_ref")
        otp = request.data.get("otp")

        # Prepare the authorization payload with the PIN
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
            # Complete the charge with the authorization payload
            response = requests.post('https://api.flutterwave.com/v3/validate-charge', json=authorization_payload, headers=headers)
            response_data = response.json()

            if response_data["status"] == "success":
                return Response({
                    "status": "success",
                    "message": "Payment completed successfully.",
                    "data": response_data["data"]
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": "error",
                    "message": response_data["message"]
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)