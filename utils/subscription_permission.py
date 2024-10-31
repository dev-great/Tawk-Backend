from rest_framework.permissions import BasePermission
from rest_framework import status
from subscription.models import Subscription, UserMembership
from rest_framework.exceptions import PermissionDenied
from exceptions.custom_apiexception_class import CustomAPIException


class IsSubscribed(BasePermission):
    """
    Custom permission to only allow access to users with an active subscription.
    """

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        try:
            user_membership = UserMembership.objects.get(user=request.user)
            subscription = Subscription.objects.get(
                user_membership=user_membership)

            if subscription.active:
                return True
            else:
                error_msg = "User's subscription is not active."
                return CustomAPIException(detail=error_msg, status_code=status.HTTP_409_CONFLICT).get_full_details()

        except UserMembership.DoesNotExist:
            error_msg = "User doesn't have an active membership."
            return CustomAPIException(detail=error_msg, status_code=status.HTTP_409_CONFLICT).get_full_details()

        except Subscription.DoesNotExist:
            error_msg = "User doesn't have an active subscription."
            return CustomAPIException(detail=error_msg, status_code=status.HTTP_409_CONFLICT).get_full_details()

        except Exception as e:
            error_msg = "User doesn't have an active subscription."
            return CustomAPIException(detail=error_msg, status_code=status.HTTP_409_CONFLICT).get_full_details()
