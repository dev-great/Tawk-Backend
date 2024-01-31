from django.contrib.auth import authenticate
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_protect
from rest_framework.generics import DestroyAPIView
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator
from authorization.models import CustomUser, Referral, ReferralCode
from rest_framework.exceptions import ValidationError
from authorization.serializer import ChangePasswordSerializer, ReferralCodeSerializer, ReferralHistorySerializer, UserLoginSerializer, UserSerializer

User = get_user_model()


class CustomValidationException(Exception):
    def __init__(self, error, message, status_code=status.HTTP_400_BAD_REQUEST, *args, **kwargs):
        self.error = error,
        self.message = message,
        self.status_code = status_code
        super().__init__(*args, **kwargs)


class RegisterView(APIView):
    csrf_protect_method = method_decorator(csrf_protect)

    @swagger_auto_schema(request_body=UserSerializer)
    def post(self, request):
        serializers = UserSerializer(data=request.data)
        if serializers.is_valid(raise_exception=True):
            email = serializers.validated_data.get("email")

            # Check if the email already exists
            if User.objects.filter(email=email).exists():
                return Response({
                    "statusCode": status.HTTP_400_BAD_REQUEST,
                    "message": "Email already exists.",
                }, status=status.HTTP_400_BAD_REQUEST)

            # If email doesn't exist, save the new user
            user = serializers.save()

            # Create and associate a Token with the new user
            token, _ = Token.objects.get_or_create(user=user)

            # Include the token key in the payload
            payload = {
                'user': serializers.data,
                'token': token.key
            }

            return Response({
                "statusCode": status.HTTP_200_OK,
                "message": "User registered successfully.",
                "data": payload,
            }, status=status.HTTP_200_OK)

        return Response({
            "statusCode": status.HTTP_400_BAD_REQUEST,
            "message": "Invalid data.",
            "error": serializers.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    csrf_protect_method = method_decorator(csrf_protect)

    @swagger_auto_schema(
        request_body=UserSerializer,
        operation_description=" Edit user profile information. Use this endpoint to update the profile details of the authenticated user. Provide the new profile data in the request body using the UserProfileSerializer."

    )
    def patch(self, request):
        user_email = request.user.email
        profile = CustomUser.objects.get(email__exact=user_email)

        serializers = UserSerializer(
            profile, data=request.data, partial=True)
        if serializers.is_valid():

            # User update is sucessful
            serializers.save()
            return Response({
                "statusCode": status.HTTP_200_OK,
                "Success": "User updated successfully"
            },  status=status.HTTP_200_OK)

        # In an instance an error occures
        return Response({
            "statusCode": status.HTTP_400_BAD_REQUEST,
            "message": "Invalid data.",
            "error": serializers.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        try:
            email = request.user.email
            profile = CustomUser.objects.get(email__exact=email)

            serializer = UserSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            return Response({
                "statusCode": status.HTTP_400_BAD_REQUEST,
                "message": "User profile not found.",
                "error": serializer.errors,
            }, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({
                "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Invalid data.",
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserLoginView(APIView):

    @swagger_auto_schema(request_body=UserLoginSerializer)
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:

            # Login form validation error
            return Response({
                "statusCode": status.HTTP_400_BAD_REQUEST,
                "message": "An error occurred, validation failed.",
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(request, username=username, password=password)

        if user is None:
            # Invalid login credentials
            return Response({
                "statusCode": status.HTTP_401_UNAUTHORIZED,
                "message": "Invalid username or password."
            }, status=status.HTTP_401_UNAUTHORIZED)

        try:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred, data not fetched.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Logout(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        try:
            request.user.auth_token.delete()
            return Response({
                "statusCode": status.HTTP_200_OK,
                "message": "Logged out successfully."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred while logging out.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(request_body=ChangePasswordSerializer)
    def post(self, request, format=None):
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            user = self.request.user
            old_password = serializer.data.get("old_password")
            new_password = serializer.data.get("new_password")

            if not user.check_password(old_password):
                return Response({
                    "statusCode": status.HTTP_400_BAD_REQUEST,
                    "message": "Wrong password."
                }, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()

            return Response({
                "statusCode": status.HTTP_200_OK,
                "message": "Password updated successfully."
            }, status=status.HTTP_200_OK)

        return Response({
            "statusCode": status.HTTP_400_BAD_REQUEST,
            "message": "Invalid data.",
            "error": serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


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


class DeleteAccount(DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return get_object_or_404(CustomUser, email=self.request.user.email)

    def delete(self, request, *args, **kwargs):
        try:
            inshopper_user = self.get_object()
            self.perform_destroy(inshopper_user)
            return Response({"result": "user deleted"}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
