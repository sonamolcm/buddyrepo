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
    CallerLoginView,
    CallerLoginSendOTPView,
    CallerLoginVerifyOTPView,
    # Listener Login Flow
    ListenerLoginView,
    # Logout Flow
    CallerLogoutView,
    ListenerLogoutView,
    LogoutView,
    # Account Deletion Flow
    DeleteAccountView,
    # Caller Profile
    ProfileView,
    CallerProfileView,
    # My Account Wallet & Account Deletion
    WalletView,
    GetCoinsView,
    AddCoinsView,
    CoinPurchaseHistoryView,
    CoinTransactionHistoryView,
    CallRequestView,
    IncomingCallsView,
    CallStatusUpdateView,
    AcceptCallView,
    RejectCallView,
    StartCallView,
    EndCallView,
    AgoraCallTokenView,
    CallHistoryView,
    CallDetailView,
    CallerAccountDeleteView,
    CallerFavoritesView,
    CallerFavoriteDetailView,
    # Metadata Dropdowns
    LanguageListView,
    InterestListView,
    CategoryListCreateView,
    CategoryDetailView,
    # Legal & Helpline
    TermsAndConditionsView,
    CallerPrivacySettingsView,
    PrivacyPolicyView,
    HelplineView,
    # Web Simulator & Web Auth Compatibility Views
    WebSendOTPView,
    WebVerifyOTPView,
    WebAboutYouView,
    WebInterestsView,
    WebLoginView,
    # Admin Listener Management APIs
    AdminCreateListenerView,
    AdminListenerListView,
    AdminDeleteListenerView,
    # Complete Caller & Listener CRUD
    CallerListCreateView,
    CallerDetailView,
    CallerUpdateView,
    CallerDeleteView,
    CallerDeleteDirectView,
    ListenerListCreateView,
    ListenerDetailView,
    ListenerDeleteView,
    ListenerDeleteDirectView,
    # Agent System APIs
    AgentLoginView,
    AgentLogoutView,
    AgentForgotPasswordView,
    AgentResetPasswordView,
    AgentProfileView,
    AgentProfessionsView,
    AgentRateView,
    AgentDutyView,
    AgentDutyOnView,
    AgentDutyOffView,
    AgentDashboardView,
    AgentEarningsTodayView,
    AgentEarningsHistoryView,
    AgentWalletView,
    AgentPayoutView,
    AgentRatingView,
    AgentRecentSessionsView,
    # Live Admin Actions
    AdminPayoutActionView,
    AdminUserToggleStatusView,
    FCMTokenUpdateView,
)

urlpatterns = [
    # Admin Live Action Routes
    path('admin/withdrawals/<int:payout_id>/action/', AdminPayoutActionView.as_view(), name='admin-payout-action'),
    path('admin/withdrawals/<int:payout_id>/action', AdminPayoutActionView.as_view()),
    path('admin/users/<int:user_id>/toggle/', AdminUserToggleStatusView.as_view(), name='admin-user-toggle'),
    path('admin/users/<int:user_id>/toggle', AdminUserToggleStatusView.as_view()),

    # ==========================================
    # 0. WEB SIMULATOR & COMPATIBILITY ROUTES
    # ==========================================
    path('auth/send-otp/', WebSendOTPView.as_view(), name='web-send-otp'),
    path('auth/verify-otp/', WebVerifyOTPView.as_view(), name='web-verify-otp'),
    path('auth/about-you/', WebAboutYouView.as_view(), name='web-about-you'),
    path('auth/interests/', WebInterestsView.as_view(), name='web-interests'),
    path('auth/login/', WebLoginView.as_view(), name='web-login'),

    # ==========================================
    # 1. CALLER SIGNUP FLOW
    # ==========================================
    path('auth/caller/signup/send-otp/', CallerSignupSendOTPView.as_view(), name='caller-signup-send-otp'),
    path('auth/caller/signup/verify-otp/', CallerSignupVerifyOTPView.as_view(), name='caller-signup-verify-otp'),
    path('auth/caller/signup/complete-profile/', CallerSignupCompleteProfileView.as_view(), name='caller-signup-complete-profile'),

    # ==========================================
    # 2. CALLER LOGIN & LOGOUT FLOW
    # ==========================================
    path('auth/caller/login/', CallerLoginView.as_view(), name='caller-login'),
    path('auth/caller/login', CallerLoginView.as_view(), name='caller-login-noslash'),
    path('caller/login/', CallerLoginView.as_view(), name='caller-login-short'),
    path('caller/login', CallerLoginView.as_view(), name='caller-login-short-noslash'),
    path('auth/caller/login/send-otp/', CallerLoginSendOTPView.as_view(), name='caller-login-send-otp'),
    path('auth/caller/login/send-otp', CallerLoginSendOTPView.as_view()),
    path('caller/login/send-otp/', CallerLoginSendOTPView.as_view()),
    path('caller/login/send-otp', CallerLoginSendOTPView.as_view()),
    path('auth/caller/login/verify-otp/', CallerLoginVerifyOTPView.as_view(), name='caller-login-verify-otp'),
    path('auth/caller/login/verify-otp', CallerLoginVerifyOTPView.as_view()),
    path('caller/login/verify-otp/', CallerLoginVerifyOTPView.as_view()),
    path('caller/login/verify-otp', CallerLoginVerifyOTPView.as_view()),
    path('auth/caller/logout/', CallerLogoutView.as_view(), name='caller-logout'),
    path('auth/caller/logout', CallerLogoutView.as_view(), name='caller-logout-noslash'),
    path('caller/logout/', CallerLogoutView.as_view(), name='caller-logout-short'),
    path('caller/logout', CallerLogoutView.as_view(), name='caller-logout-short-noslash'),

    # ==========================================
    # 3. LISTENER LOGIN & LOGOUT FLOW
    # ==========================================
    path('auth/listener/login/', ListenerLoginView.as_view(), name='listener-login'),
    path('auth/listener/login', ListenerLoginView.as_view(), name='listener-login-noslash'),
    path('listener/login/', ListenerLoginView.as_view(), name='listener-login-short'),
    path('listener/login', ListenerLoginView.as_view(), name='listener-login-short-noslash'),
    path('auth/listener/logout/', ListenerLogoutView.as_view(), name='listener-logout'),
    path('auth/listener/logout', ListenerLogoutView.as_view(), name='listener-logout-noslash'),
    path('listener/logout/', ListenerLogoutView.as_view(), name='listener-logout-short'),
    path('listener/logout', ListenerLogoutView.as_view(), name='listener-logout-short-noslash'),
    path('listenerlogout/', ListenerLogoutView.as_view(), name='listener-logout-joined'),
    path('listenerlogout', ListenerLogoutView.as_view()),
    path('listener-logout/', ListenerLogoutView.as_view()),
    path('listener-logout', ListenerLogoutView.as_view()),

    # ==========================================
    # 3.1 GENERAL LOGOUT FLOW
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
    # 5. CALLER PROFILE (ALL VARIANTS & ALIASES)
    # ==========================================
    path('profile/', ProfileView.as_view(), name='profile-detail'),
    path('profile', ProfileView.as_view()),
    path('profile/<str:identifier>/', ProfileView.as_view()),
    path('profile/<str:identifier>', ProfileView.as_view()),

    path('caller/profile/', CallerProfileView.as_view(), name='caller-profile'),
    path('caller/profile', CallerProfileView.as_view()),
    path('caller/profile/<str:identifier>/', CallerProfileView.as_view()),
    path('caller/profile/<str:identifier>', CallerProfileView.as_view()),

    path('caller-profile/', CallerProfileView.as_view(), name='caller-profile-dash'),
    path('caller-profile', CallerProfileView.as_view()),
    path('caller-profile/<str:identifier>/', CallerProfileView.as_view()),
    path('caller-profile/<str:identifier>', CallerProfileView.as_view()),

    path('callerprofile/', CallerProfileView.as_view(), name='caller-profile-joined'),
    path('callerprofile', CallerProfileView.as_view()),
    path('callerprofile/<str:identifier>/', CallerProfileView.as_view()),
    path('callerprofile/<str:identifier>', CallerProfileView.as_view()),

    # Exact name matches requested by user
    path('callerprofileview/', CallerProfileView.as_view(), name='caller-profile-view'),
    path('callerprofileview', CallerProfileView.as_view()),
    path('callerprofileview/<str:identifier>/', CallerProfileView.as_view()),
    path('callerprofileview/<str:identifier>', CallerProfileView.as_view()),

    path('caller-profile-view/', CallerProfileView.as_view(), name='caller-profile-view-dash'),
    path('caller-profile-view', CallerProfileView.as_view()),
    path('caller-profile-view/<str:identifier>/', CallerProfileView.as_view()),
    path('caller-profile-view/<str:identifier>', CallerProfileView.as_view()),

    path('profile/delete/', DeleteAccountView.as_view(), name='profile-delete'),
    path('profile/delete', DeleteAccountView.as_view()),
    path('caller/profile/delete/', DeleteAccountView.as_view()),
    path('caller/profile/delete', DeleteAccountView.as_view()),
    path('caller-profile/delete/', DeleteAccountView.as_view()),
    path('caller-profile/delete', DeleteAccountView.as_view()),

    # ==========================================
    # 5.1 MY ACCOUNT: WALLET & COINS (GET & ADD)
    # ==========================================
    path('wallet/', WalletView.as_view(), name='wallet-balance'),
    path('wallet', WalletView.as_view()),
    path('wallet/coins/', GetCoinsView.as_view()),
    path('wallet/coins', GetCoinsView.as_view()),
    path('coins/', GetCoinsView.as_view(), name='coins-get'),
    path('coins', GetCoinsView.as_view()),
    path('get-coins/', GetCoinsView.as_view(), name='coins-get-alias'),
    path('get-coins', GetCoinsView.as_view()),
    path('getcoins/', GetCoinsView.as_view()),
    path('getcoins', GetCoinsView.as_view()),
    path('coins/add/', AddCoinsView.as_view(), name='coins-add'),
    path('coins/add', AddCoinsView.as_view()),
    path('add-coins/', AddCoinsView.as_view(), name='coins-add-alias'),
    path('add-coins', AddCoinsView.as_view()),
    path('addcoins/', AddCoinsView.as_view()),
    path('addcoins', AddCoinsView.as_view()),

    # Coin Purchase & Transaction History
    path('coins/history/', CoinPurchaseHistoryView.as_view(), name='coin-purchase-history'),
    path('coins/history', CoinPurchaseHistoryView.as_view()),
    path('coins/purchase-history/', CoinPurchaseHistoryView.as_view(), name='coin-purchase-history-alias'),
    path('coins/purchase-history', CoinPurchaseHistoryView.as_view()),
    path('coins/purchases/', CoinPurchaseHistoryView.as_view(), name='coin-purchases'),
    path('coins/purchases', CoinPurchaseHistoryView.as_view()),
    path('coins/purchase/', CoinPurchaseHistoryView.as_view(), name='coin-purchase'),
    path('coins/purchase', CoinPurchaseHistoryView.as_view()),
    path('wallet/history/', CoinPurchaseHistoryView.as_view(), name='wallet-history'),
    path('wallet/history', CoinPurchaseHistoryView.as_view()),
    path('wallet/transactions/', CoinPurchaseHistoryView.as_view(), name='wallet-transactions'),
    path('wallet/transactions', CoinPurchaseHistoryView.as_view()),

    # ==========================================
    # 5.2 CALL WORKFLOW & HISTORY
    # ==========================================
    path('calls/request/', CallRequestView.as_view(), name='call-request'),
    path('calls/request', CallRequestView.as_view()),
    path('call/request/', CallRequestView.as_view()),
    path('call/request', CallRequestView.as_view()),
    path('callrequest/', CallRequestView.as_view()),
    path('callrequest', CallRequestView.as_view()),
    path('call-request/', CallRequestView.as_view()),
    path('call-request', CallRequestView.as_view()),

    path('calls/incoming/', IncomingCallsView.as_view(), name='calls-incoming'),
    path('calls/incoming', IncomingCallsView.as_view()),
    path('call/incoming/', IncomingCallsView.as_view()),
    path('call/incoming', IncomingCallsView.as_view()),

    path('calls/<int:call_id>/status/', CallStatusUpdateView.as_view(), name='call-status-update'),
    path('calls/<int:call_id>/status', CallStatusUpdateView.as_view()),

    path('calls/<int:call_id>/accept/', AcceptCallView.as_view(), name='call-accept'),
    path('calls/<int:call_id>/accept', AcceptCallView.as_view()),
    path('call/<int:call_id>/accept/', AcceptCallView.as_view()),
    path('call/<int:call_id>/accept', AcceptCallView.as_view()),

    path('calls/<int:call_id>/reject/', RejectCallView.as_view(), name='call-reject'),
    path('calls/<int:call_id>/reject', RejectCallView.as_view()),
    path('call/<int:call_id>/reject/', RejectCallView.as_view()),
    path('call/<int:call_id>/reject', RejectCallView.as_view()),

    path('calls/<int:call_id>/start/', StartCallView.as_view(), name='call-start'),
    path('calls/<int:call_id>/start', StartCallView.as_view()),
    path('call/<int:call_id>/start/', StartCallView.as_view()),
    path('call/<int:call_id>/start', StartCallView.as_view()),

    path('calls/<int:call_id>/end/', EndCallView.as_view(), name='call-end'),
    path('calls/<int:call_id>/end', EndCallView.as_view()),
    path('call/<int:call_id>/end/', EndCallView.as_view()),
    path('call/<int:call_id>/end', EndCallView.as_view()),

    path('calls/<int:call_id>/agora-token/', AgoraCallTokenView.as_view(), name='call-agora-token'),
    path('calls/<int:call_id>/agora-token', AgoraCallTokenView.as_view()),
    path('call/<int:call_id>/agora-token/', AgoraCallTokenView.as_view()),
    path('call/<int:call_id>/agora-token', AgoraCallTokenView.as_view()),

    path('calls/history/', CallHistoryView.as_view(), name='calls-history'),
    path('calls/history', CallHistoryView.as_view()),
    path('call/history/', CallHistoryView.as_view()),
    path('call/history', CallHistoryView.as_view()),
    path('callhistory/', CallHistoryView.as_view(), name='call-history'),
    path('callhistory', CallHistoryView.as_view()),
    path('call-history/', CallHistoryView.as_view(), name='call-history-alias'),
    path('call-history', CallHistoryView.as_view()),
    path('calls/', CallHistoryView.as_view(), name='calls-list'),
    path('calls', CallHistoryView.as_view()),
    path('callhistory/<int:call_id>/', CallDetailView.as_view(), name='call-detail'),
    path('callhistory/<int:call_id>', CallDetailView.as_view()),
    path('call-history/<int:call_id>/', CallDetailView.as_view()),
    path('call-history/<int:call_id>', CallDetailView.as_view()),

    path('caller/account/', CallerAccountDeleteView.as_view(), name='caller-account-delete'),
    path('caller/account', CallerAccountDeleteView.as_view()),

    # Caller Favorites
    path('favourites/', CallerFavoritesView.as_view(), name='caller-favourites'),
    path('favourites', CallerFavoritesView.as_view()),
    path('favourites/<int:agent_id>/', CallerFavoriteDetailView.as_view(), name='caller-favourite-detail'),
    path('favourites/<int:agent_id>', CallerFavoriteDetailView.as_view()),
    path('favourites/<str:agent_id>/', CallerFavoriteDetailView.as_view()),
    path('favourites/<str:agent_id>', CallerFavoriteDetailView.as_view()),
    path('favorites/', CallerFavoritesView.as_view(), name='caller-favorites'),
    path('favorites', CallerFavoritesView.as_view()),
    path('favorites/<int:agent_id>/', CallerFavoriteDetailView.as_view(), name='caller-favorite-detail'),
    path('favorites/<int:agent_id>', CallerFavoriteDetailView.as_view()),
    path('favorites/<str:agent_id>/', CallerFavoriteDetailView.as_view()),
    path('favorites/<str:agent_id>', CallerFavoriteDetailView.as_view()),

    # ==========================================
    # 6. METADATA DROPDOWNS (LANGUAGES, INTERESTS & CATEGORIES)
    # ==========================================
    path('languages/', LanguageListView.as_view(), name='language-list'),
    path('interests/', InterestListView.as_view(), name='interest-list'),

    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories', CategoryListCreateView.as_view()),
    path('categories/search/', CategoryListCreateView.as_view(), name='category-search'),
    path('categories/search', CategoryListCreateView.as_view()),
    path('categories/<str:identifier>/matches/', CategoryDetailView.as_view(), name='category-matches'),
    path('categories/<str:identifier>/matches', CategoryDetailView.as_view()),
    path('categories/<str:identifier>/listeners/', CategoryDetailView.as_view(), name='category-listeners'),
    path('categories/<str:identifier>/listeners', CategoryDetailView.as_view()),
    path('categories/<str:category_id>/listeners/<str:identifier>/', ListenerDetailView.as_view(), name='category-listener-detail'),
    path('categories/<str:category_id>/listeners/<str:identifier>', ListenerDetailView.as_view()),
    path('categories/<str:identifier>/', CategoryDetailView.as_view(), name='category-detail'),
    path('categories/<str:identifier>', CategoryDetailView.as_view()),

    # Doctors / Buddies profession alias routes
    path('doctors/', ListenerListCreateView.as_view(), name='doctor-list'),
    path('doctors', ListenerListCreateView.as_view()),
    path('doctors/<str:identifier>/', ListenerDetailView.as_view(), name='doctor-detail'),
    path('doctors/<str:identifier>', ListenerDetailView.as_view()),

    # ==========================================
    # 6.1 APP LEGAL & SUPPORT (TERMS, PRIVACY, HELPLINE)
    # ==========================================
    path('terms/', TermsAndConditionsView.as_view(), name='terms-and-conditions'),
    path('terms', TermsAndConditionsView.as_view()),
    path('terms-and-conditions/', TermsAndConditionsView.as_view()),
    path('terms-and-conditions', TermsAndConditionsView.as_view()),

    path('privacy/', CallerPrivacySettingsView.as_view(), name='privacy-settings'),
    path('privacy', CallerPrivacySettingsView.as_view()),
    path('privacy-policy/', CallerPrivacySettingsView.as_view()),
    path('privacy-policy', CallerPrivacySettingsView.as_view()),

    path('helpline/', HelplineView.as_view(), name='helpline'),
    path('helpline', HelplineView.as_view()),
    path('support/', HelplineView.as_view(), name='support'),
    path('support', HelplineView.as_view()),


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

    # Dedicated Caller Update routes (all aliases)
    path('callerupdate/', CallerUpdateView.as_view(), name='caller-update-root'),
    path('callerupdate', CallerUpdateView.as_view()),
    path('callerupdate/<str:identifier>/', CallerUpdateView.as_view()),
    path('callerupdate/<str:identifier>', CallerUpdateView.as_view()),
    path('caller-update/', CallerUpdateView.as_view()),
    path('caller-update', CallerUpdateView.as_view()),
    path('caller-update/<str:identifier>/', CallerUpdateView.as_view()),
    path('caller-update/<str:identifier>', CallerUpdateView.as_view()),
    path('caller/update/', CallerUpdateView.as_view(), name='caller-update-short'),
    path('caller/update', CallerUpdateView.as_view()),
    path('caller/update/<str:identifier>/', CallerUpdateView.as_view()),
    path('caller/update/<str:identifier>', CallerUpdateView.as_view()),

    # Dedicated Caller Delete routes (all aliases)
    path('callerdelete/', CallerDeleteView.as_view(), name='caller-delete-root'),
    path('callerdelete', CallerDeleteView.as_view()),
    path('callerdelete/<str:identifier>/', CallerDeleteView.as_view()),
    path('callerdelete/<str:identifier>', CallerDeleteView.as_view()),
    path('caller-delete/', CallerDeleteView.as_view()),
    path('caller-delete', CallerDeleteView.as_view()),
    path('caller-delete/<str:identifier>/', CallerDeleteView.as_view()),
    path('caller-delete/<str:identifier>', CallerDeleteView.as_view()),
    path('caller/delete/', CallerDeleteView.as_view(), name='caller-delete-short'),
    path('caller/delete', CallerDeleteView.as_view()),
    path('caller/delete/<str:identifier>/', CallerDeleteView.as_view()),
    path('caller/delete/<str:identifier>', CallerDeleteView.as_view()),

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

    # ==========================================
    # 10. AGENT SYSTEM ROUTES
    # ==========================================
    # Agent Authentication
    path('auth/agent/login/', AgentLoginView.as_view(), name='agent-login'),
    path('auth/agent/login', AgentLoginView.as_view()),
    path('agent/login/', AgentLoginView.as_view(), name='agent-login-short'),
    path('agent/login', AgentLoginView.as_view()),
    path('auth/agent/logout/', AgentLogoutView.as_view(), name='agent-logout'),
    path('auth/agent/logout', AgentLogoutView.as_view()),
    path('agent/logout/', AgentLogoutView.as_view(), name='agent-logout-short'),
    path('agent/logout', AgentLogoutView.as_view()),
    path('agent/password/forgot/', AgentForgotPasswordView.as_view(), name='agent-password-forgot'),
    path('agent/password/forgot', AgentForgotPasswordView.as_view()),
    path('auth/agent/password/forgot/', AgentForgotPasswordView.as_view()),
    path('auth/agent/password/forgot', AgentForgotPasswordView.as_view()),
    path('agent/password/reset/', AgentResetPasswordView.as_view(), name='agent-password-reset'),
    path('agent/password/reset', AgentResetPasswordView.as_view()),
    path('auth/agent/password/reset/', AgentResetPasswordView.as_view()),
    path('auth/agent/password/reset', AgentResetPasswordView.as_view()),

    # Agent Profile & Settings
    path('agent/profile/', AgentProfileView.as_view(), name='agent-profile'),
    path('agent/profile', AgentProfileView.as_view()),
    path('agent/professions/', AgentProfessionsView.as_view(), name='agent-professions'),
    path('agent/professions', AgentProfessionsView.as_view()),
    path('agent/rate/', AgentRateView.as_view(), name='agent-rate'),
    path('agent/rate', AgentRateView.as_view()),

    # Duty & Session Tracking
    path('agent/duty/', AgentDutyView.as_view(), name='agent-duty'),
    path('agent/duty', AgentDutyView.as_view()),
    path('agent/duty/on/', AgentDutyOnView.as_view(), name='agent-duty-on'),
    path('agent/duty/on', AgentDutyOnView.as_view()),
    path('agent/duty/off/', AgentDutyOffView.as_view(), name='agent-duty-off'),
    path('agent/duty/off', AgentDutyOffView.as_view()),

    # Dashboard & Statistics
    path('agent/dashboard/', AgentDashboardView.as_view(), name='agent-dashboard'),
    path('agent/dashboard', AgentDashboardView.as_view()),

    # Earnings & Wallet
    path('agent/earnings/today/', AgentEarningsTodayView.as_view(), name='agent-earnings-today'),
    path('agent/earnings/today', AgentEarningsTodayView.as_view()),
    path('agent/earnings/', AgentEarningsHistoryView.as_view(), name='agent-earnings-history'),
    path('agent/earnings', AgentEarningsHistoryView.as_view()),
    path('agent/wallet/', AgentWalletView.as_view(), name='agent-wallet'),
    path('agent/wallet', AgentWalletView.as_view()),
    path('agent/payouts/', AgentPayoutView.as_view(), name='agent-payouts'),
    path('agent/payouts', AgentPayoutView.as_view()),

    # Ratings, Reviews & Sessions
    path('agent/rating/', AgentRatingView.as_view(), name='agent-rating'),
    path('agent/rating', AgentRatingView.as_view()),
    path('agent/reviews/', AgentRatingView.as_view(), name='agent-reviews'),
    path('agent/reviews', AgentRatingView.as_view()),
    path('agent/sessions/recent/', AgentRecentSessionsView.as_view(), name='agent-sessions-recent'),
    path('agent/sessions/recent', AgentRecentSessionsView.as_view()),

    # FCM Device Token Update
    path('fcm-token/', FCMTokenUpdateView.as_view(), name='update-fcm-token'),
    path('fcm-token', FCMTokenUpdateView.as_view()),
]
