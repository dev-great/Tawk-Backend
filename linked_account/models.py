from datetime import timezone
import uuid
from django.db import models

from authorization.models import CustomUser

# Create your models here.

class SocialUser(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    user_id = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    
    # FACEBOOK ACCOUNT
    facebook_id = models.CharField(max_length=255, blank=True, null=True) 
    facebook_access_token = models.CharField(max_length=255, blank=True, null=True)  
    facebook_page_id = models.CharField(max_length=255, blank=True, null=True) 
    facebook_token_expires_in = models.DateTimeField(null=True, blank=True)
    
    # GOOGLE ACCOUNT
    youtube_id = models.CharField(max_length=255, blank=True, null=True) 
    youtube_access_token = models.CharField(max_length=255, blank=True, null=True)  
    youtube_token_expires_in = models.DateTimeField(null=True, blank=True)
    
    
    google_business_access_token = models.CharField(max_length=255, blank=True, null=True) 
    google_business_token_expires_in = models.DateTimeField(null=True, blank=True)
    
    instagram_access_token = models.CharField(max_length=255, blank=True, null=True) 
    instagram_id = models.CharField(max_length=255, blank=True, null=True) 
    instagram_token_expires_in = models.DateTimeField(null=True, blank=True)
    
    linkedin_access_token = models.CharField(max_length=255, blank=True, null=True) 
    linkedin_id = models.CharField(max_length=255, blank=True, null=True) 
    linkedin_token_expires_in = models.DateTimeField(null=True, blank=True)
    
    pinterest_access_token = models.CharField(max_length=255, blank=True, null=True) 
    pinterest_id = models.CharField(max_length=255, blank=True, null=True) 
    pinterest_token_expires_in = models.DateTimeField(null=True, blank=True)
    
    tiktok_access_token = models.CharField(max_length=255, blank=True, null=True) 
    tiktok_id = models.CharField(max_length=255, blank=True, null=True) 
    tiktok_token_expires_in = models.DateTimeField(null=True, blank=True)
    
    thread_access_token = models.CharField(max_length=255, blank=True, null=True) 
    thread_id = models.CharField(max_length=255, blank=True, null=True) 
    thread_token_expires_in = models.DateTimeField(null=True, blank=True)
    
    twitter_access_token = models.CharField(max_length=255, blank=True, null=True) 
    twitter_id = models.CharField(max_length=255, blank=True, null=True) 
    twitter_token_expires_in = models.DateTimeField(null=True, blank=True)
    
    slack_access_token = models.CharField(max_length=255, blank=True, null=True) 
    slack_id = models.CharField(max_length=255, blank=True, null=True) 
    slack_token_expires_in = models.DateTimeField(null=True, blank=True)
    
    discord_access_token = models.CharField(max_length=255, blank=True, null=True) 
    discord_id = models.CharField(max_length=255, blank=True, null=True)
    discord_token_expires_in = models.DateTimeField(null=True, blank=True) 
    
    tumblr_access_token = models.CharField(max_length=255, blank=True, null=True) 
    tumblr_id = models.CharField(max_length=255, blank=True, null=True) 
    tumblr_token_expires_in = models.DateTimeField(null=True, blank=True)
    
    medium_access_token = models.CharField(max_length=255, blank=True, null=True) 
    medium_id = models.CharField(max_length=255, blank=True, null=True) 
    medium_token_expires_in = models.DateTimeField(null=True, blank=True)
    
    telegram_access_token = models.CharField(max_length=255, blank=True, null=True) 
    telegram_id = models.CharField(max_length=255, blank=True, null=True) 
    telegram_token_expires_in = models.DateTimeField(null=True, blank=True)
    
    whatsapp_access_token = models.CharField(max_length=255, blank=True, null=True) 
    whatsapp_id = models.CharField(max_length=255, blank=True, null=True) 
    whatsapp_token_expires_in = models.DateTimeField(null=True, blank=True)
    
  
