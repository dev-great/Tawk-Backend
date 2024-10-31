from django.urls import path
from post.views import CreatePostAPIView, DeletePostAPIView, ImageView,  UpdatePostAPIView, UserPostsAPIView

app_name = 'post'
urlpatterns = [
    path('post/delete-post/', DeletePostAPIView.as_view(), name='delete_post'),
    path('post/get-posts/', UserPostsAPIView.as_view(), name='user_posts'),
    path('post/create-post/', CreatePostAPIView.as_view(), name='create_post'),
    path('post/edit-post/', UpdatePostAPIView.as_view(), name='edit_post'),
    path('post/create-post-image/', ImageView.as_view(), name='create_post_image'),
]
