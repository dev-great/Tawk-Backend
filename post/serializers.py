from dataclasses import field
from rest_framework import serializers
from post.models import Post, PostImage


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["title", "author", "body"]


class UpdatePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["title", "body"]
