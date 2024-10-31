
from .models import *
from .serializers import *
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
import firebase_admin
from firebase_admin import messaging
# Create your views here.
from django.contrib.auth import get_user_model
User = get_user_model()


class CustomValidationException(Exception):
    def __init__(self, error, message, status_code=status.HTTP_400_BAD_REQUEST, *args, **kwargs):
        self.error = error,
        self.message = message,
        self.status_code = status_code
        super().__init__(*args, **kwargs)


class SpecificUserNotificationView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        user = get_object_or_404(User, email=self.request.user.email)
        return NotificationPost.objects.filter(date__gte=user.date_joined, target=user).select_related('target')

    def get(self, request):
        try:
            queryset = self.get_queryset()
            serializer = NotificationSerializer(queryset, many=True)
            return Response({
                "statusCode": status.HTTP_200_OK,
                "message": "Successfully.",
                "data": serializer.data,
            }, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({
                "statusCode": status.HTTP_404_NOT_FOUND,
                "message": "Data error.",
                "error": "User does not exist.",
            }, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({
                "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Server error",
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
