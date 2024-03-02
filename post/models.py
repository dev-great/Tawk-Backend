from time import time
from django.db import models
from django.urls import reverse
from django.utils import timezone
from authorization.models import CustomUser
from apscheduler.schedulers.background import BackgroundScheduler
from ckeditor.fields import RichTextField


class Post(models.Model):
    title = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="scheduled_post"
    )
    image = models.URLField(max_length=200)
    body = RichTextField(blank=True, null=True)
    published_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-published_at",)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:blog_detail", args=[self.slug])
