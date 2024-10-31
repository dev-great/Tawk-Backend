from time import time
import uuid
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


def get_post_image_upload_path(instance, filename):
    folder_path = f"fufumaps/menu_item/{instance.menu_item_id}/{timezone.now().strftime('%Y/%m/%d')}/"
    return folder_path + filename


class PostImage(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    post_id = models.ForeignKey(
        'Post', on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to=get_post_image_upload_path, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_on']


class Post(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    title = models.CharField(max_length=250,)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="post")
    body = models.TextField(blank=True, null=True)
    isPublish = models.BooleanField(default=False)
    scheduled_publish = models.DateTimeField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_on",)

    def __str__(self):
        return self.title
