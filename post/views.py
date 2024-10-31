# Example import, use the appropriate library
import requests

from linked_account.models import SocialUser
from .models import *
from exceptions.custom_apiexception_class import *
from rest_framework import status
from rest_framework.views import APIView
from utils.custom_response import custom_response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import os
from post.models import Post, PostImage
from post.serializers import ImageSerializer, PostSerializer, UpdatePostSerializer
from dotenv import load_dotenv

load_dotenv()


class CustomValidationException(Exception):
    def __init__(self, error, message, status_code=status.HTTP_400_BAD_REQUEST, *args, **kwargs):
        self.error = error,
        self.message = message,
        self.status_code = status_code
        super().__init__(*args, **kwargs)


# CREATE THE IMAGE MODEL DIFFERENT FROM THE POST MODEL SO WE CAN HANDLE MULTIPLE IMAGES ON A POST.
class ImageView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=ImageSerializer)
    def post(self, request):
        try:
            images = request.FILES.getlist('images')
            menu_item_id = request.data.get('menu_item_id')

            menu_item_instance = Post.objects.get(id=menu_item_id)
            serialized_data = []

            for image in images:
                img = PostImage.objects.create(
                    menu_item=menu_item_instance, image=image)
                serializer = ImageSerializer(img)
                serialized_data.append(serializer.data)

            return Response({
                "statusCode": status.HTTP_201_CREATED,
                "message": "Successfully.",
                "data": serialized_data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Server error",
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# CREATE NEW POST
class CreatePostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=PostSerializer)
    def post(self, request, format=None):
        try:
            serializer = PostSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(author=request.user)
                return Response({
                    "statusCode": status.HTTP_201_CREATED,
                    "message": "Successfully.",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "statusCode": status.HTTP_400_BAD_REQUEST,
                    "message": "Data Error.",
                    "data": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Server error",
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdatePostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=UpdatePostSerializer)
    def patch(self, request):
        try:
            post_id = request.data.get('post_id')
            post_instance = Post.objects.get(id=post_id, author=request.user)
            serializer = UpdatePostSerializer(
                post_instance, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "statusCode": status.HTTP_200_OK,
                    "message": "Post updated successfully.",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "statusCode": status.HTTP_400_BAD_REQUEST,
                    "message": "Data Error.",
                    "data": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Post.DoesNotExist:
            return Response({
                "statusCode": status.HTTP_404_NOT_FOUND,
                "message": "Post not found or you don't have permission to update it.",
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Server error",
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

 # Delete all post and images related to the post


class DeletePostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        try:
            post_id = request.data.get('post_id')

            post_instance = Post.objects.get(id=post_id, author=request.user)
            post_images = PostImage.objects.filter(post=post_instance)

            post_images.delete()
            post_instance.delete()

            return Response({
                "statusCode": status.HTTP_204_NO_CONTENT,
                "message": "Post deleted successfully."
            }, status=status.HTTP_204_NO_CONTENT)
        except Post.DoesNotExist:
            return Response({
                "statusCode": status.HTTP_404_NOT_FOUND,
                "message": "Post not found or you don't have permission to delete it.",
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Server error",
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserPostsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            posts = Post.objects.filter(author_id=request.user)
            serializer = PostSerializer(posts, many=True)
            return Response({
                "statusCode": status.HTTP_200_OK,
                "message": "User's posts retrieved successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Server error",
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class FacebookPostView(APIView):
    permission_classes = [IsAuthenticated]

    def get_page_access_token(self, user_access_token, page_id):
        """Exchange user token for a page access token"""
        url = f"https://graph.facebook.com/v14.0/{page_id}?fields=access_token"
        params = {
            'access_token': user_access_token
        }
        response = requests.get(url, params=params)
        data = response.json()
        return data.get('access_token')

    def post_to_facebook(self, page_access_token, page_id, message):
        """Post to the Facebook page using the page access token"""
        url = f"https://graph.facebook.com/v14.0/{page_id}/feed"
        params = {
            'access_token': page_access_token,
            'message': message
        }
        response = requests.post(url, data=params)
        return response.json()

    def post(self, request, *args, **kwargs):
        try:
            # Get the user's SocialUser object
            social_user = SocialUser.objects.get(user_id=request.user)

            if not social_user.facebook_access_token:
                return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Facebook account not connected")

            # Get the page ID and message from the request
            page_id = request.data.get('page_id')
            message = request.data.get('message')

            if not page_id or not message:
                return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Page ID and message are required")

            # Get the page access token
            page_access_token = self.get_page_access_token(social_user.facebook_access_token, page_id)

            if not page_access_token:
                return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Failed to get page access token")

            # Post the message to the Facebook page
            post_response = self.post_to_facebook(page_access_token, page_id, message)

            if 'id' in post_response:
                return custom_response(status_code=status.HTTP_200_OK, message="Post created successfully", data=post_response)
            else:
                raise CustomAPIException(detail=post_response.get('error', {}).get('message', 'Failed to post to Facebook'))

        except SocialUser.DoesNotExist:
            return custom_response(status_code=status.HTTP_404_NOT_FOUND, message="Social user not found")
        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()
        
        
        
class GoogleBusinessView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        access_token = request.data.get('access_token')
        account_id = request.data.get('account_id')  # Business account ID

        # Example: Fetch business information
        business_info = get_business_info(access_token, account_id)

        # Example: Update an offer
        offer_id = request.data.get('offer_id')
        offer_data = {
            "offer": {
                "title": "Special Discount",
                "description": "Get 20% off on your next purchase.",
                "startTime": "2023-10-01T00:00:00Z",
                "endTime": "2023-10-31T23:59:59Z",
            }
        }
        updated_offer = update_offer(access_token, account_id, offer_id, offer_data)

        return custom_response(status_code=status.HTTP_200_OK, message="Operation successful", data={
            "business_info": business_info,
            "updated_offer": updated_offer
        })


def get_business_info(access_token, account_id):
    """Fetch business information using the Google Business Profile API"""
    url = f'https://mybusinessbusinessinformation.googleapis.com/v1/{account_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    return response.json()


def update_offer(access_token, account_id, offer_id, offer_data):
    """Update an offer using the Google Business Profile API"""
    url = f'https://mybusinessbusinessinformation.googleapis.com/v1/{account_id}/offers/{offer_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    response = requests.patch(url, headers=headers, json=offer_data)
    return response.json()
