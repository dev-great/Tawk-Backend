from django.urls import path
from post.views import CreatePostAPIView, DeletePostAPIView, ImageView, PostToFacebookView, PostToInstagramView, PostToTwitterView, UpdatePostAPIView, UserPostsAPIView

urlpatterns = [
    path('delete-post/', DeletePostAPIView.as_view(), name='delete_post'),
    path('get-posts/', UserPostsAPIView.as_view(), name='user_posts'),
    path('create-post/', CreatePostAPIView.as_view(), name='create_post'),
    path('edit-post/', UpdatePostAPIView.as_view(), name='edit_post'),
    path('create-post-image/', ImageView.as_view(), name='create_post_image'),

    # FACEBOOK
    path('post-to-facebook/', PostToFacebookView.as_view(), name='post_to_facebook'),

    # INSTAGRAM
    path('post-to-instagram/', PostToInstagramView.as_view(),
         name='post_to_instagram'),

    # TWITTER
    path('post-to-twitter/', PostToTwitterView.as_view(), name='post_to_twitter'),


]
