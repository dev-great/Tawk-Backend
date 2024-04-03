# Example import, use the appropriate library

import tweepy
from instagram.client import InstagramAPI
from django.shortcuts import get_object_or_404
from facebook import GraphAPI
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import os
from authorization.models import SocialMediaUser
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


class PostToFacebookView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        post_id = request.data.get('post_id')
        facebook_user_id = request.data.get('facebook_user_id')

        post = get_object_or_404(Post, id=post_id)
        post_images = PostImage.objects.filter(post_id=post_id)
        graph = GraphAPI(access_token=os.getenv('FACEBOOK_ACCESS_TOKEN'))

        try:
            photo_ids = []

            for post_image in post_images:
                photo_id = graph.put_photo(
                    image=open(post_image.image.path, 'rb'), published=False
                )['id']
                photo_ids.append(photo_id)

            message = post.title
            attached_media = [{'media_fbid': photo_id}
                              for photo_id in photo_ids]
            result = graph.put_object(
                facebook_user_id, "feed", message=message, attached_media=attached_media)

            return Response({
                "statusCode": status.HTTP_200_OK,
                "message": "Facebook post successfully created.",
                "data": result
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Server error",
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PostToInstagramView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        post_id = request.data.get('post_id')
        instagram_user_id = request.data.get('instagram_user_id')

        post = get_object_or_404(Post, id=post_id)
        post_images = PostImage.objects.filter(post_id=post_id)

        # Initialize Instagram API client
        api = InstagramAPI(client_id=os.getenv('INSTAGRAM_CLIENT_ID'),
                           client_secret=os.getenv('INSTAGRAM_CLIENT_SECRET'))

        try:
            media_ids = []

            for post_image in post_images:
                media_id = api.upload_photo(photo=open(
                    post_image.image.path, 'rb'), caption=post.title)
                media_ids.append(media_id)

            # Post the uploaded media to Instagram
            api.post_media(instagram_user_id,
                           media_ids=media_ids, caption=post.title)

            return Response({
                "statusCode": status.HTTP_200_OK,
                "message": "Instagram post successfully created.",
                "data": {"media_ids": media_ids}
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Server error",
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PostToTwitterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        post_id = request.data.get('post_id')

        post = get_object_or_404(Post, id=post_id)
        post_images = PostImage.objects.filter(post_id=post_id)

        # Initialize Tweepy API client
        auth = tweepy.OAuthHandler(
            os.getenv('TWITTER_API_KEY'), os.getenv('TWITTER_API_SECRET'))
        auth.set_access_token(os.getenv('TWITTER_ACCESS_TOKEN'), os.getenv(
            'TWITTER_ACCESS_TOKEN_SECRET'))
        api = tweepy.API(auth)

        try:
            media_ids = []

            for post_image in post_images:
                media = api.media_upload(post_image.image.path)
                media_ids.append(media.media_id)

            # Post the uploaded media to Twitter
            status = api.update_status(status=post.title, media_ids=media_ids)

            return Response({
                "statusCode": status.HTTP_200_OK,
                "message": "Twitter post successfully created.",
                "data": {"tweet_id": status.id_str}
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Server error",
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
