import logging
import random
from datetime import timedelta
from rest_framework import status
from google.oauth2 import id_token
from google.auth.transport import requests
from exceptions.custom_apiexception_class import *
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from rest_framework import generics
from utils.custom_response import custom_response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_protect
from rest_framework.generics import DestroyAPIView
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.template import TemplateDoesNotExist
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from dotenv import load_dotenv
from django.core.cache import cache  
from django.utils.decorators import method_decorator
from authorization.models import CustomUser, Referral, ReferralCode
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from authorization.serializer import ChangePasswordSerializer, TokenObtainPairResponseSerializer, TokenRefreshResponseSerializer, TokenVerifyResponseSerializer,ReferralCodeSerializer, ReferralHistorySerializer, UserSerializer

otp_storage = {}
load_dotenv()
User = get_user_model()
logger = logging.getLogger(__name__)


class CustomValidationException(Exception):
    def __init__(self, error, message, status_code=status.HTTP_400_BAD_REQUEST, *args, **kwargs):
        self.error = error,
        self.message = message,
        self.status_code = status_code
        super().__init__(*args, **kwargs)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={status.HTTP_201_CREATED: UserSerializer}
    )
    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            logger.info(f"Generated refresh token: {str(refresh)}")
            response = custom_response(
                status_code=status.HTTP_201_CREATED,
                message="Success",
                data={
                    'user': serializer.data,
                    'access': str(refresh.access_token),
                }
            )

            response.set_cookie(
                'refresh_token',
                str(refresh),
                max_age=timedelta(days=7),
                expires=timedelta(days=7),
                secure=True, 
                httponly=True,
                samesite='Lax',
            )

            logger.info(f"User registered: {serializer.data['email']}")
            return response
        else:
            error_msg = serializer.errors
            logger.error(f"Registration error: {error_msg}")
            return CustomAPIException(detail=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST).get_full_details()


class LoginView(TokenObtainPairView):
    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: TokenObtainPairResponseSerializer,
            status.HTTP_400_BAD_REQUEST: "Bad request, typically because of a malformed request body.",
            status.HTTP_401_UNAUTHORIZED: "Unauthorized, typically because of invalid credentials.",
        }
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        logger.info("Login request received.")
        print(request.data)
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            logger.info("Request data is valid.")
        except TokenError as e:
            logger.error(f"TokenError encountered: {e}")
            return CustomAPIException(
                detail="Invalid token.", status_code=status.HTTP_401_UNAUTHORIZED).get_full_details()
        except Exception as e:
            logger.error(f"Exception encountered: {e}")
            return CustomAPIException(detail=str(
                e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()

        logger.info("Login successful.")

        user_email = request.data['email']
        print(user_email)
        try:
            profile = CustomUser.objects.get(email__iexact=user_email)
        except CustomUser.DoesNotExist:
            logger.error(f"User with email {user_email} does not exist.")
            return CustomAPIException(
                detail="User not found.",
                status_code=status.HTTP_404_NOT_FOUND
            ).get_full_details()

        user_data = UserSerializer(profile).data

        refresh = RefreshToken.for_user(profile)
        logger.info(f"Generated refresh token: {str(refresh)}")

        response = Response({
            "auth": {
                "access": serializer.validated_data['access'],
            },
            "user": user_data,
        })

        try:
            response.set_cookie(
                'refresh_token', 
                str(refresh), 
                max_age=timedelta(days=7),
                expires=timedelta(days=7),
                secure=True,  
                httponly=True,  
                samesite='Lax', 
            )
        except Exception as e:
            return CustomAPIException(
                detail=f"Error setting cookie: {str(e)}", 
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ).get_full_details()

        return response

        response_data = {
            "auth": {
                "access": serializer.validated_data['access'],
            },
            "user": user_data,
        }

        return custom_response(status_code=status.HTTP_200_OK, message="Success", data=response_data)


class TokenRefreshView(TokenRefreshView):
    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: TokenRefreshResponseSerializer,
            status.HTTP_400_BAD_REQUEST: "Bad request, typically because of a malformed request body.",
            status.HTTP_401_UNAUTHORIZED: "Unauthorized, typically because of invalid token.",
        }
    )
    def post(self, request, *args, **kwargs):
        logger.info("Token refresh request received.")
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            logger.info("Token refresh successful.")
            return custom_response(status_code=status.HTTP_200_OK, message="Token is refresh.", data=response.data)
        else:
            logger.error(
                f"Token refresh failed with status code {response.status_code}.")
            return CustomAPIException(detail="Token is invalid.", status_code=response.status_code, data=response.data).get_full_details()


class TokenVerifyView(TokenVerifyView):
    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: TokenVerifyResponseSerializer,
            status.HTTP_400_BAD_REQUEST: "Bad request, typically because of a malformed request body.",
            status.HTTP_401_UNAUTHORIZED: "Unauthorized, typically because of invalid token.",
        }
    )
    def post(self, request, *args, **kwargs):
        logger.info("Token verification request received.")
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            logger.info("Token verification successful.")
            return custom_response(status_code=status.HTTP_200_OK, message="Token is valid.", data=response.data)
        else:
            logger.error(
                f"Token verification failed with status code {response.status_code}.")
            return CustomAPIException(detail="Token is invalid or expired.", status_code=response.status_code, data=response.data).get_full_details()



class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    csrf_protect_method = method_decorator(csrf_protect)

    @swagger_auto_schema(request_body=UserSerializer)
    def patch(self, request):
        logger.info(
            f"UserProfile PATCH request received for user: {request.user.email}")
        user_email = request.user.email

        try:
            profile = CustomUser.objects.get(email__exact=user_email)
            logger.debug(f"User profile found for email: {user_email}")
        except CustomUser.DoesNotExist:
            logger.error(f"User profile not found for email: {user_email}")
            raise CustomAPIException(
                detail="User profile not found.", status_code=status.HTTP_404_NOT_FOUND).get_full_details()

        serializers = UserSerializer(profile, data=request.data, partial=True)
        if serializers.is_valid():
            serializers.save()
            logger.info(
                f"User profile updated successfully for email: {user_email}")
            return custom_response(status_code=status.HTTP_200_OK, message="User updated successfully", data=serializers.data)

        logger.error(
            f"User profile update failed for email: {user_email}, errors: {serializers.errors}")
        raise CustomAPIException(
            detail=serializers.errors, status_code=status.HTTP_400_BAD_REQUEST).get_full_details()

    def get(self, request):
        logger.info(
            f"UserProfile GET request received for user: {request.user.email}")
        email = request.user.email

        try:
            profile = CustomUser.objects.get(email__exact=email)
            logger.debug(f"User profile found for email: {email}")
        except CustomUser.DoesNotExist:
            logger.error(f"User profile not found for email: {email}")
            raise CustomAPIException(
                detail="User profile not found.", status_code=status.HTTP_404_NOT_FOUND).get_full_details()

        serializer = UserSerializer(profile)
        logger.info(f"User profile retrieved successfully for email: {email}")
        return custom_response(status_code=status.HTTP_200_OK, message="Success.", data=serializer.data)



class Logout(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'refresh', openapi.IN_QUERY, description="Refresh token", type=openapi.TYPE_STRING, required=True
            )
        ],
        responses={
            status.HTTP_205_RESET_CONTENT: "Logout successful.",
            status.HTTP_400_BAD_REQUEST: "Bad request, typically because of a malformed request body.",
            status.HTTP_401_UNAUTHORIZED: "Unauthorized, typically because of invalid credentials.",
        }
    )
    def post(self, request):
        logger.info(
            f"Logout POST request received for user: {request.user.email}")

        try:
            refresh_token = request.data['refresh']
            logger.debug(f"Refresh token received: {refresh_token}")

            token = RefreshToken(refresh_token)
            token.blacklist()

            logger.info(
                f"Token blacklisted successfully for user: {request.user.email}")
            return custom_response(status_code=status.HTTP_205_RESET_CONTENT, message="Logout successful.", data=None)

        except Exception as e:
            logger.error(
                f"Logout failed for user: {request.user.email}, error: {str(e)}")
            raise CustomAPIException(detail=str(
                e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    model = User

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        logger.info(
            f"ChangePassword update request received for user: {request.user.email}")

        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if not self.object.check_password(serializer.data.get("old_password")):
                logger.warning(
                    f"Invalid old password provided by user: {request.user.email}")
                return CustomAPIException(
                    detail="Invalid Credential",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data={"old_password": ["Wrong password."]}
                ).get_full_details()

            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            logger.info(
                f"Password updated successfully for user: {request.user.email}")

            return custom_response(status_code=status.HTTP_200_OK, message='Password updated successfully', data=None)

        logger.error(
            f"Password update failed for user: {request.user.email}, errors: {serializer.errors}")
        return CustomAPIException(detail=str(serializer.errors), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()


class DeleteAccount(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        user_email = self.request.user.email
        logger.info(f"Fetching user object for email: {user_email}")
        return get_object_or_404(CustomUser, email=user_email)

    def delete(self, request, *args, **kwargs):
        try:
            user_email = request.user.email
            logger.info(f"Delete request received for user: {user_email}")

            paysita_user = self.get_object()
            self.perform_destroy(paysita_user)
            logger.info(f"User deleted successfully: {user_email}")

            return custom_response(status_code=status.HTTP_200_OK, message="User deleted", data=None)
        except CustomUser.DoesNotExist:
            logger.warning(f"User not found for email: {user_email}")
            return CustomAPIException(detail="User not found", status_code=status.HTTP_404_NOT_FOUND).get_full_details()
        except Exception as e:
            logger.error(f"Error deleting user {user_email}: {str(e)}")
            return CustomAPIException(detail=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR).get_full_details()

    def perform_destroy(self, instance):
        instance.delete()
        logger.info(f"User instance deleted: {instance.email}")


class ReferralView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReferralCodeSerializer

    def get_object(self):
        try:
            return ReferralCode.objects.select_related('user').get(user=self.request.user)
        except ReferralCode.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is not None:
            serializer = self.serializer_class(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"error": "Referral code not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(request_body=ReferralCodeSerializer)
    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is not None:
            serializer = self.serializer_class(
                instance, data=request.data, partial=True, context={'request': request})
        else:
            serializer = self.serializer_class(
                data=request.data, context={'request': request})

        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        return Response({"error": False}, status=status.HTTP_201_CREATED)


class ReferralHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReferralHistorySerializer

    def get_queryset(self):
        # Use select_related() to fetch related 'referred_to' user to avoid additional queries
        return Referral.objects.filter(referred_by=self.request.user).select_related('referred_to')

    def get(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.serializer_class(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Referral.DoesNotExist:
            return Response({"error": "Referral history not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class GoogleAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        token = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImIyZjgwYzYzNDYwMGVkMTMwNzIxMDFhOGI0MjIwNDQzNDMzZGIyODIiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJhenAiOiIzNTA1NTU0NTA2OTMtOWJhYTE3MjdxYzI4aTdpOGcwc3NoaDRhNTJhYTMzMW8uYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJhdWQiOiIzNTA1NTU0NTA2OTMtZ2ppYnFhcXRxdDZxMW8wNjF2YXBzNDZjMGNzN3BvY2kuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJzdWIiOiIxMTM1ODc2MTQxMzU4Mjg2NDcyNzAiLCJlbWFpbCI6ImdtYXJzaGFsMDcwQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiR3JlYXRuZXNzIE1hcnNoYWwiLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSVl6dnZLbXFHcWRfYzFwTG5qZG9vQXBrSU12ZGJUNTAwWTg4ZE9GSnBZdEQycDBJOXo9czk2LWMiLCJnaXZlbl9uYW1lIjoiR3JlYXRuZXNzIiwiZmFtaWx5X25hbWUiOiJNYXJzaGFsIiwiaWF0IjoxNzI1NDQ5Nzk1LCJleHAiOjE3MjU0NTMzOTV9.of5fqF5lC_I_3PnOh_G17a66SASvpOq6xkrrJj1Y0TyptTaWNHJB92Aoy7aOK17DO1gHS8gAQoLHMrSBusj0_5lKkdTx6nocDpSYkjCdjz6qUhQeE8Z8J_vP4pNGMM8kShfgijuFTeP1jn_vscF0E9hYRgRH2tKAh6KIpoKM0625b_GFdsj1pBg1MrpmQLC_k21ZUMLjY1yU70RKc4frwE9G1NvWc7YCO0CQ"
        CLIENT_ID = "350555450693-gjibqaqtqt6q1o061vaps46c0cs7poci.apps.googleusercontent.com"
        try:
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), "350555450693-gjibqaqtqt6q1o061vaps46c0cs7poci.apps.googleusercontent.com")

            print("Token is valid:", idinfo)
            return custom_response(status_code=status.HTTP_200_OK, message="User success", data=idinfo)

        except Exception as e:
            return CustomAPIException(
                detail=str(e), status_code=status.HTTP_404_NOT_FOUND).get_full_details()


class EmailOTPAuthentication(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        email = request.user.email
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        # Store OTP in cache with a timeout (e.g., 5 minutes)
        cache.set(email, otp, timeout=300)
        merge_data = {
            'tawk_user': request.user,
            'otp': otp,
        }
        try:
            html_body = render_to_string(
            "otp_mail.html", merge_data)
        
        except TemplateDoesNotExist as template_error:
            logger.error(f"Template not found: {template_error}")
            html_body = f"""Dear {email},\n\nYour OTP is: {
                otp}\n\nPlease use this OTP to reset your password."""

        msg = EmailMultiAlternatives(
            subject="Yinoral Email Verification.",
            from_email=settings.EMAIL_HOST_USER,
            to=[email],
            body=" ",
        )
        msg.attach_alternative(html_body, "text/html")
        
        try:
            msg.send(fail_silently=False)
            logger.info(f"OTP sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return custom_response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="Failed to send OTP.", data=None)

        return custom_response(status_code=status.HTTP_200_OK, message="OTP sent to your email.", data=None)

    def put(self, request):
        email = request.user.email
        otp_entered = request.data.get('otp')

        otp_stored = cache.get(email)
        if email not in otp_stored:
            return CustomAPIException(detail="OTP not sent for this email.", status_code=status.HTTP_400_BAD_REQUEST).get_full_details()

        if otp_entered == otp_stored:
            cache.delete(email)
            return custom_response(status_code=status.HTTP_200_OK, message="Email verification successful.", data=None)
        else:
            return CustomAPIException(detail="Incorrect OTP.", status_code=status.HTTP_400_BAD_REQUEST).get_full_details()


