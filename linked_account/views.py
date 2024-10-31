# views.py
from datetime import timedelta, timezone
from django.conf import settings
from django.shortcuts import redirect
import requests
from .models import *
from exceptions.custom_apiexception_class import *
from rest_framework import status
from rest_framework.views import APIView
from utils.custom_response import custom_response
from rest_framework.permissions import  IsAuthenticated


class FacebookLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def get_facebook_access_token(self, code):
        """Function to exchange code for access token"""
        token_url = f'https://graph.facebook.com/v14.0/oauth/access_token'
        params = {
            'client_id': settings.FACEBOOK_APP_ID,
            'redirect_uri': settings.FACEBOOK_REDIRECT_URI,  # Callback URL
            'client_secret': settings.FACEBOOK_APP_SECRET,
            'code': code
        }
        response = requests.get(token_url, params=params)
        return response.json()

    def get_facebook_pages(self, access_token):
        """Fetch the user's Facebook Pages"""
        pages_url = 'https://graph.facebook.com/v14.0/me/accounts'
        params = {
            'access_token': access_token
        }
        response = requests.get(pages_url, params=params)
        return response.json()

    def exchange_for_long_lived_token(self, short_lived_token):
        """Function to exchange short-lived token for long-lived token"""
        token_exchange_url = 'https://graph.facebook.com/v14.0/oauth/access_token'
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': settings.FACEBOOK_APP_ID,
            'client_secret': settings.FACEBOOK_APP_SECRET,
            'fb_exchange_token': short_lived_token
        }
        response = requests.get(token_exchange_url, params=params)
        return response.json()


    def post(self, request, *args, **kwargs):
        code = request.GET.get('code')
        if not code:
            return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Authorization code is required")

        try:
            # Exchange the code for an access token
            token_data = self.get_facebook_access_token(code)
            short_lived_token = token_data.get('access_token')

            if not short_lived_token:
                raise CustomAPIException(detail="Failed to retrieve access token from Facebook", status_code=status.HTTP_400_BAD_REQUEST)


            # Exchange short-lived token for long-lived token
            long_token_data = self.exchange_for_long_lived_token(short_lived_token)
            long_lived_token = long_token_data.get('access_token')
            expires_in = long_token_data.get('expires_in')  # Validity of long-lived token (about 60 days)

            # Fetch the user's Facebook Pages
            pages_data = self.get_facebook_pages(long_lived_token)
            pages = pages_data.get('data', [])

            if not pages:
                raise CustomAPIException(detail="No Facebook Pages found for the user", status_code=status.HTTP_400_BAD_REQUEST)

            # Select the first Page (or implement logic to let the user choose)
            page_id = pages[0]['id']


            # Save or update the user's SocialUser model
            social_user, created = SocialUser.objects.get_or_create(user_id=request.user)
            social_user.facebook_access_token = long_lived_token
            social_user.facebook_id = token_data.get('user_id')  
            social_user.facebook_page_id = page_id  
            social_user.facebook_token_expires_in = timezone.now() + timedelta(seconds=expires_in)
            social_user.save()

            return custom_response(status_code=status.HTTP_200_OK, message="Facebook account connected successfully", data={"facebook_id": social_user.facebook_id})

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()
        
        
class FacebookRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Redirect user to Facebook OAuth URL
        facebook_login_url = (
            "https://www.facebook.com/v14.0/dialog/oauth?"
            f"client_id={settings.FACEBOOK_APP_ID}&"
            f"redirect_uri={settings.FACEBOOK_REDIRECT_URI}&"
            f"scope=pages_manage_posts,pages_read_engagement,user_posts,publish_to_groups,publish_pages,user_photos,user_videos"  
        )
        return redirect(facebook_login_url)

class YouTubeLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def get_youtube_access_token(self, code):
        """Function to exchange code for access token"""
        token_url = 'https://oauth2.googleapis.com/token'
        data = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': settings.YOUTUBE_REDIRECT_URI,
            'code': code,
            'grant_type': 'authorization_code'
        }
        response = requests.post(token_url, data=data)
        return response.json()

    def get_youtube_user_info(self, access_token):
        """Fetch the user's YouTube account info"""
        user_info_url = 'https://www.googleapis.com/youtube/v3/channels?part=id&mine=true'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(user_info_url, headers=headers)
        return response.json()

    def post(self, request, *args, **kwargs):
        code = request.GET.get('code')
        if not code:
            return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Authorization code is required")

        try:
            # Exchange the code for an access token
            token_data = self.get_youtube_access_token(code)
            access_token = token_data.get('access_token')

            if not access_token:
                raise CustomAPIException(detail="Failed to retrieve access token from YouTube", status_code=status.HTTP_400_BAD_REQUEST)

            # Fetch the user's YouTube account info
            user_info = self.get_youtube_user_info(access_token)
            youtube_id = user_info['items'][0]['id'] if user_info['items'] else None

            # Save or update the user's SocialUser model
            social_user, created = SocialUser.objects.get_or_create(user_id=request.user)
            social_user.youtube_access_token = access_token
            social_user.youtube_id = youtube_id
            social_user.youtube_token_expires_in = timezone.now() + timedelta(seconds=token_data.get('expires_in', 3600))
            social_user.save()

            return custom_response(status_code=status.HTTP_200_OK, message="YouTube account connected successfully", data={"youtube_id": social_user.youtube_id})

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()

class YouTubeRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Redirect user to YouTube OAuth URL
        youtube_login_url = (
            "https://accounts.google.com/o/oauth2/auth?"
            f"client_id={settings.GOOGLE_CLIENT_ID}&"
            f"redirect_uri={settings.YOUTUBE_REDIRECT_URI}&"
            f"scope=https://www.googleapis.com/auth/youtube "
            f"https://www.googleapis.com/auth/youtube.upload "
            f"https://www.googleapis.com/auth/youtube.readonly&"
            "response_type=code"
        )
        return redirect(youtube_login_url)


class GoogleBusinessLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def get_google_business_access_token(self, code):
        """Function to exchange code for access token"""
        token_url = 'https://oauth2.googleapis.com/token'
        data = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_BUSINESS_REDIRECT_URI,
            'code': code,
            'grant_type': 'authorization_code'
        }
        response = requests.post(token_url, data=data)
        return response.json()

    def get_google_business_user_info(self, access_token):
        """Fetch the user's Google Business account info"""
        user_info_url = 'https://www.googleapis.com/business/v1/locations'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(user_info_url, headers=headers)
        return response.json()

    def post(self, request, *args, **kwargs):
        code = request.GET.get('code')
        if not code:
            return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Authorization code is required")

        try:
            # Exchange the code for an access token
            token_data = self.get_google_business_access_token(code)
            access_token = token_data.get('access_token')

            if not access_token:
                raise CustomAPIException(detail="Failed to retrieve access token from Google Business", status_code=status.HTTP_400_BAD_REQUEST)

            # Fetch the user's Google Business account info
            user_info = self.get_google_business_user_info(access_token)
            # Process the Google Business user info as needed

            # Save or update the user's SocialUser model
            social_user, created = SocialUser.objects.get_or_create(user_id=request.user)
            social_user.google_business_access_token = access_token
            # Save other relevant information as needed
            social_user.save()

            return custom_response(status_code=status.HTTP_200_OK, message="Google Business account connected successfully")

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()

class GoogleBusinessRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Redirect user to Google Business OAuth URL
        google_business_login_url = (
            "https://accounts.google.com/o/oauth2/auth?"
            f"client_id={settings.GOOGLE_CLIENT_ID}&"
            f"redirect_uri={settings.GOOGLE_BUSINESS_REDIRECT_URI}&"
            f"scope=https://www.googleapis.com/auth/business.manage "
            f"https://www.googleapis.com/auth/businessinformation "
            f"https://www.googleapis.com/auth/business.messaging&"
            "response_type=code"
        )
        return redirect(google_business_login_url)



class InstagramLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def get_instagram_access_token(self, code):
        """Function to exchange code for access token"""
        token_url = 'https://api.instagram.com/oauth/access_token'
        data = {
            'client_id': settings.INSTAGRAM_CLIENT_ID,
            'client_secret': settings.INSTAGRAM_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'redirect_uri': settings.INSTAGRAM_REDIRECT_URI,  # Your redirect URI
            'code': code
        }
        response = requests.post(token_url, data=data)
        return response.json()

    def get_user_media(self, access_token):
        """Fetch the user's Instagram media"""
        media_url = f'https://graph.instagram.com/me/media?access_token={access_token}'
        response = requests.get(media_url)
        return response.json()

    def post(self, request, *args, **kwargs):
        code = request.GET.get('code')
        if not code:
            return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Authorization code is required")

        try:
            # Exchange the code for an access token
            token_data = self.get_instagram_access_token(code)
            access_token = token_data.get('access_token')

            if not access_token:
                raise CustomAPIException(detail="Failed to retrieve access token from Instagram", status_code=status.HTTP_400_BAD_REQUEST)

            # Fetch the user's Instagram media
            media_data = self.get_user_media(access_token)

            # Save or update the user's SocialUser model
            social_user, created = SocialUser.objects.get_or_create(user_id=request.user)
            social_user.instagram_access_token = access_token
            social_user.instagram_id = token_data.get('user_id')  # Get the user's Instagram ID
            social_user.save()

            return custom_response(status_code=status.HTTP_200_OK, message="Instagram account connected successfully", data={"instagram_id": social_user.instagram_id})

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()
        
        
class InstagramRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Redirect user to Instagram OAuth URL with all scopes
        instagram_login_url = (
            "https://api.instagram.com/oauth/authorize?"
            f"client_id={settings.INSTAGRAM_CLIENT_ID}&"
            f"redirect_uri={settings.INSTAGRAM_REDIRECT_URI}&"
            f"scope=instagram_basic,instagram_content_publish,instagram_manage_comments,instagram_manage_insights,"
            f"instagram_graph_user_media,instagram_graph_user_profile&"
            "response_type=code"
        )
        return redirect(instagram_login_url)



class LinkedInLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def get_linkedin_access_token(self, code):
        """Function to exchange code for access token"""
        token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.LINKEDIN_REDIRECT_URI,
            'client_id': settings.LINKEDIN_CLIENT_ID,
            'client_secret': settings.LINKEDIN_CLIENT_SECRET,
        }
        response = requests.post(token_url, data=data)
        return response.json()

    def get_user_profile(self, access_token):
        """Fetch the user's LinkedIn profile"""
        profile_url = 'https://api.linkedin.com/v2/me'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(profile_url, headers=headers)
        return response.json()

    def post(self, request, *args, **kwargs):
        code = request.GET.get('code')
        if not code:
            return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Authorization code is required")

        try:
            # Exchange the code for an access token
            token_data = self.get_linkedin_access_token(code)
            access_token = token_data.get('access_token')

            if not access_token:
                raise CustomAPIException(detail="Failed to retrieve access token from LinkedIn", status_code=status.HTTP_400_BAD_REQUEST)

            # Fetch the user's LinkedIn profile
            profile_data = self.get_user_profile(access_token)

            # Save or update the user's SocialUser model
            social_user, created = SocialUser.objects.get_or_create(user_id=request.user)
            social_user.linkedin_access_token = access_token
            social_user.linkedin_id = profile_data.get('id')  # Get the user's LinkedIn ID
            social_user.save()

            return custom_response(status_code=status.HTTP_200_OK, message="LinkedIn account connected successfully", data={"linkedin_id": social_user.linkedin_id})

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()


class LinkedInRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Redirect user to LinkedIn OAuth URL with all scopes
        linkedin_login_url = (
            "https://www.linkedin.com/oauth/v2/authorization?"
            f"response_type=code&"
            f"client_id={settings.LINKEDIN_CLIENT_ID}&"
            f"redirect_uri={settings.LINKEDIN_REDIRECT_URI}&"
            f"scope=r_liteprofile%20r_emailaddress%20w_member_social%20rw_organization_admin%20"
            f"r_fullprofile%20w_organization_social%20r_organization_social%20w_video"  
        )
        return redirect(linkedin_login_url)


class PinterestLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def get_pinterest_access_token(self, code):
        """Function to exchange code for access token"""
        token_url = 'https://api.pinterest.com/v1/oauth/token'
        data = {
            'client_id': settings.PINTEREST_CLIENT_ID,
            'client_secret': settings.PINTEREST_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.PINTEREST_REDIRECT_URI,
        }
        response = requests.post(token_url, data=data)
        return response.json()

    def get_user_profile(self, access_token):
        """Fetch the user's Pinterest profile"""
        profile_url = 'https://api.pinterest.com/v1/me/?access_token=' + access_token
        response = requests.get(profile_url)
        return response.json()

    def post(self, request, *args, **kwargs):
        code = request.GET.get('code')
        if not code:
            return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Authorization code is required")

        try:
            # Exchange the code for an access token
            token_data = self.get_pinterest_access_token(code)
            access_token = token_data.get('access_token')

            if not access_token:
                raise CustomAPIException(detail="Failed to retrieve access token from Pinterest", status_code=status.HTTP_400_BAD_REQUEST)

            # Fetch the user's Pinterest profile
            profile_data = self.get_user_profile(access_token)

            # Save or update the user's SocialUser model
            social_user, created = SocialUser.objects.get_or_create(user_id=request.user)
            social_user.pinterest_access_token = access_token
            social_user.pinterest_id = profile_data.get('id')  # Get the user's Pinterest ID
            social_user.save()

            return custom_response(status_code=status.HTTP_200_OK, message="Pinterest account connected successfully", data={"pinterest_id": social_user.pinterest_id})

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()


class PinterestRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Redirect user to Pinterest OAuth URL with full scopes
        pinterest_login_url = (
            "https://api.pinterest.com/oauth?"
            f"response_type=code&"
            f"client_id={settings.PINTEREST_CLIENT_ID}&"
            f"redirect_uri={settings.PINTEREST_REDIRECT_URI}&"
            f"scope=read_public,write_public,read_relationships,write_relationships,read_images,read_boards,write_boards,read_pins,write_pins"  # Added scopes
        )
        return redirect(pinterest_login_url)




class TikTokLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def get_tiktok_access_token(self, code):
        """Function to exchange code for access token"""
        token_url = 'https://www.tiktok.com/v2/auth/authorize/'
        data = {
            'client_key': settings.TIKTOK_CLIENT_ID,
            'client_secret': settings.TIKTOK_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': settings.TIKTOK_REDIRECT_URI,
        }
        response = requests.post(token_url, data=data)
        return response.json()

    def get_user_profile(self, access_token):
        """Fetch the user's TikTok profile"""
        profile_url = 'https://open-api.tiktok.com/user/profile/'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(profile_url, headers=headers)
        return response.json()

    def post(self, request, *args, **kwargs):
        code = request.GET.get('code')
        if not code:
            return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Authorization code is required")

        try:
            # Exchange the code for an access token
            token_data = self.get_tiktok_access_token(code)
            access_token = token_data.get('access_token')

            if not access_token:
                raise CustomAPIException(detail="Failed to retrieve access token from TikTok", status_code=status.HTTP_400_BAD_REQUEST)

            # Fetch the user's TikTok profile
            profile_data = self.get_user_profile(access_token)

            # Save or update the user's SocialUser model
            social_user, created = SocialUser.objects.get_or_create(user_id=request.user)
            social_user.tiktok_access_token = access_token
            social_user.tiktok_id = profile_data.get('data', {}).get('id')  # Get the user's TikTok ID
            social_user.save()

            return custom_response(status_code=status.HTTP_200_OK, message="TikTok account connected successfully", data={"tiktok_id": social_user.tiktok_id})

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()


class TikTokRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Redirect user to TikTok OAuth URL with all scopes
        tiktok_login_url = (
            "https://open-api.tiktok.com/oauth/authorize?"
            f"client_key={settings.TIKTOK_CLIENT_ID}&"
            f"response_type=code&"
            f"redirect_uri={settings.TIKTOK_REDIRECT_URI}&"
            f"scope=user.info.basic,user.info.edit,video.list,video.upload,"
            f"video.delete,video.like,video.comment,video.favorites,"
            f"user.follower.list,user.following.list,user.share"
        )
        return redirect(tiktok_login_url)

class ThreadLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def exchange_code_for_token(self, code):
        """Function to exchange code for a short-lived access token."""
        token_url = 'https://graph.threads.net/oauth/access_token' 
        params = {
            'client_id': settings.THREAD_CLIENT_ID,
            'client_secret': settings.THREAD_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': settings.THREAD_REDIRECT_URI,
        }
        response = requests.post(token_url, params=params)
        return response.json()

    def exchange_short_lived_for_long_lived(self, short_lived_token):
        """Exchange short-lived access token for a long-lived token."""
        long_lived_token_url = 'https://graph.threads.net/oauth/access_token'  
        params = {
            'client_id': settings.THREAD_CLIENT_ID,
            'client_secret': settings.THREAD_CLIENT_SECRET,
            'grant_type': 'fb_exchange_token',
            'fb_exchange_token': short_lived_token,  
        }
        response = requests.post(long_lived_token_url, params=params)
        return response.json()

    def get_user_profile(self, access_token):
        """Fetch the user's Thread profile."""
        profile_url = 'https://graph.threads.net/me?fields=id,username,name,threads_profile_picture_url,threads_biography'  # Updated URL
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(profile_url, headers=headers)
        return response.json()

    def post(self, request, *args, **kwargs):
        code = request.GET.get('code')
        if not code:
            return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Authorization code is required")

        try:
            # Exchange the code for a short-lived access token
            token_data = self.exchange_code_for_token(code)
            short_lived_access_token = token_data.get('access_token')

            if not short_lived_access_token:
                raise CustomAPIException(detail="Failed to retrieve short-lived access token from Thread", status_code=status.HTTP_400_BAD_REQUEST)

            # Exchange short-lived token for long-lived token
            long_lived_token_data = self.exchange_short_lived_for_long_lived(short_lived_access_token)
            long_lived_access_token = long_lived_token_data.get('access_token')

            if not long_lived_access_token:
                raise CustomAPIException(detail="Failed to retrieve long-lived access token from Thread", status_code=status.HTTP_400_BAD_REQUEST)

            # Fetch the user's Thread profile
            profile_data = self.get_user_profile(long_lived_access_token)

            # Save or update the user's SocialUser model
            social_user, created = SocialUser.objects.get_or_create(user_id=request.user)
            social_user.thread_access_token = long_lived_access_token
            social_user.thread_id = profile_data.get('id')  # Get the user's Thread ID
            social_user.save()

            return custom_response(status_code=status.HTTP_200_OK, message="Thread account connected successfully", data={"thread_id": social_user.thread_id})

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()


class ThreadRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Redirect user to Thread OAuth URL with required scopes
        thread_login_url = (
            "https://api.thread.com/oauth/authorize?"
            f"client_id={settings.THREAD_CLIENT_ID}&"
            f"response_type=code&"
            f"redirect_uri={settings.THREAD_REDIRECT_URI}&"
            f"scope=read_profile,write_profile,read_posts,write_posts"
        )
        return redirect(thread_login_url)


class TwitterLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def exchange_code_for_token(self, code):
        """Function to exchange code for an access token."""
        token_url = 'https://api.twitter.com/oauth2/token'  # Adjust URL for Twitter API
        params = {
            'client_id': settings.TWITTER_CLIENT_ID,
            'client_secret': settings.TWITTER_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': settings.TWITTER_REDIRECT_URI,
        }
        response = requests.post(token_url, params=params)
        return response.json()

    def get_user_profile(self, access_token):
        """Fetch the user's Twitter profile."""
        profile_url = 'https://api.twitter.com/2/me'  # Update to the correct profile endpoint
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(profile_url, headers=headers)
        return response.json()

    def post(self, request, *args, **kwargs):
        code = request.GET.get('code')
        if not code:
            return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Authorization code is required")

        try:
            # Exchange the code for an access token
            token_data = self.exchange_code_for_token(code)
            access_token = token_data.get('access_token')

            if not access_token:
                raise CustomAPIException(detail="Failed to retrieve access token from Twitter", status_code=status.HTTP_400_BAD_REQUEST)

            # Fetch the user's Twitter profile
            profile_data = self.get_user_profile(access_token)

            # Save or update the user's SocialUser model
            social_user, created = SocialUser.objects.get_or_create(user_id=request.user)
            social_user.twitter_access_token = access_token
            social_user.twitter_id = profile_data.get('id')  # Get the user's Twitter ID
            social_user.save()

            return custom_response(status_code=status.HTTP_200_OK, message="Twitter account connected successfully", data={"twitter_id": social_user.twitter_id})

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()

class TwitterRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Redirect user to Twitter OAuth URL with required scopes
        twitter_login_url = (
            "https://api.twitter.com/oauth/authorize?"
            f"client_id={settings.TWITTER_CLIENT_ID}&"
            f"response_type=code&"
            f"redirect_uri={settings.TWITTER_REDIRECT_URI}&"
            f"scope="
            "tweet.read,tweet.write,tweet.moderate.write,"
            "user.read,user.write,"
            "like.read,like.write,"
            "list.read,list.write,"
            "follows.read,follows.write,"
            "spaces.read,spaces.write,"
            "bookmark.read,bookmark.write"
        )
        return redirect(twitter_login_url)


class SlackLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def exchange_code_for_token(self, code):
        """Function to exchange code for an access token."""
        token_url = 'https://slack.com/api/oauth.v2.access'
        params = {
            'client_id': settings.SLACK_CLIENT_ID,
            'client_secret': settings.SLACK_CLIENT_SECRET,
            'code': code,
            'redirect_uri': settings.SLACK_REDIRECT_URI,
        }
        response = requests.post(token_url, params=params)
        return response.json()

    def get_user_profile(self, access_token):
        """Fetch the user's Slack profile."""
        profile_url = 'https://slack.com/api/users.profile.get'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(profile_url, headers=headers)
        return response.json()

    def post(self, request, *args, **kwargs):
        code = request.GET.get('code')
        if not code:
            return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Authorization code is required")

        try:
            # Exchange the code for an access token
            token_data = self.exchange_code_for_token(code)
            access_token = token_data.get('access_token')

            if not access_token:
                raise CustomAPIException(detail="Failed to retrieve access token from Slack", status_code=status.HTTP_400_BAD_REQUEST)

            # Fetch the user's Slack profile
            profile_data = self.get_user_profile(access_token)

            # Save or update the user's SocialUser model
            social_user, created = SocialUser.objects.get_or_create(user_id=request.user)
            social_user.slack_access_token = access_token
            social_user.slack_id = profile_data.get('user', {}).get('id')  # Get the user's Slack ID
            social_user.save()

            return custom_response(status_code=status.HTTP_200_OK, message="Slack account connected successfully", data={"slack_id": social_user.slack_id})

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()

class SlackRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Redirect user to Slack OAuth URL with required scopes
        slack_login_url = (
            "https://slack.com/api/oauth/authorize?"
            f"client_id={settings.SLACK_CLIENT_ID}&"
            f"scope="
            "channels:read,channels:manage,"
            "groups:read,groups:manage,"
            "im:read,im:write,"
            "mpim:read,mpim:write,"
            "users:read,users:read.email,"
            "chat:write,chat:write.public,"
            "files:read,files:write,"
            "events:read,events:write,"
            "app_mentions:read,app_home:read,"
            "oauth:write"
        )
        return redirect(slack_login_url)


class DiscordLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def exchange_code_for_token(self, code):
        """Function to exchange code for an access token."""
        token_url = 'https://discord.com/api/oauth2/token'
        data = {
            'client_id': settings.DISCORD_CLIENT_ID,
            'client_secret': settings.DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.DISCORD_REDIRECT_URI,
            'scope': 'identify email guilds'
        }
        response = requests.post(token_url, data=data)
        return response.json()

    def get_user_profile(self, access_token):
        """Fetch the user's Discord profile."""
        profile_url = 'https://discord.com/api/v10/users/@me'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(profile_url, headers=headers)
        return response.json()

    def post(self, request, *args, **kwargs):
        code = request.data.get('code')
        if not code:
            return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Authorization code is required")

        try:
            # Exchange the code for an access token
            token_data = self.exchange_code_for_token(code)
            access_token = token_data.get('access_token')

            if not access_token:
                raise CustomAPIException(detail="Failed to retrieve access token from Discord", status_code=status.HTTP_400_BAD_REQUEST)

            # Fetch the user's Discord profile
            profile_data = self.get_user_profile(access_token)

            # Save or update the user's SocialUser model
            social_user, created = SocialUser.objects.get_or_create(user_id=request.user)
            social_user.discord_access_token = access_token
            social_user.discord_id = profile_data.get('id')  # Get the user's Discord ID
            social_user.save()

            return custom_response(status_code=status.HTTP_200_OK, message="Discord account connected successfully", data={"discord_id": social_user.discord_id})

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()

class DiscordRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Redirect user to Discord OAuth URL with all required scopes
        discord_login_url = (
            "https://discord.com/api/oauth2/authorize?"
            f"client_id={settings.DISCORD_CLIENT_ID}&"
            f"redirect_uri={settings.DISCORD_REDIRECT_URI}&"
            f"response_type=code&"
            f"scope="
            "identify email guilds connections "
            "activities.read activities.write rpc "
            "webhook.incoming bot"
        )
        return redirect(discord_login_url)


class TumblrLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def exchange_code_for_token(self, code):
        """Function to exchange code for an access token."""
        token_url = 'https://api.tumblr.com/v2/oauth2/token'
        data = {
            'client_id': settings.TUMBLR_CLIENT_ID,
            'client_secret': settings.TUMBLR_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.TUMBLR_REDIRECT_URI,
        }
        response = requests.post(token_url, data=data)
        return response.json()

    def get_user_blogs(self, access_token):
        """Fetch the authenticated user's blogs."""
        user_info_url = 'https://api.tumblr.com/v2/user/info'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(user_info_url, headers=headers)
        return response.json()

    def get_user_profile(self, access_token, blog_identifier):
        """Fetch the user's Tumblr profile."""
        profile_url = f'https://api.tumblr.com/v2/blog/{blog_identifier}/info'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(profile_url, headers=headers)
        return response.json()

    def post(self, request, *args, **kwargs):
        code = request.data.get('code')
        if not code:
            return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Authorization code is required")

        try:
            # Exchange the code for an access token
            token_data = self.exchange_code_for_token(code)
            access_token = token_data.get('access_token')

            if not access_token:
                raise CustomAPIException(detail="Failed to retrieve access token from Tumblr", status_code=status.HTTP_400_BAD_REQUEST)

            # Fetch the user's blogs
            user_blogs = self.get_user_blogs(access_token)
            blog_identifier = user_blogs['response']['blogs'][0]['name']  # Get the first blog's name

            # Fetch the user's Tumblr profile
            profile_data = self.get_user_profile(access_token, blog_identifier)

            # Save or update the user's SocialUser model
            social_user, created = SocialUser.objects.get_or_create(user_id=request.user)
            social_user.tumblr_access_token = access_token
            social_user.tumblr_id = profile_data['response']['blog']['name']  # Get the user's Tumblr ID
            social_user.save()

            return custom_response(status_code=status.HTTP_200_OK, message="Tumblr account connected successfully", data={"tumblr_id": social_user.tumblr_id})

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()

class TumblrRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Redirect user to Tumblr OAuth URL with required scopes
        tumblr_login_url = (
            "https://api.tumblr.com/v2/oauth2/authorize?"
            f"client_id={settings.TUMBLR_CLIENT_ID}&"
            f"redirect_uri={settings.TUMBLR_REDIRECT_URI}&"
            f"response_type=code&"
            f"scope=read,write"  # Adjust scopes as needed
        )
        return redirect(tumblr_login_url)
    
    
class MediumLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def exchange_code_for_token(self, code):
        """Function to exchange code for an access token."""
        token_url = 'https://api.medium.com/v1/tokens'
        data = {
            'client_id': settings.MEDIUM_CLIENT_ID,
            'client_secret': settings.MEDIUM_CLIENT_SECRET,
            'code': code,
            'redirect_uri': settings.MEDIUM_REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        response = requests.post(token_url, data=data)
        return response.json()

    def get_user_profile(self, access_token):
        """Fetch the user's Medium profile."""
        profile_url = 'https://api.medium.com/v1/me'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(profile_url, headers=headers)
        return response.json()

    def post(self, request, *args, **kwargs):
        code = request.data.get('code')
        if not code:
            return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Authorization code is required")

        try:
            # Exchange the code for an access token
            token_data = self.exchange_code_for_token(code)
            access_token = token_data.get('access_token')

            if not access_token:
                raise CustomAPIException(detail="Failed to retrieve access token from Medium", status_code=status.HTTP_400_BAD_REQUEST)

            # Fetch the user's Medium profile
            profile_data = self.get_user_profile(access_token)

            # Save or update the user's SocialUser model
            social_user, created = SocialUser.objects.get_or_create(user_id=request.user)
            social_user.medium_access_token = access_token
            social_user.medium_id = profile_data.get('id')  # Get the user's Medium ID
            social_user.save()

            return custom_response(status_code=status.HTTP_200_OK, message="Medium account connected successfully", data={"medium_id": social_user.medium_id})

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()
        
        
class MediumRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Redirect user to Medium OAuth URL with all required scopes
        medium_login_url = (
            "https://medium.com/m/oauth/authorize?"
            f"client_id={settings.MEDIUM_CLIENT_ID}&"
            f"redirect_uri={settings.MEDIUM_REDIRECT_URI}&"
            f"response_type=code&"
            f"scope=basicProfile,publishPost,listPublications,writePublication,readAll,writeAll"  # All available scopes
        )
        return redirect(medium_login_url)



class TelegramLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def exchange_code_for_token(self, code):
        """Function to exchange code for an access token."""
        token_url = 'https://api.telegram.org/bot{}/getToken'.format(settings.TELEGRAM_BOT_ID)
        data = {
            'client_id': settings.TELEGRAM_CLIENT_ID,
            'client_secret': settings.TELEGRAM_CLIENT_SECRET,
            'code': code,
            'redirect_uri': settings.TELEGRAM_REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        response = requests.post(token_url, data=data)
        return response.json()

    def get_user_profile(self, access_token):
        """Fetch the user's Telegram profile."""
        profile_url = 'https://api.telegram.org/bot{}/getMe'.format(settings.TELEGRAM_BOT_ID)
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(profile_url, headers=headers)
        return response.json()

    def post(self, request, *args, **kwargs):
        code = request.data.get('code')
        if not code:
            return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Authorization code is required")

        try:
            # Exchange the code for an access token
            token_data = self.exchange_code_for_token(code)
            access_token = token_data.get('access_token')

            if not access_token:
                raise CustomAPIException(detail="Failed to retrieve access token from Telegram", status_code=status.HTTP_400_BAD_REQUEST)

            # Fetch the user's Telegram profile
            profile_data = self.get_user_profile(access_token)

            # Save or update the user's SocialUser model
            social_user, created = SocialUser.objects.get_or_create(user_id=request.user)
            social_user.telegram_access_token = access_token
            social_user.telegram_id = profile_data.get('id')  # Get the user's Telegram ID
            social_user.save()

            return custom_response(status_code=status.HTTP_200_OK, message="Telegram account connected successfully", data={"telegram_id": social_user.telegram_id})

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()
        
        
class TelegramRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Redirect user to Telegram OAuth URL with required scopes
        telegram_login_url = (
            "https://oauth.telegram.org/auth?"
            f"bot_id={settings.TELEGRAM_BOT_ID}&"
            f"redirect_uri={settings.TELEGRAM_REDIRECT_URI}&"
            f"response_type=code&"
            f"scope=read,write,send_messages,read_user_profile,manage_bot,join_groups,add_admin"
        )
        return redirect(telegram_login_url) 


        

class WhatsAppLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def exchange_code_for_token(self, code):
        """Function to exchange code for an access token."""
        token_url = 'https://api.whatsapp.com/v1/auth/token'  # Example URL; adjust accordingly
        data = {
            'client_id': settings.WHATSAPP_CLIENT_ID,
            'client_secret': settings.WHATSAPP_CLIENT_SECRET,
            'code': code,
            'redirect_uri': settings.WHATSAPP_REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        response = requests.post(token_url, data=data)
        return response.json()

    def get_user_profile(self, access_token):
        """Fetch the user's WhatsApp profile."""
        profile_url = 'https://api.whatsapp.com/v1/me'  # Example URL; adjust accordingly
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(profile_url, headers=headers)
        return response.json()

    def post(self, request, *args, **kwargs):
        code = request.data.get('code')
        if not code:
            return custom_response(status_code=status.HTTP_400_BAD_REQUEST, message="Authorization code is required")

        try:
            # Exchange the code for an access token
            token_data = self.exchange_code_for_token(code)
            access_token = token_data.get('access_token')

            if not access_token:
                raise CustomAPIException(detail="Failed to retrieve access token from WhatsApp", status_code=status.HTTP_400_BAD_REQUEST)

            # Fetch the user's WhatsApp profile
            profile_data = self.get_user_profile(access_token)

            # Save or update the user's SocialUser model
            social_user, created = SocialUser.objects.get_or_create(user_id=request.user)
            social_user.whatsapp_access_token = access_token
            social_user.whatsapp_id = profile_data.get('id')  # Get the user's WhatsApp ID
            social_user.save()

            return custom_response(status_code=status.HTTP_200_OK, message="WhatsApp account connected successfully", data={"whatsapp_id": social_user.whatsapp_id})

        except Exception as e:
            return CustomAPIException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST).get_full_details()


class WhatsAppRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Redirect user to WhatsApp OAuth URL with required scopes
        whatsapp_login_url = (
            "https://api.whatsapp.com/v1/auth?"
            f"client_id={settings.WHATSAPP_CLIENT_ID}&"
            f"redirect_uri={settings.WHATSAPP_REDIRECT_URI}&"
            f"response_type=code&"
            f"scope=read,write,send_messages,manage_profile,message_history,contact_list,group_management"
        )
        return redirect(whatsapp_login_url)
