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

    # Gabby Talk Logo handling
    import os, shutil, base64
    from django.conf import settings
    src_logo = r"C:\Users\SONA\.gemini\antigravity-ide\brain\2545965a-d412-4e3f-a386-e4674baed1ac\.user_uploaded\media_1788946290772.jpg"
    dst_dir = os.path.join(settings.BASE_DIR, 'static', 'images')
    dst_logo = os.path.join(dst_dir, 'gabby_talk_logo.jpg')
    app_logo_data = ""
    try:
        os.makedirs(dst_dir, exist_ok=True)
        if os.path.exists(src_logo):
            if not os.path.exists(dst_logo):
                shutil.copy(src_logo, dst_logo)
            with open(src_logo, 'rb') as f:
                app_logo_data = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
        elif os.path.exists(dst_logo):
            with open(dst_logo, 'rb') as f:
                app_logo_data = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    except Exception:
        pass

    context = {
        'app_name': 'Gabby Talk',
        'app_tagline': 'Real People • Meaningful Conversations',
        'app_logo_url': app_logo_data or '/static/images/gabby_talk_logo.jpg',
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


def admin_live_data_api(request: HttpRequest) -> HttpResponse:
    """Returns current live statistics, recent calls, users, payouts and transactions as JSON."""
    from django.http import JsonResponse
    from django.db.models import Sum
    from core.models import (
        User,
        ListenerProfile,
        CallerProfile,
        Call,
        Wallet,
        WalletTransaction,
        AgentPayout,
        AgentEarning
    )

    try:
        callers_count = User.objects.filter(role__in=['CALLER', 'USER']).count()
        listeners_count = User.objects.filter(role__in=['LISTENER', 'BUDDY', 'AGENT']).count()
        active_listeners_count = ListenerProfile.objects.filter(is_available=True).count()
        calls_count = Call.objects.count()

        total_coins_data = Wallet.objects.aggregate(total=Sum('balance'))
        total_coins = total_coins_data.get('total') or 0

        pending_withdrawals_count = AgentPayout.objects.filter(status='PENDING').count()
        total_payout_coins = AgentPayout.objects.filter(status__in=['APPROVED', 'COMPLETED']).aggregate(total=Sum('coins'))['total'] or 0

        # Recent Calls (latest 50)
        calls_qs = Call.objects.select_related('caller', 'receiver').order_by('-created_at')[:50]
        recent_calls = []
        for c in calls_qs:
            dur_sec = getattr(c, 'duration_seconds', 0) or 0
            dur = f"{dur_sec}s" if dur_sec else (f"{c.duration_minutes}m" if getattr(c, 'duration_minutes', 0) else "-")
            coins = getattr(c, 'coins_spent', None) or getattr(c, 'coins_deducted', None) or getattr(c, 'coins', 0) or 0

            caller_disp = 'Unknown'
            if c.caller:
                caller_disp = c.caller.phone_number or c.caller.username

            receiver_disp = 'Unknown'
            if c.receiver:
                receiver_disp = c.receiver.first_name or c.receiver.username

            recent_calls.append({
                'id': c.id,
                'caller': caller_disp,
                'receiver': receiver_disp,
                'call_type': getattr(c, 'call_type', 'VOICE') or 'VOICE',
                'status': getattr(c, 'status', 'COMPLETED'),
                'duration': dur,
                'duration_seconds': dur_sec,
                'coins': coins,
                'timestamp': c.created_at.strftime('%b %d, %H:%M') if hasattr(c, 'created_at') and c.created_at else ''
            })

        # Users (latest 100) - safely resolve OneToOne relations
        users_qs = User.objects.select_related('caller_profile', 'listener_profile', 'wallet', 'agent_wallet').order_by('-created_at')[:100]
        users_list = []
        for u in users_qs:
            name = u.first_name or u.username
            cp = getattr(u, 'caller_profile', None)
            lp = getattr(u, 'listener_profile', None)
            w = getattr(u, 'wallet', None)
            aw = getattr(u, 'agent_wallet', None)

            if cp and cp.name:
                name = cp.name
            elif lp and lp.name:
                name = lp.name

            bal = 0
            is_earned = False
            if aw and aw.balance:
                bal = aw.balance
                is_earned = True
            elif w and w.balance:
                bal = w.balance

            users_list.append({
                'id': u.id,
                'username': u.username,
                'name': name,
                'phone': u.phone_number or '',
                'role': u.role,
                'is_listener': u.is_listener,
                'coins': bal,
                'is_earned': is_earned,
                'is_verified': bool(u.is_verified),
                'is_active': bool(u.is_active),
                'created_at': u.created_at.strftime('%b %d, %Y') if hasattr(u, 'created_at') and u.created_at else ''
            })

        # Payouts (latest 30)
        payouts_qs = AgentPayout.objects.select_related('agent').order_by('-requested_at')[:30]
        payouts_list = []
        for p in payouts_qs:
            payouts_list.append({
                'id': p.id,
                'agent': (p.agent.first_name or p.agent.username) if p.agent else 'Unknown',
                'coins': p.coins,
                'amount_inr': getattr(p, 'amount_inr', p.coins) or p.coins,
                'method': getattr(p, 'payout_method', 'UPI') or 'UPI',
                'status': p.status,
                'requested_at': p.requested_at.strftime('%b %d, %H:%M') if hasattr(p, 'requested_at') and p.requested_at else ''
            })

        # Transactions (latest 30)
        tx_qs = WalletTransaction.objects.select_related('wallet__user').order_by('-created_at')[:30]
        transactions_list = []
        for tx in tx_qs:
            username = tx.wallet.user.username if (tx.wallet and tx.wallet.user) else 'Unknown'
            transactions_list.append({
                'id': tx.id,
                'username': username,
                'type': tx.transaction_type,
                'amount': tx.amount,
                'description': tx.description or 'Wallet transaction',
                'created_at': tx.created_at.strftime('%b %d, %H:%M') if hasattr(tx, 'created_at') and tx.created_at else ''
            })

        return JsonResponse({
            'success': True,
            'stats': {
                'calls_count': calls_count,
                'all_users_count': callers_count + listeners_count,
                'callers_count': callers_count,
                'listeners_count': listeners_count,
                'active_listeners_count': active_listeners_count,
                'pending_withdrawals_count': pending_withdrawals_count,
                'total_coins': total_coins,
                'total_payout_coins': total_payout_coins,
            },
            'recent_calls': recent_calls,
            'users': users_list,
            'payouts': payouts_list,
            'transactions': transactions_list,
        })
    except Exception as e:
        import traceback
        return JsonResponse({'success': False, 'message': str(e), 'trace': traceback.format_exc()}, status=500)


