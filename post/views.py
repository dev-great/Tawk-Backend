from post.models import Post
from rest_framework import generics
from post.serializers import PostSerializer, UpdatePostSerializer


class PostList(generics.ListCreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer


class PostUpdate(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post
    serializer_class = UpdatePostSerializer
