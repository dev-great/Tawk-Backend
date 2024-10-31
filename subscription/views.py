
from datetime import timezone
from .models import SubscriptionPlan, Subscription
from .serializers import SubscriptionPlanSerializer, SubscriptionSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from django.contrib.auth import get_user_model
User = get_user_model()


# Create your views here.

class SubscriptionView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionSerializer

    def get_object(self):
        try:
            return Subscription.objects.select_related('user').get(user=self.request.user)
        except Subscription.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND

    def get(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except status.HTTP_404_NOT_FOUND:
            return Response("Subscription not found.", status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(request_body=SubscriptionSerializer)
    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            # Raise exception for invalid data
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Subscription.DoesNotExist:
            return Response({
                "statusCode": status.HTTP_404_NOT_FOUND,
                "message": "Subscription not found.",
                "error": serializer.errors,
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                "statusCode": status.HTTP_400_BAD_REQUEST,
                "message": "An error occurred",
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=SubscriptionSerializer)
    def patch(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=request.data, partial=True)

            if serializer.is_valid():
                plan_id = serializer.validated_data.get('plan')
                payment_months = serializer.validated_data.get(
                    'payment_months')
                subscription = SubscriptionPlan.objects.get(name=plan_id)
                expiration_date = timezone.now(
                ) + timezone.timedelta(days=subscription.duration * payment_months)

                serializer.save(expiration_date=expiration_date,
                                is_active=expiration_date > timezone.now())
                return Response({
                    "statusCode": status.HTTP_200_OK,
                    "message": "Subscription check completed.",
                    "data": serializer.data,
                }, status=status.HTTP_200_OK)

            return Response({
                "statusCode": status.HTTP_400_BAD_REQUEST,
                "message": "Subscription renewed sucessfully.",
                "error": serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        except Subscription.DoesNotExist:
            return Response({
                "statusCode": status.HTTP_404_NOT_FOUND,
                "message": "Subscription not found.",
                "error": serializer.errors,
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubscriptionPlanListView(APIView):

    def get(self, request):
        try:
            subscription_plans = SubscriptionPlan.objects.all()
            serializer = SubscriptionPlanSerializer(
                subscription_plans, many=True)
            return Response({
                "statusCode": status.HTTP_200_OK,
                "message": "Subscription check completed.",
                "data": serializer.data,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "statusCode": status.HTTP_400_BAD_REQUEST,
                "message": "An error occurred",
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionCheckAPIView(APIView):

    def get(self, request, format=None):
        try:
            current_date = timezone.now()
            # Update is_active for expired subscriptions
            Subscription.objects.filter(
                expiration_date__lte=current_date).update(is_active=False)

            # If you also need to retrieve data for some further processing, use select_related()
            subscriptions = Subscription.objects.select_related(
                'plan').filter(expiration_date__lte=current_date)

            # You can use serializers to serialize the queryset if necessary
            serialized_data = SubscriptionPlanSerializer(
                subscriptions, many=True).data

            return Response({
                "statusCode": status.HTTP_200_OK,
                "message": "Subscription check completed.",
                "data": serialized_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "statusCode": status.HTTP_400_BAD_REQUEST,
                "message": "An error occurred",
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
