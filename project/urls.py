"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# pyrefly: ignore [missing-import]
from django.contrib import admin
# pyrefly: ignore [missing-import]
from django.urls import path, include
# pyrefly: ignore [missing-import]
from django.conf import settings
# pyrefly: ignore [missing-import]
from django.conf.urls.static import static

from core.views import (
    ListenerLoginView,
    CallerLogoutView,
    ListenerLogoutView,
    LogoutView,
    DeleteAccountView,
    AdminCreateListenerView,
    AdminListenerListView,
    AdminDeleteListenerView,
    CallerListCreateView,
    CallerDetailView,
    CallerDeleteView,
    CallerDeleteDirectView,
    ListenerListCreateView,
    ListenerDetailView,
    ListenerDeleteView,
    ListenerDeleteDirectView,
    TermsAndConditionsView,
    PrivacyPolicyView,
    HelplineView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # ==========================================
    # CALLER CRUD ENDPOINTS
    # ==========================================
    path('api/callers/', CallerListCreateView.as_view(), name='api-direct-callers'),
    path('api/callers', CallerListCreateView.as_view()),
    path('callers/', CallerListCreateView.as_view()),
    path('callers', CallerListCreateView.as_view()),
    path('api/callers/<int:user_id>/delete/', CallerDeleteView.as_view(), name='api-caller-delete'),
    path('api/callers/<int:user_id>/delete', CallerDeleteView.as_view()),
    path('callers/<int:user_id>/delete/', CallerDeleteView.as_view()),
    path('callers/<int:user_id>/delete', CallerDeleteView.as_view()),
    path('api/callers/<str:identifier>/', CallerDetailView.as_view()),
    path('api/callers/<str:identifier>', CallerDetailView.as_view()),
    path('callers/<str:identifier>/', CallerDetailView.as_view()),
    path('callers/<str:identifier>', CallerDetailView.as_view()),
    path('api/callers/<str:identifier>/delete/', CallerDeleteDirectView.as_view()),
    path('api/callers/<str:identifier>/delete', CallerDeleteDirectView.as_view()),
    path('callers/<str:identifier>/delete/', CallerDeleteDirectView.as_view()),
    path('callers/<str:identifier>/delete', CallerDeleteDirectView.as_view()),

    # ==========================================
    # LISTENER CRUD ENDPOINTS (ALL VARIATIONS)
    # ==========================================
    path('api/listeners/', ListenerListCreateView.as_view(), name='api-direct-listeners'),
    path('api/listeners', ListenerListCreateView.as_view()),
    path('listeners/', ListenerListCreateView.as_view()),
    path('listeners', ListenerListCreateView.as_view()),
    path('api/listeners/<int:user_id>/delete/', ListenerDeleteView.as_view(), name='api-listener-delete'),
    path('api/listeners/<int:user_id>/delete', ListenerDeleteView.as_view()),
    path('listeners/<int:user_id>/delete/', ListenerDeleteView.as_view()),
    path('listeners/<int:user_id>/delete', ListenerDeleteView.as_view()),
    path('api/listeners/<str:identifier>/', ListenerDetailView.as_view()),
    path('api/listeners/<str:identifier>', ListenerDetailView.as_view()),
    path('listeners/<str:identifier>/', ListenerDetailView.as_view()),
    path('listeners/<str:identifier>', ListenerDetailView.as_view()),
    path('api/listeners/<str:identifier>/delete/', ListenerDeleteDirectView.as_view()),
    path('api/listeners/<str:identifier>/delete', ListenerDeleteDirectView.as_view()),
    path('listeners/<str:identifier>/delete/', ListenerDeleteDirectView.as_view()),
    path('listeners/<str:identifier>/delete', ListenerDeleteDirectView.as_view()),
    path('api/listeners/create/', AdminCreateListenerView.as_view()),
    path('api/listeners/create', AdminCreateListenerView.as_view()),
    path('listeners/create/', AdminCreateListenerView.as_view()),
    path('listeners/create', AdminCreateListenerView.as_view()),
    path('api/listeners/delete/', AdminDeleteListenerView.as_view()),
    path('api/listeners/delete', AdminDeleteListenerView.as_view()),
    path('listeners/delete/', AdminDeleteListenerView.as_view()),
    path('listeners/delete', AdminDeleteListenerView.as_view()),
    path('api/listeners/delete/<str:identifier>/', AdminDeleteListenerView.as_view()),
    path('api/listeners/delete/<str:identifier>', AdminDeleteListenerView.as_view()),
    path('listeners/delete/<str:identifier>/', AdminDeleteListenerView.as_view()),
    path('listeners/delete/<str:identifier>', AdminDeleteListenerView.as_view()),

    # Admin aliases
    path('api/admin/listeners/', AdminListenerListView.as_view()),
    path('api/admin/listeners', AdminListenerListView.as_view()),
    path('admin/listeners/', AdminListenerListView.as_view()),
    path('admin/listeners', AdminListenerListView.as_view()),
    path('api/admin/listeners/create/', AdminCreateListenerView.as_view()),
    path('api/admin/listeners/create', AdminCreateListenerView.as_view()),
    path('admin/listeners/create/', AdminCreateListenerView.as_view()),
    path('admin/listeners/create', AdminCreateListenerView.as_view()),
    path('api/admin/listeners/delete/', AdminDeleteListenerView.as_view()),
    path('api/admin/listeners/delete', AdminDeleteListenerView.as_view()),
    path('admin/listeners/delete/', AdminDeleteListenerView.as_view()),
    path('admin/listeners/delete', AdminDeleteListenerView.as_view()),
    path('api/admin/listeners/delete/<str:identifier>/', AdminDeleteListenerView.as_view()),
    path('api/admin/listeners/delete/<str:identifier>', AdminDeleteListenerView.as_view()),
    path('admin/listeners/delete/<str:identifier>/', AdminDeleteListenerView.as_view()),
    path('admin/listeners/delete/<str:identifier>', AdminDeleteListenerView.as_view()),
    path('api/admin/listeners/<str:identifier>/', ListenerDetailView.as_view()),
    path('api/admin/listeners/<str:identifier>', ListenerDetailView.as_view()),
    path('admin/listeners/<str:identifier>/', ListenerDetailView.as_view()),
    path('admin/listeners/<str:identifier>', ListenerDetailView.as_view()),


    # Direct Listener & General Login endpoints (handles all URL variations)
    path('api/auth/listener/login/', ListenerLoginView.as_view(), name='api-auth-listener-login'),
    path('api/auth/listener/login', ListenerLoginView.as_view()),
    path('auth/listener/login/', ListenerLoginView.as_view()),
    path('auth/listener/login', ListenerLoginView.as_view()),
    path('api/listener/login/', ListenerLoginView.as_view()),
    path('api/listener/login', ListenerLoginView.as_view()),
    path('listener/login/', ListenerLoginView.as_view()),
    path('listener/login', ListenerLoginView.as_view()),

    # General login aliases
    path('api/auth/login/', ListenerLoginView.as_view()),
    path('api/auth/login', ListenerLoginView.as_view()),
    path('auth/login/', ListenerLoginView.as_view()),
    path('auth/login', ListenerLoginView.as_view()),
    path('api/login/', ListenerLoginView.as_view()),
    path('api/login', ListenerLoginView.as_view()),
    path('login/', ListenerLoginView.as_view()),
    path('login', ListenerLoginView.as_view()),

    # Caller logout aliases
    path('api/auth/caller/logout/', CallerLogoutView.as_view(), name='api-auth-caller-logout'),
    path('api/auth/caller/logout', CallerLogoutView.as_view()),
    path('auth/caller/logout/', CallerLogoutView.as_view()),
    path('auth/caller/logout', CallerLogoutView.as_view()),
    path('api/caller/logout/', CallerLogoutView.as_view()),
    path('api/caller/logout', CallerLogoutView.as_view()),
    path('caller/logout/', CallerLogoutView.as_view()),
    path('caller/logout', CallerLogoutView.as_view()),

    # Listener logout aliases
    path('api/auth/listener/logout/', ListenerLogoutView.as_view(), name='api-auth-listener-logout'),
    path('api/auth/listener/logout', ListenerLogoutView.as_view()),
    path('auth/listener/logout/', ListenerLogoutView.as_view()),
    path('auth/listener/logout', ListenerLogoutView.as_view()),
    path('api/listener/logout/', ListenerLogoutView.as_view()),
    path('api/listener/logout', ListenerLogoutView.as_view()),
    path('listener/logout/', ListenerLogoutView.as_view()),
    path('listener/logout', ListenerLogoutView.as_view()),

    # General logout aliases
    path('api/auth/logout/', LogoutView.as_view(), name='api-auth-logout'),
    path('api/auth/logout', LogoutView.as_view()),
    path('auth/logout/', LogoutView.as_view()),
    path('auth/logout', LogoutView.as_view()),
    path('api/logout/', LogoutView.as_view()),
    path('api/logout', LogoutView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('logout', LogoutView.as_view()),

    # General delete account aliases
    path('api/auth/delete-account/', DeleteAccountView.as_view(), name='api-auth-delete-account'),
    path('api/auth/delete-account', DeleteAccountView.as_view()),
    path('auth/delete-account/', DeleteAccountView.as_view()),
    path('auth/delete-account', DeleteAccountView.as_view()),
    path('api/delete-account/', DeleteAccountView.as_view()),
    path('api/delete-account', DeleteAccountView.as_view()),
    path('delete-account/', DeleteAccountView.as_view()),
    path('delete-account', DeleteAccountView.as_view()),
    path('api/profile/delete/', DeleteAccountView.as_view()),
    path('api/profile/delete', DeleteAccountView.as_view()),
    path('profile/delete/', DeleteAccountView.as_view()),
    path('profile/delete', DeleteAccountView.as_view()),

    # ==========================================
    # LEGAL & HELPLINE ROUTES
    # ==========================================
    path('api/helpline/', HelplineView.as_view(), name='api-helpline'),
    path('api/helpline', HelplineView.as_view()),
    path('api/api/helpline/', HelplineView.as_view()),
    path('api/api/helpline', HelplineView.as_view()),
    path('helpline/', HelplineView.as_view()),
    path('helpline', HelplineView.as_view()),
    path('api/support/', HelplineView.as_view()),
    path('api/support', HelplineView.as_view()),
    path('support/', HelplineView.as_view()),
    path('support', HelplineView.as_view()),

    path('api/terms-and-conditions/', TermsAndConditionsView.as_view(), name='api-terms-and-conditions'),
    path('api/terms-and-conditions', TermsAndConditionsView.as_view()),
    path('api/api/terms-and-conditions/', TermsAndConditionsView.as_view()),
    path('api/api/terms-and-conditions', TermsAndConditionsView.as_view()),
    path('terms-and-conditions/', TermsAndConditionsView.as_view()),
    path('terms-and-conditions', TermsAndConditionsView.as_view()),
    path('api/terms/', TermsAndConditionsView.as_view()),
    path('api/terms', TermsAndConditionsView.as_view()),
    path('terms/', TermsAndConditionsView.as_view()),
    path('terms', TermsAndConditionsView.as_view()),

    path('api/privacy-policy/', PrivacyPolicyView.as_view(), name='api-privacy-policy'),
    path('api/privacy-policy', PrivacyPolicyView.as_view()),
    path('api/api/privacy-policy/', PrivacyPolicyView.as_view()),
    path('api/api/privacy-policy', PrivacyPolicyView.as_view()),
    path('privacy-policy/', PrivacyPolicyView.as_view()),
    path('privacy-policy', PrivacyPolicyView.as_view()),
    path('api/privacy/', PrivacyPolicyView.as_view()),
    path('api/privacy', PrivacyPolicyView.as_view()),
    path('privacy/', PrivacyPolicyView.as_view()),
    path('privacy', PrivacyPolicyView.as_view()),

    # Standard App routing
    path('api/', include('core.urls')),
    path('', include('core.urls')),
]


# Serve user-uploaded media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

