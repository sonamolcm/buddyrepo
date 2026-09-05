# pyright: reportMissingImports=false
# pyrefly: ignore [missing-import]
from django.urls import path  # type: ignore
# pyrefly: ignore [missing-import]
from rest_framework_simplejwt.views import TokenRefreshView  # type: ignore

# pyrefly: ignore [missing-import]
from .views import (  # type: ignore
    # Caller Signup Flow
    CallerSignupSendOTPView,
    CallerSignupVerifyOTPView,
    CallerSignupCompleteProfileView,
    # Caller Login Flow
    CallerLoginSendOTPView,
    CallerLoginVerifyOTPView,
    # Listener Login Flow
    ListenerLoginView,
    # Logout Flow
    LogoutView,
    # Account Deletion Flow
    DeleteAccountView,
    # Caller Profile
    ProfileView,
    # Metadata Dropdowns
    LanguageListView,
    InterestListView,
    CategoryListCreateView,
    CategoryDetailView,
    # Web Simulator & Web Auth Compatibility Views
    WebSendOTPView,
    WebVerifyOTPView,
    WebAboutYouView,
    WebLoginView,
    # Admin Listener Management APIs
    AdminCreateListenerView,
    AdminListenerListView,
    AdminDeleteListenerView,
    # Complete Caller & Listener CRUD
    CallerListCreateView,
    CallerDetailView,
    CallerDeleteView,
    CallerDeleteDirectView,
    ListenerListCreateView,
    ListenerDetailView,
    ListenerDeleteView,
    ListenerDeleteDirectView,
)

urlpatterns = [
    # ==========================================
    # 0. WEB SIMULATOR & COMPATIBILITY ROUTES
    # ==========================================
    path('auth/send-otp/', WebSendOTPView.as_view(), name='web-send-otp'),
    path('auth/verify-otp/', WebVerifyOTPView.as_view(), name='web-verify-otp'),
    path('auth/about-you/', WebAboutYouView.as_view(), name='web-about-you'),
    path('auth/login/', WebLoginView.as_view(), name='web-login'),

    # ==========================================
    # 1. CALLER SIGNUP FLOW
    # ==========================================
    path('auth/caller/signup/send-otp/', CallerSignupSendOTPView.as_view(), name='caller-signup-send-otp'),
    path('auth/caller/signup/verify-otp/', CallerSignupVerifyOTPView.as_view(), name='caller-signup-verify-otp'),
    path('auth/caller/signup/complete-profile/', CallerSignupCompleteProfileView.as_view(), name='caller-signup-complete-profile'),

    # ==========================================
    # 2. CALLER LOGIN FLOW
    # ==========================================
    path('auth/caller/login/send-otp/', CallerLoginSendOTPView.as_view(), name='caller-login-send-otp'),
    path('auth/caller/login/verify-otp/', CallerLoginVerifyOTPView.as_view(), name='caller-login-verify-otp'),

    # ==========================================
    # 3. LISTENER LOGIN FLOW
    # ==========================================
    path('auth/listener/login/', ListenerLoginView.as_view(), name='listener-login'),
    path('auth/listener/login', ListenerLoginView.as_view(), name='listener-login-noslash'),
    path('listener/login/', ListenerLoginView.as_view(), name='listener-login-short'),
    path('listener/login', ListenerLoginView.as_view(), name='listener-login-short-noslash'),

    # ==========================================
    # 3.1 LOGOUT FLOW
    # ==========================================
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/logout', LogoutView.as_view(), name='auth-logout-noslash'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('logout', LogoutView.as_view(), name='logout-noslash'),

    # ==========================================
    # 3.2 DELETE ACCOUNT FLOW
    # ==========================================
    path('auth/delete-account/', DeleteAccountView.as_view(), name='auth-delete-account'),
    path('auth/delete-account', DeleteAccountView.as_view(), name='auth-delete-account-noslash'),
    path('delete-account/', DeleteAccountView.as_view(), name='delete-account'),
    path('delete-account', DeleteAccountView.as_view(), name='delete-account-noslash'),

    # ==========================================
    # 4. JWT TOKEN REFRESH
    # ==========================================
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/token/refresh', TokenRefreshView.as_view(), name='token-refresh-noslash'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh-short'),
    path('token/refresh', TokenRefreshView.as_view(), name='token-refresh-short-noslash'),

    # ==========================================
    # 5. CALLER PROFILE
    # ==========================================
    path('profile/', ProfileView.as_view(), name='profile-detail'),
    path('caller/profile/', ProfileView.as_view(), name='caller-profile'),
    path('profile/delete/', DeleteAccountView.as_view(), name='profile-delete'),
    path('profile/delete', DeleteAccountView.as_view()),
    path('caller/profile/delete/', DeleteAccountView.as_view()),
    path('caller/profile/delete', DeleteAccountView.as_view()),

    # ==========================================
    # 6. METADATA DROPDOWNS (LANGUAGES, INTERESTS & CATEGORIES)
    # ==========================================
    path('languages/', LanguageListView.as_view(), name='language-list'),
    path('interests/', InterestListView.as_view(), name='interest-list'),

    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories', CategoryListCreateView.as_view()),
    path('categories/<int:id>/', CategoryDetailView.as_view(), name='category-detail'),
    path('categories/<int:id>', CategoryDetailView.as_view()),


    # ==========================================
    # 7. ADMIN LISTENER MANAGEMENT API (LEGACY ALIASES)
    # ==========================================
    path('admin/listeners/create/', AdminCreateListenerView.as_view(), name='api-admin-create-listener'),
    path('admin/listeners/create', AdminCreateListenerView.as_view()),
    path('admin/listeners/delete/', AdminDeleteListenerView.as_view(), name='api-admin-delete-listener'),
    path('admin/listeners/delete', AdminDeleteListenerView.as_view()),
    path('admin/listeners/', AdminListenerListView.as_view(), name='api-admin-list-listeners'),
    path('admin/listeners', AdminListenerListView.as_view()),

    # ==========================================
    # 8. COMPLETE CRUD FOR CALLERS
    # ==========================================
    path('callers/', CallerListCreateView.as_view(), name='caller-list-create'),
    path('callers', CallerListCreateView.as_view()),
    path('callers/<int:user_id>/delete/', CallerDeleteView.as_view(), name='caller-delete'),
    path('callers/<int:user_id>/delete', CallerDeleteView.as_view()),
    path('callers/<str:identifier>/', CallerDetailView.as_view(), name='caller-detail'),
    path('callers/<str:identifier>', CallerDetailView.as_view()),
    path('callers/<str:identifier>/delete/', CallerDeleteDirectView.as_view(), name='caller-detail-delete'),
    path('callers/<str:identifier>/delete', CallerDeleteDirectView.as_view()),

    # ==========================================
    # 9. COMPLETE CRUD FOR LISTENERS
    # ==========================================
    path('listeners/', ListenerListCreateView.as_view(), name='listener-list-create'),
    path('listeners', ListenerListCreateView.as_view()),
    path('listeners/<int:user_id>/delete/', ListenerDeleteView.as_view(), name='listener-delete'),
    path('listeners/<int:user_id>/delete', ListenerDeleteView.as_view()),
    path('listeners/create/', ListenerListCreateView.as_view()),
    path('listeners/create', ListenerListCreateView.as_view()),
    path('listeners/delete/', ListenerListCreateView.as_view()),
    path('listeners/delete', ListenerListCreateView.as_view()),
    path('listeners/<str:identifier>/', ListenerDetailView.as_view(), name='listener-detail'),
    path('listeners/<str:identifier>', ListenerDetailView.as_view()),
    path('listeners/<str:identifier>/delete/', ListenerDeleteDirectView.as_view(), name='listener-detail-delete'),
    path('listeners/<str:identifier>/delete', ListenerDeleteDirectView.as_view()),
]
