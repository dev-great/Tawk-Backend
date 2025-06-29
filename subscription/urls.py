from django.urls import path
from .views import SubscriptionPlanListView, InitiateSubscriptionView, ValidateSubscriptionView,CreateFreePlanView

app_name = 'subscription'

urlpatterns = [
    path('subscription_plans/', SubscriptionPlanListView.as_view()),
    path('subscribe/', InitiateSubscriptionView.as_view()),
    path('verify/', ValidateSubscriptionView.as_view()),
    path('free-plan/', CreateFreePlanView.as_view()),

]
