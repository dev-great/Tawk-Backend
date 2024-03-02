from django.urls import path
from post.views import PostList, PostUpdate

urlpatterns = [
    path("", PostList.as_view()),
    path("post/edit/<int:pk>", PostUpdate.as_view()),
]
