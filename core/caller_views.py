# pyright: reportMissingImports=false
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse

def app_home_view(request: HttpRequest) -> HttpResponse:
    """Renders the main mobile app onboarding interface (Splash -> Role -> Auth -> Home)."""
    return render(request, 'index.html')

def caller_signup_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')

def caller_signup_otp_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')

def caller_login_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')

def caller_login_otp_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')

def caller_profile_setup_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')

def caller_home_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')

def caller_profile_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')

def admin_panel_view(request: HttpRequest) -> HttpResponse:
    """Renders the comprehensive Buddy Admin Dashboard with real-time statistics."""
    from core.models import (
        User,
        ListenerProfile,
        CallerProfile,
        Call,
        Wallet,
        WalletTransaction,
        Category,
        AgentPayout,
        AgentEarning
    )
    from django.db.models import Sum, Count, Q
    from core.views import WORLD_LANGUAGES

    callers_count = User.objects.filter(role__in=['CALLER', 'USER']).count()
    listeners_count = User.objects.filter(role__in=['LISTENER', 'BUDDY', 'AGENT']).count()
    active_listeners_count = ListenerProfile.objects.filter(is_available=True).count()
    calls_count = Call.objects.count()
    categories_count = Category.objects.filter(is_active=True).count()

    total_coins_data = Wallet.objects.aggregate(total=Sum('balance'))
    total_coins = total_coins_data.get('total') or 0

    pending_withdrawals_count = AgentPayout.objects.filter(status='PENDING').count()
    total_payout_coins = AgentPayout.objects.filter(status__in=['APPROVED', 'COMPLETED']).aggregate(total=Sum('coins'))['total'] or 0

    recent_calls = Call.objects.select_related('caller', 'receiver').order_by('-created_at')[:80]
    all_users = User.objects.select_related('caller_profile', 'listener_profile', 'wallet', 'agent_wallet').order_by('-created_at')[:100]
    categories = list(Category.objects.filter(is_active=True).order_by('name'))
    payouts = AgentPayout.objects.select_related('agent', 'agent__agent_wallet').order_by('-requested_at')[:60]
    wallet_transactions = WalletTransaction.objects.select_related('wallet__user').order_by('-created_at')[:60]
    agent_earnings = AgentEarning.objects.select_related('agent').order_by('-created_at')[:60]

    context = {
        'callers_count': callers_count,
        'listeners_count': listeners_count,
        'active_listeners_count': active_listeners_count,
        'categories_count': categories_count,
        'calls_count': calls_count,
        'total_coins': total_coins,
        'pending_withdrawals_count': pending_withdrawals_count,
        'total_payout_coins': total_payout_coins,
        'recent_calls': recent_calls,
        'all_users': all_users,
        'categories': categories,
        'world_languages': WORLD_LANGUAGES,
        'payouts': payouts,
        'wallet_transactions': wallet_transactions,
        'agent_earnings': agent_earnings,
    }
    return render(request, 'admin_panel.html', context)

