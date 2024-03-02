from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.staticfiles.urls import static

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Tawq API Documentation",
        default_version='v1',
        description="Tawq is a cutting-edge platform that meets the needs of content creators,\n tutors, scholars and basically anyone into any form of content creation.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="lets@tawq.io"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # CUSTOM URLS
    path('api/v1/authorization/',
         include('authorization.urls', namespace='authorization')),
    path('api/v1/subscription/',
         include('subscription.urls', namespace='subscription')),
     path('api/v1/post.urls/', 
          include(('post.urls', 'post'), namespace='post-section')),


    # APPLICATION DOCUMENTATION
    path('api/v1/swagger-docs/', schema_view.with_ui('swagger',
         cache_timeout=0), name='schema-swagger-ui'),
    path('api/v1/redoc/', schema_view.with_ui('redoc',
         cache_timeout=0), name='schema-redoc'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


admin.site.site_header = 'Tawq Tools'
admin.site.index_title = 'Administrators Dashboard'
admin.site.site_title = 'Control Panel'
