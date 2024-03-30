from django.urls import path
from post.views import CreatePostAPIView, DeletePostAPIView, ImageView, UpdatePostAPIView, UserPostsAPIView

urlpatterns = [
    path('delete-post/', DeletePostAPIView.as_view(), name='delete_post'),
    path('get-posts/', UserPostsAPIView.as_view(), name='user_posts'),
    path('create-post/', CreatePostAPIView.as_view(), name='create_post'),
    path('edit-post/', UpdatePostAPIView.as_view(), name='edit_post'),
    path('create-post-image/', ImageView.as_view(), name='create_post_image'),
]
