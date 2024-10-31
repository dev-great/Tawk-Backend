from .models import SocialUser
from rest_framework import serializers

class SocialUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialUser
        fields = '__all__'
