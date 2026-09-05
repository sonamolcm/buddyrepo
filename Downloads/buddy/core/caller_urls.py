# pyright: reportMissingImports=false
# pyrefly: ignore [missing-import]
from django.urls import path  # type: ignore
# pyrefly: ignore [missing-import]
from .caller_views import (
    caller_signup_view,
    caller_signup_otp_view,
    caller_login_view,
    caller_login_otp_view,
    caller_profile_setup_view,
    caller_home_view,
    caller_profile_view,
)

urlpatterns = [
    path('signup/', caller_signup_view, name='caller-web-signup'),
    path('signup/otp/', caller_signup_otp_view, name='caller-web-signup-otp'),
    path('login/', caller_login_view, name='caller-web-login'),
    path('login/otp/', caller_login_otp_view, name='caller-web-login-otp'),
    path('profile-setup/', caller_profile_setup_view, name='caller-web-profile-setup'),
    path('home/', caller_home_view, name='caller-web-home'),
    path('profile/', caller_profile_view, name='caller-web-profile'),
]
