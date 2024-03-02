from post.models import Post
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from post.serializers import PostSerializer, UpdatePostSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

"""This view is to create a new post"""

class CreatePost(generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = IsAuthenticated

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(
            {"message": "Post Created", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )

""""This view is to view created posts"""
class PostList(generics.ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def get(self, request, *args, **kwargs):
        post = Post.objects.all()
        serializer = self.serializer_class(post, many=True)
        return Response(
            {"message": "Scheduled Pos", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

"""This view is to update the post"""

class UpdatePost(generics.UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = UpdatePostSerializer
    permission_classes =  IsAuthenticated

    def patch(self, request, customuser_id, *args, **kwargs):
        if request.c == "buyer":
            post_update = Post.objects.get(id=customuser_id)
            serializer = self.serializer_class(
                post_update, data=request.data
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(buyer=request.user)
            return Response(
                {"message": "Post  Updated Successfully"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"message": "You are not authorised to update this post"},
                status=status.HTTP_400_BAD_REQUEST,
            )

class PostDetail(generics.RetrieveAPIView):
    queryset = Post
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        post = get_object_or_404(self.queryset, pk=pk)
        serializer = self.serializer_class(post)

        if Post.objects.filter(id=pk).exists():
            return Response(
                {"message": "Post Details retrieved", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "message": "Post not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )


"""This view is to delete the post"""

class DeletePost(generics.DestroyAPIView):
    queryset = Post
    serializer_class = UpdatePostSerializer
    permission_classes = IsAuthenticated

    def delete(self, request, pk):
        post = Post.objects.filter(id=pk)

        if Post.objects.filter(id=pk).exists():
            post.delete()
            return Response({"message": "Post deleted"}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "Post does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
