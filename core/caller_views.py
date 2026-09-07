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
    from core.models import User, ListenerProfile, CallerProfile, Call, Wallet
    from django.db.models import Sum

    callers_count = User.objects.filter(role__in=['CALLER', 'USER']).count()
    listeners_count = User.objects.filter(role__in=['LISTENER', 'BUDDY']).count()
    active_listeners_count = ListenerProfile.objects.filter(is_available=True).count()
    calls_count = Call.objects.count()
    total_coins_data = Wallet.objects.aggregate(total=Sum('balance'))
    total_coins = total_coins_data.get('total') or 0

    recent_listeners = ListenerProfile.objects.select_related('user').order_by('-created_at')[:15]
    recent_calls = Call.objects.select_related('caller', 'receiver').order_by('-created_at')[:10]

    context = {
        'callers_count': callers_count,
        'listeners_count': listeners_count,
        'active_listeners_count': active_listeners_count,
        'calls_count': calls_count,
        'total_coins': total_coins,
        'recent_listeners': recent_listeners,
        'recent_calls': recent_calls,
    }
    return render(request, 'admin_panel.html', context)

