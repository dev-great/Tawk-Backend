from dataclasses import field
from rest_framework import serializers
from post.models import Post


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["title", "slug", "author", "image", "body"]


class UpdatePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["title", "slug", "image", "body"]
