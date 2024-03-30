import logging
from celery import shared_task
from django.utils import timezone
from .models import Post

logger = logging.getLogger(__name__)


@shared_task
def publish_scheduled_posts():
    logger.info("Publishing scheduled posts...")
    logger.info(f"Current time: {timezone.now()}")
    now = timezone.now()
    print(now)
    scheduled_posts = Post.objects.filter(
        isPublish=False, scheduled_publish__lte=now)

    for post in scheduled_posts:
        logger.info(f"Publishing post with id {post.id}")
        post.isPublish = True
        post.save()
