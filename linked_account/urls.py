from django.urls import path
from .views import DiscordLoginView, DiscordRedirectView, FacebookLoginView, FacebookRedirectView, GoogleBusinessLoginView, GoogleBusinessRedirectView, InstagramLoginView, InstagramRedirectView, LinkedInLoginView, LinkedInRedirectView, MediumLoginView, MediumRedirectView, PinterestLoginView, PinterestRedirectView, SlackLoginView, SlackRedirectView, TelegramLoginView, TelegramRedirectView, ThreadLoginView, ThreadRedirectView, TikTokLoginView, TikTokRedirectView, TumblrLoginView, TumblrRedirectView, TwitterLoginView, TwitterRedirectView, WhatsAppLoginView, WhatsAppRedirectView, YouTubeLoginView, YouTubeRedirectView

app_name = 'linked_account'

urlpatterns = [
    #FACEBOOK
    path('facebook/connect/', FacebookLoginView.as_view(), name='facebook-login'),
    path('facebook/callback/', FacebookRedirectView.as_view(), name='facebook-redirect'),
    
    #INSTAGRAM
    path('instagram/connect/', InstagramRedirectView.as_view(), name='instagram-login'),
    path('instagram/callback/', InstagramLoginView.as_view(), name='instagram-callback'),
    
    #LINKEDIN
    path('linkedin/callback/', LinkedInRedirectView.as_view(), name='linkedin_redirect'),
    path('linkedin/connect/', LinkedInLoginView.as_view(), name='linkedin_login'),
    
    #PINTREST
    path('pinterest/callback/', PinterestRedirectView.as_view(), name='pinterest_redirect'),
    path('pinterest/connect/', PinterestLoginView.as_view(), name='pinterest_login'),
    
    #TIKTOK
    path('tiktok/callback/', TikTokRedirectView.as_view(), name='tiktok_redirect'),
    path('tiktok/connect/', TikTokLoginView.as_view(), name='tiktok_login'),

    #THREAD 
    path('thread/callback/', ThreadRedirectView.as_view(), name='thread_redirect'),
    path('thread/connect/', ThreadLoginView.as_view(), name='thread_login'),
    
    # TWITTER
    path('twitter/callback/', TwitterRedirectView.as_view(), name='twitter_redirect'),
    path('twitter/connect/', TwitterLoginView.as_view(), name='twitter_login'),

    # YOUTUBE
    path('youtube/connect/', YouTubeLoginView.as_view(), name='youtube_login'),
    path('youtube/callback/', YouTubeRedirectView.as_view(), name='youtube_redirect'),
    
    # GOOGLE BUSINESS
    path('google-business/connect/', GoogleBusinessLoginView.as_view(), name='google_business_login'),
    path('google-business/callback/', GoogleBusinessRedirectView.as_view(), name='google_business_redirect'),
    
    #SLACK
    path('slack/connect/', SlackLoginView.as_view(), name='slack_login'),
    path('slack/callback/', SlackRedirectView.as_view(), name='slack_redirect'),

    #DISCORD
    path('discord/connect/', DiscordLoginView.as_view(), name='discord_login'),
    path('discord/callback/', DiscordRedirectView.as_view(), name='discord_redirect'),

    # Tumblr
    path('tumblr/connect/', TumblrLoginView.as_view(), name='tumblr_login'),
    path('tumblr/callback/', TumblrRedirectView.as_view(), name='tumblr_redirect'),
    
    # Medium
    path('medium/connect/', MediumLoginView.as_view(), name='medium_login'),
    path('medium/callback/', MediumRedirectView.as_view(), name='medium_redirect'),
    
    # Telegram
    path('telegram/connect/', TelegramLoginView.as_view(), name='telegram_login'),
    path('telegram/callback/', TelegramRedirectView.as_view(), name='telegram_redirect'),
    
    # WhatsApp
    path('whatsapp/connect/', WhatsAppLoginView.as_view(), name='whatsapp_login'),
    path('whatsapp/callback/', WhatsAppRedirectView.as_view(), name='whatsapp_redirect'),

]
