from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.staticfiles.urls import static
from tawq.settings import STATIC_ROOT, STATIC_URL
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Tawk API Documentation",
        default_version='v1',
        description="TawqKis a cutting-edge platform that meets the needs of content creators,\n individuals, businesses and basically anyone into any form of content creation.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="lets@tawkglobal.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # CUSTOM URLS
    path('api/v1/authorization/', include('authorization.urls')),
    path('api/v1/subscription/', include('subscription.urls')),
    path('api/v1/post/', include('post.urls')),
    path('api/v1/socials/', include('linked_account.urls')),
    path('api/v1/webhook/', include('webhook.urls')),

]


# APPLICATION DOCUMENTATION
urlpatterns += [
    path('api/v1/docs/', schema_view.with_ui('swagger',
         cache_timeout=0), name='schema-swagger-ui'),
]

urlpatterns += static(STATIC_URL, document_root=STATIC_ROOT)


admin.site.site_header = 'Tawk Tools'
admin.site.index_title = 'Administrators Dashboard'
admin.site.site_title = 'Control Panel'
