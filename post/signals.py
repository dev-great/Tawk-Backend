# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.utils import timezone
# from .models import Post


# @receiver(post_save, sender=Post)
# def update_is_published(sender, instance, **kwargs):
#     if not instance.isPublish and instance.created_on.date() == timezone.now().date():
#         instance.isPublish = True
#         instance.save(update_fields=['isPublish'])
