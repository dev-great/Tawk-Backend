from rest_framework import serializers

from notification.models import NotificationPost


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPost
        fields = '__all__'
