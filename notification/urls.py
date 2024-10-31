from django.urls import path
from .views import SpecificUserNotificationView

app_name = 'notification'

urlpatterns = [
    path('user_notifications/', SpecificUserNotificationView.as_view()),

]
