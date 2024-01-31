from django.urls import path
from .views import SubscriptionPlanListView, SubscriptionView, SubscriptionCheckAPIView

app_name = 'core'

urlpatterns = [
    path('subscription_plans/', SubscriptionPlanListView.as_view()),
    path('subscriptions/', SubscriptionView.as_view()),
    path('subscription/check/', SubscriptionCheckAPIView.as_view()),

]
