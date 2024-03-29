from django.urls import path
from post.views import PostList, UpdatePost, CreatePost, DeletePost

urlpatterns = [
    path("", PostList.as_view()),
    path("post/create/", CreatePost.as_view()),
    path("post/edit/<int:pk>", UpdatePost.as_view()),
    path("post/delete/", DeletePost.as_view()),
]
