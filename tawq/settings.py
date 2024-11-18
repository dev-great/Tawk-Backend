from datetime import timedelta
import os
from dotenv import load_dotenv
from pathlib import Path
import dj_database_url
import cloudinary
import cloudinary.uploader
import cloudinary.api

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-295#lq+1oh6yv$@&dn^c8d)8tpwma-8xvhvlnup3)u_5@1r!r='
DEBUG = False

ALLOWED_HOSTS = ['*']


SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SESSION_COOKIE_HTTPONLY = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  
    "https://tawk-backend-46a670866b8a.herokuapp.com", 
]
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# Application definition
INSTALLED_APPS = [
    # Django's built-in applications
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party applications
    'drf_yasg',
    'corsheaders',
    'cloudinary',
    'social_django',
    'rest_framework',
    'oauth2_provider',
    'drf_social_oauth2',
    "drf_standardized_errors",
    'rest_framework_simplejwt',
    'django_rest_passwordreset',
    'rest_framework_simplejwt.token_blacklist',


    # Custom applications
    'authorization',
    'subscription',
    'notification',
    'analytic',
    'scheduling',
    'social_inbox',
    'talk_ai',
    'collaboration',
    'white_label',
    'utils',
    'wallet',
    'post',
    'linked_account',
    'webhook',
]

SITE_ID = 1

#SOCIAL_AUTH_JSONFIELD_ENABLED = True
#ACTIVATE_JWT = True
DRFSO2_URL_NAMESPACE = "social"


DRF_STANDARDIZED_ERRORS = {
    "EXCEPTION_FORMATTER_CLASS": 'utils.custom_exception.MyExceptionFormatter',
}
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': "drf_standardized_errors.handler.exception_handler",
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'drf_social_oauth2.authentication.SocialAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
    'rest_framework.permissions.IsAuthenticated',
    ],
}

AUTHENTICATION_BACKENDS = (
    # Google OAuth2
    'social_core.backends.google.GoogleOAuth2',

    # Facebook OAuth2
    'social_core.backends.facebook.FacebookAppOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',

    # django-rest-framework-social-oauth2
    'drf_social_oauth2.backends.DjangoOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)


SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.create_user',  
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'authorization.views.ensure_email_and_provider', 
)


SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'DEFAULT_FIELD_INSPECTORS': [
        'drf_yasg.inspectors.CamelCaseJSONFilter',
        'drf_yasg.inspectors.InlineSerializerInspector',
        'drf_yasg.inspectors.RelatedFieldInspector',
        'drf_yasg.inspectors.ChoiceFieldInspector',
        'drf_yasg.inspectors.FileFieldInspector',
        'drf_yasg.inspectors.DictFieldInspector',
        'drf_yasg.inspectors.SimpleFieldInspector',
        'drf_yasg.inspectors.StringDefaultFieldInspector',
    ],
    'SECURITY_DEFINITIONS': {
        'Token': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        },
     
    }
}


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # 'django_tenants.middleware.main.TenantMainMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'tawq.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',

            ],
        },
    },
]

WSGI_APPLICATION = 'tawq.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# DATABASE_ROUTERS = (
#     'django_tenants.routers.TenantSyncRouter',
# )

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


FLW_PUBLIC_KEY = os.getenv("FLW_PUBLIC_KEY")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
FLW_ENCRIPTION_KEY = os.getenv("FLW_ENCRIPTION_KEY")
FLW_WEBHOOK_SECRET = "a3c1d5b6f7e8d9a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8g9h0i1j2k3l4m5"


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'authorization.CustomUser'


ACCOUNT_EMAIL_VERIFICATION = "none"
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.mail.yahoo.com'
EMAIL_PORT = 465
EMAIL_HOST_USER = 'unique_mind16@yahoo.com'
EMAIL_HOST_PASSWORD = 'xqywwridnwrxgjwr'
EMAIL_USE_SSL = True
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER



DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG = {
    "CLASS": "django_rest_passwordreset.tokens.RandomStringTokenGenerator",
    "OPTIONS": {
        "min_length": 6,
        "max_length": 6,
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'social_core': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}




STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


CLOUDINARY_URL = 'cloudinary://387625877385614:zZrsexxvBVryHpiyJ6DG2tZrl5Y@dbrvleydy'

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dbrvleydy',
    'API_KEY': '387625877385614',
    'API_SECRET': 'zZrsexxvBVryHpiyJ6DG2tZrl5Y',
}

cloudinary.config(
    cloud_name='dbrvleydy',
    api_key='387625877385614',
    api_secret='zZrsexxvBVryHpiyJ6DG2tZrl5Y'
)


# Media files
MEDIA_URL = '/media/'
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'


# If file isn’t necessary, WhiteNoise ignore missing files
WHITENOISE_ALLOW_ALL_ORIGINS = True


# Google configuration
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = "201572501772-phe7fgp08l0tdpqvmvmbe37757j7v3dp.apps.googleusercontent.com",
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = "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",
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = 'http://localhost:8000/api/v1/authorization/social/complete/google/'
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]

SOCIAL_AUTH_APPLE_ID_CLIENT = 'com.yinoral.app.us-service'
SOCIAL_AUTH_APPLE_ID_TEAM = 'CHYWU6M75M'
SOCIAL_AUTH_APPLE_ID_KEY = 'ZKZBVHBCUL'
SOCIAL_AUTH_APPLE_ID_SECRET = """ 
-----BEGIN PRIVATE KEY-----
MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQgZY30xPdpYvUNP/h+
5vAe28ft2aPxZey7etGtyIIbsh2gCgYIKoZIzj0DAQehRANCAATDESHtpSGluAuU
06Xv/BpCfUjLwCNbuadD/VAz5haHWDH4ww2vLkYo3sKsz9prw9ZOdenkxei1bnfz
abq1WSAk
-----END PRIVATE KEY-----
"""


# ALL SOCIAL INTEGRATIONS


# Facebook configuration
SOCIAL_AUTH_FACEBOOK_KEY = '525916073144369'
SOCIAL_AUTH_FACEBOOK_SECRET = '0570be6120817f26a1db6458261bfcc4'
SOCIAL_AUTH_FACEBOOK_SCOPE = [
    'email',                        # Basic permission
    'pages_show_list',               # Access pages the user manages
    'pages_manage_posts',            # Post as the page
    'pages_read_engagement',         # Read page insights
    'pages_manage_engagement',       # Like and comment on behalf of the page
    'public_profile',                # Basic user profile info
    'publish_to_groups',             # Publish to groups the user manages
    'user_posts'                     # Access the user's posts
]
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id,name,email'
}

# Facebook App credentials
FACEBOOK_APP_ID = 'your_facebook_app_id'
FACEBOOK_APP_SECRET = 'your_facebook_app_secret'
FACEBOOK_REDIRECT_URI = 'https://your-redirect-uri.com/facebook/callback'  

# Google configuration
GOOGLE_CLIENT_ID = 'your_google_client_id'
GOOGLE_CLIENT_SECRET = 'your_google_client_secret'
GOOGLE_REDIRECT_URI = 'your_redirect_uri'  

INSTAGRAM_CLIENT_ID = 'your_instagram_client_id'
INSTAGRAM_CLIENT_SECRET = 'your_instagram_client_secret'
INSTAGRAM_REDIRECT_URI = 'your_redirect_uri' 

SLACK_CLIENT_ID = '<your-slack-client-id>'
SLACK_CLIENT_SECRET = '<your-slack-client-secret>'
SLACK_REDIRECT_URI = '<your-slack-redirect-uri>'



SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,

    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,

    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,

    "AUTH_HEADER_TYPES": ("bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

    "JTI_CLAIM": "jti",

    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),

    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}



if 'DATABASE_URL' in os.environ:
    import dj_database_url
    DATABASES = {'default': dj_database_url.config()}
