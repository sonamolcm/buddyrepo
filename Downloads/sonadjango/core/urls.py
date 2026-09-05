from django.urls import path
from .views import calculate_ats
from .views import ranked_candidates
from .security_api import SecurityTestAPI
from .payment_views import (
    AdminBillingAPI,
    AdminTransactionListAPI,
    CreatePaymentOrderAPI,
    VerifyPaymentAPI,
    PaymentWebhookAPI,
    SubscriptionStatusAPI,
    PremiumFeatureAPI,
    PremiumRecruiterAnalyticsAPI,
    AdminRevenueReportAPI,
)

from .views import (
    UserTestAPI,
    JobListAPI,
    JobCreateAPI,
    JobDetailAPI,
    FeaturedJobAPI,
    LatestJobAPI,
    SignupView,
    ProtectedView,
    EmployerAPI,
    CandidateAPI,
    AdminAPI,
    CandidateProfileAPI,
    CandidateProfileDetailAPI,
    EmployerProfileAPI,
    EmployerProfileDetailAPI,
    ApplyJobAPI,
    MyApplicationsAPI,
    EmployerApplicationsAPI,
    EmployerJobsAPI,
    UpdateApplicationStatusAPI,
    EmployerDashboardAPI,
    CandidateDashboardAPI,
    RecommendedJobsAPI,
    AdminDashboardAPI,
    ApproveEmployerAPI,
    BlockUserAPI,
    RemoveJobAPI,
    PlatformStatsAPI,
    UserGrowthAPI,
    JobActivityAPI,
    FlagAccountAPI,
    AuditLogAPI,
    ResumeExtractorAPI,
    calculate_ats,
    ranked_candidates,
    auto_shortlist_api,
    CallStatusAPIView
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("user/", UserTestAPI.as_view()),

    path("signup/", SignupView.as_view()),
    path("login/", TokenObtainPairView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
    path("protected/", ProtectedView.as_view()),

    path("employer/", EmployerAPI.as_view()),
    path("candidate/", CandidateAPI.as_view()),
    path("admin/", AdminAPI.as_view()),

    path("jobs/", JobListAPI.as_view()),
    path("jobs/create/", JobCreateAPI.as_view()),
    path("jobs/<int:pk>/", JobDetailAPI.as_view()),
    path("jobs/featured/", FeaturedJobAPI.as_view()),
    path("jobs/latest/", LatestJobAPI.as_view()),

    path("employer/jobs/", EmployerJobsAPI.as_view()),

    path("candidate-profile/", CandidateProfileAPI.as_view()),
    path("candidate-profile/<int:pk>/", CandidateProfileDetailAPI.as_view()),

    path("employer-profile/", EmployerProfileAPI.as_view()),
    path("employer-profile/<int:pk>/", EmployerProfileDetailAPI.as_view()),
    path("employer/jobs/", EmployerJobsAPI.as_view()),
    path("jobs/<int:pk>/apply/", ApplyJobAPI.as_view()),
    path("my-applications/", MyApplicationsAPI.as_view()),
    path("employer/applications/", EmployerApplicationsAPI.as_view()),

    path(
        "applications/<int:pk>/status/",
        UpdateApplicationStatusAPI.as_view(),
    ),
    path(
    "employer/dashboard/",
    EmployerDashboardAPI.as_view()
),
    path(
    "candidate/dashboard/",
    CandidateDashboardAPI.as_view()
),

    path(
    "candidate/recommendations/",
    RecommendedJobsAPI.as_view()
),
path(
    "admin/dashboard/",
    AdminDashboardAPI.as_view()

),

path(
"admin/approve-employer/<int:pk>/",
ApproveEmployerAPI.as_view()
),

path(
"admin/block-user/<int:pk>/",
BlockUserAPI.as_view()
),

path(
"admin/remove-job/<int:pk>/",
RemoveJobAPI.as_view()
),

path(
"admin/stats/",
PlatformStatsAPI.as_view()
),

path(
"admin/user-growth/",
UserGrowthAPI.as_view()
),

path(
"admin/job-activity/",
JobActivityAPI.as_view()
),

path(
"admin/flag-user/<int:pk>/",
FlagAccountAPI.as_view()
),

path(
"admin/audit-logs/",
AuditLogAPI.as_view()
),
path(
    "admin/stats/",
    PlatformStatsAPI.as_view()
),
path(
    "resume/extract/",
    ResumeExtractorAPI.as_view()
),
path(
    "ats/calculate/<int:application_id>/",
    calculate_ats,
    name="calculate_ats",
),
path(
    "ats/ranking/<int:job_id>/",
    ranked_candidates,
    name="ranked_candidates",
),
path(
    "applications/<int:application_id>/auto-shortlist/",
    auto_shortlist_api,
    name="auto_shortlist",
),

path(
    "applications/<int:pk>/call-status/",
    CallStatusAPIView.as_view()
),
path(
    "security-test/",
    SecurityTestAPI.as_view(),
    name="security-test"
),
path(
    "payment/create-order/",
    CreatePaymentOrderAPI.as_view(),
    name="payment-create-order"
),
path(
    "payment/verify/",
    VerifyPaymentAPI.as_view(),
    name="payment-verify"
),
path(
    "payment/webhook/",
    PaymentWebhookAPI.as_view(),
    name="payment-webhook"
),
path(
    "subscription/status/",
    SubscriptionStatusAPI.as_view(),
    name="subscription-status"
),
path(
    "premium-feature/",
    PremiumFeatureAPI.as_view(),
    name="premium-feature"
),
path(
    "recruiter/premium-analytics/",
    PremiumRecruiterAnalyticsAPI.as_view(),
    name="premium-recruiter-analytics"
),
path(
    "admin/billing/",
    AdminBillingAPI.as_view(),
    name="admin-billing"
),
path(
    "admin/transactions/",
    AdminTransactionListAPI.as_view(),
    name="admin-transactions"
),
path(
    "admin/revenue/",
    AdminRevenueReportAPI.as_view(),
    name="admin-revenue"
),
]

