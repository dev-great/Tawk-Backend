from django.urls import path, re_path, include
from authorization.views import (
    ChangePasswordView, DeleteAccount, GoogleAPIView, LoginView, Logout,
    ReferralHistoryView, ReferralView, RegisterView, TokenRefreshView,
    TokenVerifyView, UserProfileView,EmailVerificationView, EmailOTPAuthentication
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('register/', RegisterView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('email/verify/', EmailVerificationView.as_view(), name='email_verify'),
    path('email/otp/resend/', EmailOTPAuthentication.as_view(), name='email_otp'),
    path('user_profile/', UserProfileView.as_view()),
    path('logout/', Logout.as_view()),
    path('changepassword/', ChangePasswordView.as_view()),
    path('delete_user/', DeleteAccount.as_view()),
    path('password_reset/', include('django_rest_passwordreset.urls')),
    path('referral_code/', ReferralView.as_view()),
    path('referral_history/', ReferralHistoryView.as_view()),
    re_path(r'^social/', include('drf_social_oauth2.urls', namespace='social')),
    path('google-verify-api/', GoogleAPIView.as_view(), name='google_verify'),
]
