from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from post.models import Post, PostImage
from post.serializers import ImageSerializer, PostSerializer, UpdatePostSerializer


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
