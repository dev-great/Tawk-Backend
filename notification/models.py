import uuid
from django.db import models
from authorization.models import CustomUser

# Create your models here.


class NotificationPost(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    title = models.CharField(max_length=300)
    body = models.CharField(max_length=500, blank=True,
                            null=True)
    date = models.DateTimeField(auto_now_add=True)
    unread = models.BooleanField(default=True)
    target = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, default=None, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date',)

    def __str__(self):
        return self.body[:100]
