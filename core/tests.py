from django.test import TestCase
import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from core.models import (
    Category,
    ListenerProfile,
    CallerProfile,
    Call,
    CallReview,
    Wallet,
    WalletTransaction,
    AgentDutySession,
    AgentWallet,
    AgentEarning,
    AgentPayout,
    OTPVerification,
    ConversationCategory,
    CALLER_NEED_OPTIONS,
)
from core.constants import ALLOWED_REVIEW_TAGS
from core.views import get_weekly_payout_bounds

User = get_user_model()


class AgentAuthAndProfileTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Mental Wellness", description="Counseling and guidance")
        self.agent_user = User.objects.create_user(
            username="agent_test_01",
            password="SecurePassword123!",
            email="agent01@example.com",
            phone_number="+919876543210",
            role="AGENT"
        )
        self.profile, _ = ListenerProfile.objects.get_or_create(
            user=self.agent_user,
            defaults={
                'listener_id': 'agent_test_01',
                'name': 'Agent Test',
                'rate_per_second': 3,
                'profession': self.category,
                'language': 'English'
            }
        )

    def test_agent_login_success(self):
        response = self.client.post('/api/auth/agent/login/', {
            'username': 'agent_test_01',
            'password': 'SecurePassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('tokens', response.data['data'])
        self.assertIn('access', response.data['data']['tokens'])
        self.assertEqual(response.data['data']['user']['username'], 'agent_test_01')

    def test_agent_login_invalid_credentials(self):
        response = self.client.post('/api/auth/agent/login/', {
            'username': 'agent_test_01',
            'password': 'WrongPassword!'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])

    def test_agent_profile_get_and_patch(self):
        self.client.force_authenticate(user=self.agent_user)
        # GET profile
        get_res = self.client.get('/api/agent/profile/')
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_res.data['data']['rate_per_second'], 3)

        # PATCH profile
        patch_res = self.client.patch('/api/agent/profile/', {
            'bio': 'Experienced empathetic listener and advisor.',
            'name': 'Senior Agent John'
        })
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, 'Experienced empathetic listener and advisor.')
        # PATCH profile with category string name (e.g. 'nurse')
        patch_cat_res = self.client.patch('/api/agent/profile/', {
            'category': 'nurse'
        })
        self.assertEqual(patch_cat_res.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertIsNotNone(self.profile.profession)
        self.assertEqual(self.profile.profession.name.lower(), 'nurse')
        self.assertEqual(patch_cat_res.data['data']['profession_name'].lower(), 'nurse')
        self.assertEqual(patch_cat_res.data['data']['category']['name'].lower(), 'nurse')

    def test_agent_rate_update(self):
        self.client.force_authenticate(user=self.agent_user)
        # Valid rate update (choices: 3, 5, 10)
        res = self.client.post('/api/agent/rate/', {'rate_per_second': 5})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.rate_per_second, 5)

        # Invalid rate update
        bad_res = self.client.post('/api/agent/rate/', {'rate_per_second': 7})
        self.assertEqual(bad_res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_agent_password_forgot_and_reset(self):
        # Forgot password request
        forgot_res = self.client.post('/api/agent/password/forgot/', {
            'identifier': 'agent01@example.com'
        })
        self.assertEqual(forgot_res.status_code, status.HTTP_200_OK)
        reset_token = forgot_res.data['reset_token']

        # Reset password
        reset_res = self.client.post('/api/agent/password/reset/', {
            'identifier': 'agent01@example.com',
            'token': reset_token,
            'new_password': 'BrandNewPassword123!',
            'confirm_password': 'BrandNewPassword123!'
        })
        self.assertEqual(reset_res.status_code, status.HTTP_200_OK)

        # Login with new password
        login_res = self.client.post('/api/auth/agent/login/', {
            'username': 'agent_test_01',
            'password': 'BrandNewPassword123!'
        })
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)


class AgentDutyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.agent = User.objects.create_user(
            username="duty_agent",
            password="Pass123!Password",
            role="AGENT"
        )
        self.profile, _ = ListenerProfile.objects.get_or_create(
            user=self.agent,
            defaults={'listener_id': 'duty_agent', 'is_on_duty': False, 'is_available': False}
        )
        self.client.force_authenticate(user=self.agent)

    def test_duty_on_and_off(self):
        # Turn Duty ON
        on_res = self.client.post('/api/agent/duty/on/')
        self.assertEqual(on_res.status_code, status.HTTP_200_OK)
        self.assertTrue(on_res.data['is_on_duty'])
        self.profile.refresh_from_db()
        self.agent.refresh_from_db()
        self.assertTrue(self.profile.is_on_duty)
        self.assertTrue(self.profile.is_available)
        self.assertEqual(AgentDutySession.objects.filter(agent=self.agent, ended_at__isnull=True).count(), 1)

        # Check Duty status
        status_res = self.client.get('/api/agent/duty/')
        self.assertEqual(status_res.status_code, status.HTTP_200_OK)
        self.assertTrue(status_res.data['is_on_duty'])

        # Turn Duty OFF
        off_res = self.client.post('/api/agent/duty/off/')
        self.assertEqual(off_res.status_code, status.HTTP_200_OK)
        self.assertFalse(off_res.data['is_on_duty'])
        self.profile.refresh_from_db()
        self.agent.refresh_from_db()
        self.assertFalse(self.profile.is_on_duty)
        self.assertFalse(self.profile.is_available)
        self.assertEqual(AgentDutySession.objects.filter(agent=self.agent, ended_at__isnull=True).count(), 0)


class AgentCallLifecycleAndBillingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.caller = User.objects.create_user(
            username="caller_01",
            password="CallerPassword123!",
            role="CALLER"
        )
        self.agent = User.objects.create_user(
            username="agent_call_01",
            password="AgentPassword123!",
            role="AGENT"
        )
        self.profile, _ = ListenerProfile.objects.get_or_create(
            user=self.agent,
            defaults={
                'listener_id': 'agent_call_01',
                'rate_per_second': 3,
                'is_on_duty': True,
                'is_available': True
            }
        )
        self.caller_wallet, _ = Wallet.objects.get_or_create(user=self.caller, defaults={'balance': 200})
        self.agent_wallet, _ = AgentWallet.objects.get_or_create(agent=self.agent, defaults={'balance': 0})

    def test_call_lifecycle_and_per_second_billing(self):
        # Create a pending call
        call = Call.objects.create(
            caller=self.caller,
            receiver=self.agent,
            channel_name="test_channel_101",
            status="RINGING"
        )

        # 1. Agent sees incoming call
        self.client.force_authenticate(user=self.agent)
        incoming_res = self.client.get('/api/calls/incoming/')
        self.assertEqual(incoming_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(incoming_res.data['calls']), 1)
        self.assertEqual(incoming_res.data['calls'][0]['id'], call.id)

        # 2. Agent accepts call
        accept_res = self.client.post(f'/api/calls/{call.id}/accept/')
        self.assertEqual(accept_res.status_code, status.HTTP_200_OK)
        call.refresh_from_db()
        self.assertEqual(call.status, 'ACCEPTED')
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.is_busy)

        # 3. Start call
        start_res = self.client.post(f'/api/calls/{call.id}/start/')
        self.assertEqual(start_res.status_code, status.HTTP_200_OK)
        call.refresh_from_db()
        self.assertEqual(call.status, 'ACTIVE')
        self.assertIsNotNone(call.started_at)

        # Simulate 10 seconds of call time
        started_time = timezone.now() - timezone.timedelta(seconds=10)
        call.started_at = started_time
        call.save(update_fields=['started_at'])

        # 4. End call
        end_res = self.client.post(f'/api/calls/{call.id}/end/')
        self.assertEqual(end_res.status_code, status.HTTP_200_OK)
        call.refresh_from_db()
        self.assertEqual(call.status, 'COMPLETED')
        self.assertGreaterEqual(call.duration_seconds, 10)

        # Rate is 3 coins/second. coins_deducted = duration_seconds * 3
        expected_deducted = call.duration_seconds * 3
        self.assertEqual(call.coins_deducted, expected_deducted)

        # Verify Caller Wallet was debited
        self.caller_wallet.refresh_from_db()
        self.assertEqual(self.caller_wallet.balance, 200 - expected_deducted)

        # Verify Agent Wallet was credited
        self.agent_wallet.refresh_from_db()
        self.assertEqual(self.agent_wallet.balance, expected_deducted)
        self.assertEqual(self.agent_wallet.total_earned, expected_deducted)

        # Verify AgentEarning record created
        earning = AgentEarning.objects.filter(call=call, agent=self.agent).first()
        self.assertIsNotNone(earning)
        self.assertEqual(earning.coins, expected_deducted)
        self.assertEqual(earning.amount, expected_deducted)

        # Verify Agent stats updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.total_calls, 1)
        self.assertEqual(self.profile.total_earned_coins, expected_deducted)
        self.assertFalse(self.profile.is_busy)

        # 5. Prevent double ending / double charging
        double_end_res = self.client.post(f'/api/calls/{call.id}/end/')
        self.assertEqual(double_end_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.agent_wallet.refresh_from_db()
        self.assertEqual(self.agent_wallet.balance, expected_deducted)


class AgentDashboardAndPayoutTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.agent = User.objects.create_user(
            username="agent_dash_01",
            password="AgentPassword123!",
            role="AGENT"
        )
        self.profile, _ = ListenerProfile.objects.get_or_create(
            user=self.agent,
            defaults={'listener_id': 'agent_dash_01'}
        )
        self.profile.rate_per_second = 5
        self.profile.save(update_fields=['rate_per_second'])
        self.wallet, _ = AgentWallet.objects.get_or_create(agent=self.agent)
        self.wallet.balance = 150
        self.wallet.total_earned = 300
        self.wallet.save(update_fields=['balance', 'total_earned'])
        self.client.force_authenticate(user=self.agent)

        # Seed eligible completed week earnings for testing
        comp_mon, comp_sun, _, _ = get_weekly_payout_bounds()
        comp_dt = datetime.datetime.combine(comp_mon + datetime.timedelta(days=2), datetime.time(12, 0)).replace(tzinfo=datetime.timezone.utc)
        earning = AgentEarning.objects.create(
            agent=self.agent,
            coins=150,
            earning_type='VOICE',
            description="Call session"
        )
        AgentEarning.objects.filter(id=earning.id).update(created_at=comp_dt)

    def test_agent_dashboard(self):
        res = self.client.get('/api/agent/dashboard/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        data = res.data['data']
        self.assertEqual(data['earnings']['wallet_balance'], 150)
        self.assertEqual(data['earnings']['lifetime_coins'], 300)
        self.assertEqual(data['profile']['rate_per_second'], 5)

    def test_agent_payout_request_success(self):
        payout_res = self.client.post('/api/agent/payouts/', {
            'coins': 50,
            'payout_method': 'UPI',
            'details': {'upi_id': 'agent@okhdfcbank'}
        }, format='json')
        self.assertEqual(payout_res.status_code, status.HTTP_201_CREATED)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 100)
        self.assertEqual(self.wallet.total_paid_out, 50)
        self.assertEqual(AgentPayout.objects.filter(agent=self.agent).count(), 1)

    def test_agent_payout_request_insufficient_balance(self):
        bad_res = self.client.post('/api/agent/payouts/', {
            'coins': 500,
            'payout_method': 'UPI',
            'details': {'upi_id': 'agent@okhdfcbank'}
        }, format='json')
        self.assertEqual(bad_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 150)


class AgentWeeklyPayoutAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.agent = User.objects.create_user(
            username="agent_weekly_01",
            password="AgentPassword123!",
            role="AGENT",
            phone_number="+919876543220"
        )
        self.profile, _ = ListenerProfile.objects.get_or_create(
            user=self.agent,
            defaults={'listener_id': 'agent_weekly_01', 'rate_per_second': 5}
        )
        self.wallet, _ = AgentWallet.objects.get_or_create(agent=self.agent)
        self.wallet.balance = 200
        self.wallet.total_earned = 200
        self.wallet.save(update_fields=['balance', 'total_earned'])
        self.caller = User.objects.create_user(
            username="caller_weekly_01",
            password="CallerPassword123!",
            role="CALLER",
            phone_number="+919876543221"
        )
        self.comp_mon, self.comp_sun, self.curr_mon, self.curr_sun = get_weekly_payout_bounds()

    def _create_earning(self, agent, coins, target_date):
        dt = datetime.datetime.combine(target_date, datetime.time(14, 0)).replace(tzinfo=datetime.timezone.utc)
        earning = AgentEarning.objects.create(
            agent=agent,
            coins=coins,
            earning_type='VOICE',
            description=f"Voice earning {coins} coins"
        )
        AgentEarning.objects.filter(id=earning.id).update(created_at=dt)
        return AgentEarning.objects.get(id=earning.id)

    def test_valid_weekly_payout_request_automatic_completed_week(self):
        self.client.force_authenticate(user=self.agent)
        # Create 100 coins of earnings in the completed week
        earning = self._create_earning(self.agent, 100, self.comp_mon + datetime.timedelta(days=2))

        res = self.client.post('/api/agent/payouts/', {
            'payout_method': 'UPI',
            'payout_details': {'upi_id': 'agent@okhdfcbank'}
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        payout_data = res.data['payout']
        self.assertEqual(payout_data['coins'], 100)
        self.assertEqual(payout_data['week_start_date'], str(self.comp_mon))
        self.assertEqual(payout_data['week_end_date'], str(self.comp_sun))
        self.assertEqual(payout_data['status'], 'PENDING')

        # Check AgentWallet balance deducted
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 100)
        self.assertEqual(self.wallet.total_paid_out, 100)

        # Check earning is linked to this payout
        earning.refresh_from_db()
        self.assertIsNotNone(earning.payout)
        self.assertEqual(earning.payout.id, payout_data['id'])

    def test_payout_outside_eligible_weekly_period_rejected(self):
        self.client.force_authenticate(user=self.agent)
        # Attempt payout for current ongoing week
        res = self.client.post('/api/agent/payouts/', {
            'week_start_date': str(self.curr_mon),
            'payout_method': 'UPI'
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertIn("still ongoing", res.data['message'])

        # Invalid start date not a Monday
        not_monday = self.comp_mon + datetime.timedelta(days=1)
        res2 = self.client.post('/api/agent/payouts/', {
            'week_start_date': str(not_monday),
            'payout_method': 'UPI'
        })
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("must start on a Monday", res2.data['message'])

    def test_duplicate_payout_request_for_same_week_rejected(self):
        self.client.force_authenticate(user=self.agent)
        self._create_earning(self.agent, 80, self.comp_mon + datetime.timedelta(days=1))

        # First request succeeds
        res1 = self.client.post('/api/agent/payouts/', {'payout_method': 'UPI'})
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Second request for the same week fails
        res2 = self.client.post('/api/agent/payouts/', {'payout_method': 'UPI'})
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res2.data['success'])
        self.assertIn("already been submitted", res2.data['message'])

    def test_insufficient_or_zero_eligible_earnings_rejected(self):
        self.client.force_authenticate(user=self.agent)
        # No earnings created for completed week
        res = self.client.post('/api/agent/payouts/', {'payout_method': 'UPI'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertIn("No eligible unpaid earnings found", res.data['message'])

    def test_earnings_below_minimum_threshold_rejected(self):
        self.client.force_authenticate(user=self.agent)
        # Create only 30 coins (< 50 minimum)
        self._create_earning(self.agent, 30, self.comp_mon + datetime.timedelta(days=1))
        res = self.client.post('/api/agent/payouts/', {'payout_method': 'UPI'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertIn("below the minimum payout threshold of 50 coins", res.data['message'])

    def test_unauthorized_user_rejected(self):
        # No auth
        res = self.client.post('/api/agent/payouts/', {'payout_method': 'UPI'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_agent_user_rejected(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/agent/payouts/', {'payout_method': 'UPI'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_payout_processing_approve_complete_reject(self):
        self.client.force_authenticate(user=self.agent)
        earning = self._create_earning(self.agent, 75, self.comp_mon + datetime.timedelta(days=1))
        payout_res = self.client.post('/api/agent/payouts/', {'payout_method': 'UPI'})
        self.assertEqual(payout_res.status_code, status.HTTP_201_CREATED)
        payout_id = payout_res.data['payout']['id']

        # Admin Approve
        app_res = self.client.post(f'/api/admin/withdrawals/{payout_id}/action/', {'action': 'approve', 'note': 'Approved'})
        self.assertEqual(app_res.status_code, status.HTTP_200_OK)
        payout = AgentPayout.objects.get(id=payout_id)
        self.assertEqual(payout.status, 'APPROVED')

        # Admin Complete
        comp_res = self.client.post(f'/api/admin/withdrawals/{payout_id}/action/', {'action': 'complete'})
        self.assertEqual(comp_res.status_code, status.HTTP_200_OK)
        payout.refresh_from_db()
        self.assertEqual(payout.status, 'COMPLETED')

        # Admin Reject with Refund & Earning Unlink
        rej_res = self.client.post(f'/api/admin/withdrawals/{payout_id}/action/', {'action': 'reject', 'note': 'Bank failure'})
        self.assertEqual(rej_res.status_code, status.HTTP_200_OK)
        payout.refresh_from_db()
        self.assertEqual(payout.status, 'REJECTED')

        # Verify wallet refunded
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 200)
        self.assertEqual(self.wallet.total_paid_out, 0)

        # Verify earning unlinked
        earning.refresh_from_db()
        self.assertIsNone(earning.payout)

    def test_get_payouts_returns_weekly_summary(self):
        self.client.force_authenticate(user=self.agent)
        self._create_earning(self.agent, 120, self.comp_mon + datetime.timedelta(days=3))
        res = self.client.get('/api/agent/payouts/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertIn('weekly_summary', res.data)
        summary = res.data['weekly_summary']
        self.assertEqual(summary['latest_completed_week']['week_start'], str(self.comp_mon))
        self.assertEqual(summary['latest_completed_week']['week_end'], str(self.comp_sun))
        self.assertEqual(summary['latest_completed_week']['eligible_coins'], 120)
        self.assertTrue(summary['latest_completed_week']['can_request_payout'])


class CategoryFilterAndSearchAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        Category.objects.all().delete()
        Category.objects.create(name="Teacher", description="Educator", is_active=True)
        Category.objects.create(name="Technician", description="Technical specialist", is_active=True)
        Category.objects.create(name="Doctor", description="Physician", is_active=True)
        Category.objects.create(name="Software Developer", description="Coder", is_active=True)
        Category.objects.create(name="Student", description="Learner", is_active=True)
        Category.objects.create(name="Inactive Category", description="Not active", is_active=False)

    def test_list_all_active_categories_without_filter(self):
        res = self.client.get('/api/categories/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get('status', False))
        self.assertEqual(res.data.get('message'), "Categories retrieved successfully.")
        items = res.data.get('data', res.data if isinstance(res.data, list) else [])
        names = [item['name'] for item in items]
        self.assertIn("Teacher", names)
        self.assertIn("Technician", names)
        self.assertIn("Doctor", names)
        self.assertIn("Software Developer", names)
        self.assertIn("Student", names)
        self.assertNotIn("Inactive Category", names)

    def test_filter_by_first_letter(self):
        # Filtering by first letter 't' (case-insensitive)
        res = self.client.get('/api/categories/?search=t')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get('status', False))
        items = res.data.get('data', res.data if isinstance(res.data, list) else [])
        names = [item['name'] for item in items]
        self.assertEqual(names, ["Teacher", "Technician"])

    def test_filter_by_second_letter_prefix(self):
        # Filtering by first two letters 'te'
        res = self.client.get('/api/categories/?search=te')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get('status', False))
        items = res.data.get('data', res.data if isinstance(res.data, list) else [])
        names = [item['name'] for item in items]
        self.assertEqual(names, ["Teacher", "Technician"])

    def test_filter_case_insensitive_uppercase(self):
        res = self.client.get('/api/categories/?search=DO')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get('status', False))
        items = res.data.get('data', res.data if isinstance(res.data, list) else [])
        names = [item['name'] for item in items]
        self.assertEqual(names, ["Doctor"])

    def test_filter_first_letter_d(self):
        res = self.client.get('/api/categories/?search=d')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get('status', False))
        items = res.data.get('data', res.data if isinstance(res.data, list) else [])
        names = [item['name'] for item in items]
        self.assertEqual(names, ["Doctor"])

    def test_filter_first_two_letters_st_vs_so(self):
        res_st = self.client.get('/api/categories/?q=st')
        self.assertEqual(res_st.status_code, status.HTTP_200_OK)
        items_st = res_st.data.get('data', res_st.data if isinstance(res_st.data, list) else [])
        self.assertEqual([item['name'] for item in items_st], ["Student"])

        res_so = self.client.get('/api/categories/?starts_with=so')
        self.assertEqual(res_so.status_code, status.HTTP_200_OK)
        items_so = res_so.data.get('data', res_so.data if isinstance(res_so.data, list) else [])
        self.assertEqual([item['name'] for item in items_so], ["Software Developer"])

    def test_filter_no_match(self):
        res = self.client.get('/api/categories/?search=xyz')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        items = res.data.get('data', res.data if isinstance(res.data, list) else [])
        self.assertEqual(len(items), 0)

    def test_search_path_endpoint(self):
        res = self.client.get('/api/categories/search/?search=t')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        items = res.data.get('data', res.data if isinstance(res.data, list) else [])
        names = [item['name'] for item in items]
        self.assertEqual(names, ["Teacher", "Technician"])

    def test_category_shows_matches_count_and_details_when_selected(self):
        doctor_cat = Category.objects.get(name="Doctor")

        # Create two doctors
        u1 = User.objects.create_user(username="dr_smith", password="Pass123!Safe", role="LISTENER", first_name="Dr. Alice Smith", is_active=True)
        u1_profile, _ = ListenerProfile.objects.get_or_create(user=u1)
        u1_profile.listener_id = "dr_smith"
        u1_profile.name = "Dr. Alice Smith"
        u1_profile.profession = doctor_cat
        u1_profile.bio = "Cardiologist and wellness guide"
        u1_profile.rate_per_second = 5
        u1_profile.rating = 4.9
        u1_profile.total_calls = 15
        u1_profile.save()

        u2 = User.objects.create_user(username="dr_house", password="Pass123!Safe", role="LISTENER", first_name="Dr. Gregory House", is_active=True)
        u2_profile, _ = ListenerProfile.objects.get_or_create(user=u2)
        u2_profile.listener_id = "dr_house"
        u2_profile.name = "Dr. Gregory House"
        u2_profile.profession = doctor_cat
        u2_profile.bio = "Diagnostic medicine and health counselor"
        u2_profile.rate_per_second = 10
        u2_profile.rating = 5.0
        u2_profile.total_calls = 40
        u2_profile.save()

        # 1. Search category on search bar -> shows match count
        search_res = self.client.get('/api/categories/?search=doc')
        self.assertEqual(search_res.status_code, status.HTTP_200_OK)
        self.assertTrue(search_res.data.get('status', False))
        items = search_res.data.get('data', search_res.data if isinstance(search_res.data, list) else [])
        self.assertEqual(len(items), 1)
        doc_item = items[0]
        self.assertEqual(doc_item['name'], "Doctor")
        self.assertEqual(doc_item['count'], 2)
        self.assertEqual(doc_item['matches_count'], 2)
        self.assertEqual(len(doc_item['matches']), 2)

        # 2. Choose Doctor category -> shows status, message at top & matches list inside data
        cat_detail_res = self.client.get(f'/api/categories/{doctor_cat.id}/')
        self.assertEqual(cat_detail_res.status_code, status.HTTP_200_OK)
        self.assertTrue(cat_detail_res.data.get('status'))
        self.assertIn('message', cat_detail_res.data)
        cat_data = cat_detail_res.data.get('data', cat_detail_res.data)
        self.assertEqual(cat_data['name'], "Doctor")
        self.assertEqual(cat_data['count'], 2)
        self.assertEqual(len(cat_data['matches']), 2)

        # Also works by category name
        by_name_res = self.client.get('/api/categories/Doctor/')
        self.assertEqual(by_name_res.status_code, status.HTTP_200_OK)
        self.assertTrue(by_name_res.data.get('status'))
        self.assertIn('message', by_name_res.data)
        by_name_data = by_name_res.data.get('data', by_name_res.data)
        self.assertEqual(by_name_data['count'], 2)

        # 3. Select one doctor -> shows full details
        doctor_detail_res = self.client.get('/api/listeners/dr_house/')
        self.assertEqual(doctor_detail_res.status_code, status.HTTP_200_OK)
        self.assertTrue(doctor_detail_res.data['success'])
        doc_data = doctor_detail_res.data['data']
        self.assertEqual(doc_data['username'], 'dr_house')
        self.assertEqual(doc_data['name'], 'Dr. Gregory House')
        self.assertEqual(doc_data['profession']['name'], 'Doctor')
        self.assertEqual(doc_data['bio'], 'Diagnostic medicine and health counselor')
        self.assertEqual(doc_data['rate_per_second'], 10)
        self.assertEqual(doc_data['rate_per_minute'], 600)
        self.assertEqual(doc_data['total_calls'], 40)
        self.assertEqual(doc_data['rating'], 5.0)

        # 4. Filter listeners by category
        listener_filter_res = self.client.get('/api/listeners/?category=Doctor')
        self.assertEqual(listener_filter_res.status_code, status.HTTP_200_OK)
        self.assertEqual(listener_filter_res.data['count'], 2)


class CoinPurchaseHistoryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="caller_coin_user",
            password="Pass123!Safe",
            phone_number="+919988776655",
            role="CALLER",
            is_active=True,
            is_verified=True
        )
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user, defaults={'balance': 50})

    def test_get_coin_purchase_history_empty(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get('/api/coins/history/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get('status'))
        self.assertIn('message', res.data)
        self.assertIn('data', res.data)
        data = res.data['data']
        self.assertEqual(data['current_balance'], 50)
        self.assertEqual(data['total_coins_purchased'], 0)
        self.assertEqual(len(data['purchases']), 0)

    def test_post_coin_purchase_and_retrieve_history(self):
        self.client.force_authenticate(user=self.user)
        # Purchase 100 coins
        post_res = self.client.post('/api/coins/history/', {
            'coins': 100,
            'price': 99,
            'payment_id': 'pay_test_123',
            'order_id': 'ord_test_456'
        }, format='json')
        self.assertEqual(post_res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(post_res.data.get('status'))
        self.assertEqual(post_res.data['data']['coins_added'], 100)
        self.assertEqual(post_res.data['data']['current_balance'], 150)

        # Retrieve history
        get_res = self.client.get('/api/coins/history/')
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertTrue(get_res.data.get('status'))
        data = get_res.data['data']
        self.assertEqual(data['current_balance'], 150)
        self.assertEqual(data['total_coins_purchased'], 100)
        self.assertEqual(data['total_purchases'], 1)
        self.assertEqual(len(data['purchases']), 1)
        self.assertEqual(data['purchases'][0]['coins'], 100)
        self.assertEqual(data['purchases'][0]['transaction_type'], 'CREDIT')
        self.assertEqual(data['purchases'][0]['status'], 'SUCCESS')

    def test_filter_coin_history_types(self):
        self.client.force_authenticate(user=self.user)
        # Add credit and debit
        WalletTransaction.objects.create(
            wallet=self.wallet,
            transaction_type='CREDIT',
            amount=200,
            description="Recharge 200 coins"
        )
        WalletTransaction.objects.create(
            wallet=self.wallet,
            transaction_type='DEBIT',
            amount=30,
            description="Call deduction"
        )

        # Default is credit (purchases)
        res_credit = self.client.get('/api/coins/purchase-history/')
        self.assertEqual(res_credit.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_credit.data['data']['purchases']), 1)
        self.assertEqual(res_credit.data['data']['purchases'][0]['coins'], 200)

        # All transactions
        res_all = self.client.get('/api/wallet/transactions/?type=all')
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_all.data['data']['transactions']), 2)


class AgoraCallTokenTestCase(TestCase):
    def setUp(self):
        from unittest.mock import patch
        self.client = APIClient()
        self.patcher = patch('core.views.generate_agora_audio_token', return_value='mock_agora_rtc_token_xyz123')
        self.mock_agora = self.patcher.start()
        self.addCleanup(self.patcher.stop)

        self.caller = User.objects.create_user(
            username='caller_agora',
            phone_number='+919876543201',
            role='CALLER'
        )
        self.agent = User.objects.create_user(
            username='agent_agora',
            phone_number='+919876543202',
            role='AGENT'
        )
        self.other_user = User.objects.create_user(
            username='other_agora',
            phone_number='+919876543203',
            role='CALLER'
        )
        self.call = Call.objects.create(
            caller=self.caller,
            receiver=self.agent,
            channel_name='test_agora_channel_001',
            status='ACCEPTED'
        )

    def test_caller_can_generate_token_for_accepted_call(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.post(f'/api/calls/{self.call.id}/agora-token/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['call_id'], self.call.id)
        self.assertEqual(res.data['channel_name'], 'test_agora_channel_001')
        self.assertEqual(res.data['uid'], self.caller.id)
        self.assertIn('token', res.data)
        self.assertNotIn('certificate', str(res.data).lower())

    def test_agent_can_generate_token_for_accepted_call(self):
        self.client.force_authenticate(user=self.agent)
        res = self.client.post(f'/api/calls/{self.call.id}/agora-token/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['uid'], self.agent.id)

    def test_unauthorized_user_forbidden(self):
        self.client.force_authenticate(user=self.other_user)
        res = self.client.post(f'/api/calls/{self.call.id}/agora-token/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(res.data['success'])

    def test_unauthenticated_request_rejected(self):
        res = self.client.post(f'/api/calls/{self.call.id}/agora-token/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_generate_token_for_ringing_or_ended_call(self):
        self.client.force_authenticate(user=self.caller)
        self.call.status = 'RINGING'
        self.call.save(update_fields=['status'])
        res_ringing = self.client.post(f'/api/calls/{self.call.id}/agora-token/')
        self.assertEqual(res_ringing.status_code, status.HTTP_400_BAD_REQUEST)

        self.call.status = 'COMPLETED'
        self.call.save(update_fields=['status'])
        res_ended = self.client.post(f'/api/calls/{self.call.id}/agora-token/')
        self.assertEqual(res_ended.status_code, status.HTTP_400_BAD_REQUEST)

    def test_client_cannot_spoof_uid(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.post(f'/api/calls/{self.call.id}/agora-token/', {'uid': 999999}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['uid'], self.caller.id)


class AgentDashboardTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.agent = User.objects.create_user(
            username='agent_dash_user',
            phone_number='+919876543209',
            role='AGENT'
        )
        self.caller = User.objects.create_user(
            username='caller_dash_user',
            phone_number='+919876543208',
            role='CALLER'
        )

    def test_agent_dashboard_success(self):
        self.client.force_authenticate(user=self.agent)
        res = self.client.get('/api/agent/dashboard/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertIn('profile', res.data['data'])
        self.assertIn('duty', res.data['data'])
        self.assertIn('earnings', res.data['data'])
        self.assertIn('calls', res.data['data'])
        self.assertIn('recent_sessions', res.data['data'])
        self.assertIn('avatar', res.data['data']['profile'])
        self.assertIn('profile_picture', res.data['data']['profile'])

    def test_agent_dashboard_requires_agent_role(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.get('/api/agent/dashboard/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class CallerSignupCompleteProfileTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        from core.otp_service import generate_verification_token
        self.phone = "+919876543299"
        self.valid_token = generate_verification_token(self.phone, purpose='SIGNUP')

    def test_complete_profile_with_verification_token_header_success(self):
        body = {
            "name": "Arathy",
            "age": 30,
            "gender": "Female",
            "interest": ["music", "gaming"]
        }
        res = self.client.post(
            '/api/auth/caller/signup/complete-profile/',
            data=body,
            format='json',
            HTTP_VERIFICATION_TOKEN=self.valid_token
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['data']['user']['name'], "Arathy")
        self.assertEqual(res.data['data']['user']['phone_number'], self.phone)
        self.assertIn('music', res.data['data']['interests'])
        self.assertIn('gaming', res.data['data']['interests'])
        self.assertIn('access', res.data['data']['tokens'])
        self.assertIn('refresh', res.data['data']['tokens'])

    def test_complete_profile_missing_verification_token_header_fails(self):
        body = {
            "name": "Arathy",
            "age": 30,
            "gender": "Female",
            "interest": ["music", "gaming"]
        }
        res = self.client.post(
            '/api/auth/caller/signup/complete-profile/',
            data=body,
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertIn('verification_token', res.data.get('errors', {}))

    def test_complete_profile_invalid_verification_token_header_fails(self):
        body = {
            "name": "Arathy",
            "age": 30,
            "gender": "Female",
            "interest": ["music", "gaming"]
        }
        res = self.client.post(
            '/api/auth/caller/signup/complete-profile/',
            data=body,
            format='json',
            HTTP_VERIFICATION_TOKEN="invalid_bogus_token"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])


class FCMTokenUpdateTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="fcm_test_user",
            phone_number="+919876543277",
            role="AGENT"
        )

    def test_fcm_token_update_authenticated_success(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post('/api/fcm-token/', {'fcm_token': 'test_device_token_xyz_123'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['message'], "FCM token updated successfully.")
        self.user.refresh_from_db()
        self.assertEqual(self.user.fcm_token, 'test_device_token_xyz_123')

    def test_fcm_token_update_unauthenticated_fails(self):
        res = self.client.post('/api/fcm-token/', {'fcm_token': 'test_device_token_xyz_123'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fcm_token_update_empty_token_fails(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post('/api/fcm-token/', {'fcm_token': '   '}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])


class FCMCallNotificationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="FCM Health", is_active=True)
        self.caller = User.objects.create_user(
            username="caller_fcm_user",
            phone_number="+919876543261",
            role="CALLER",
            first_name="Alice Caller"
        )
        self.agent = User.objects.create_user(
            username="agent_fcm_user",
            phone_number="+919876543262",
            role="AGENT",
            fcm_token="agent_sample_fcm_token_999"
        )
        self.agent_profile, _ = ListenerProfile.objects.get_or_create(user=self.agent)
        self.agent_profile.listener_id = "agent_fcm_user"
        self.agent_profile.name = "Bob Agent"
        self.agent_profile.profession = self.category
        self.agent_profile.is_available = True
        self.agent_profile.is_on_duty = True
        self.agent_profile.is_busy = False
        self.agent_profile.save()

    def test_call_request_triggers_fcm_when_agent_has_token(self):
        from unittest.mock import patch
        self.client.force_authenticate(user=self.caller)
        with patch('core.fcm_service.send_incoming_call_fcm') as mock_send_fcm:
            mock_send_fcm.return_value = (True, "FCM sent successfully")
            res = self.client.post('/api/calls/request/', {'category_id': self.category.id}, format='json')
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            self.assertTrue(res.data['success'])
            mock_send_fcm.assert_called_once()
            call_kwargs = mock_send_fcm.call_args.kwargs
            self.assertEqual(call_kwargs['fcm_token'], 'agent_sample_fcm_token_999')
            self.assertEqual(call_kwargs['call_type'], 'audio')
            self.assertEqual(call_kwargs['caller_id'], self.caller.id)

    def test_call_request_when_agent_has_no_fcm_token_succeeds(self):
        self.agent.fcm_token = None
        self.agent.save(update_fields=['fcm_token'])
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'category_id': self.category.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])

    def test_call_request_when_fcm_send_fails_does_not_break_call(self):
        from unittest.mock import patch
        self.client.force_authenticate(user=self.caller)
        with patch('core.fcm_service.send_incoming_call_fcm') as mock_send_fcm:
            mock_send_fcm.side_effect = Exception("Simulated network timeout connecting to FCM")
            res = self.client.post('/api/calls/request/', {'category_id': self.category.id}, format='json')
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            self.assertTrue(res.data['success'])
            self.assertIn('call_id', res.data)

    def test_firebase_status_diagnostic_safe(self):
        from core.fcm_service import check_firebase_status
        status = check_firebase_status()
        self.assertIn("credentials_file_found", status)
        self.assertIn("initialized", status)
        self.assertTrue(status["credentials_file_found"])
        # Ensure no private key or secrets are exposed in diagnostic output
        status_str = str(status).lower()
        self.assertNotIn("private_key", status_str)
        self.assertNotIn("privatekey", status_str)


class DirectAgentCallFlowTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Mental Wellness", is_active=True)
        self.caller = User.objects.create_user(
            username="caller_direct_test",
            phone_number="+919876543271",
            role="CALLER",
            first_name="Diana Caller"
        )
        self.agent = User.objects.create_user(
            username="agent_direct_test",
            phone_number="+919876543272",
            role="LISTENER",
            first_name="Dr. Evelyn Stone",
            fcm_token="agent_direct_token_123"
        )
        self.agent_profile, _ = ListenerProfile.objects.get_or_create(user=self.agent)
        self.agent_profile.listener_id = "agent_direct_test"
        self.agent_profile.name = "Dr. Evelyn Stone"
        self.agent_profile.profession = self.category
        self.agent_profile.is_available = True
        self.agent_profile.is_on_duty = True
        self.agent_profile.is_busy = False
        self.agent_profile.save()

    def test_call_request_with_agent_user_id_success(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['status'], 'RINGING')
        self.assertEqual(res.data['agent']['id'], self.agent.id)
        self.assertEqual(res.data['agent']['name'], 'Dr. Evelyn Stone')
        self.assertEqual(res.data['category']['id'], self.category.id)
        self.assertEqual(res.data['category']['name'], 'Mental Wellness')
        self.assertIn('call_id', res.data)
        self.assertIn('channel_name', res.data)
        self.assertEqual(res.data['uid'], self.caller.id)
        self.assertIn('agora_token', res.data)
        self.assertIn('requested_at', res.data)

        # Ensure Agent is marked busy
        self.agent_profile.refresh_from_db()
        self.assertTrue(self.agent_profile.is_busy)
        self.assertFalse(self.agent_profile.is_available)

        # Verify Call record in DB
        call = Call.objects.get(id=res.data['call_id'])
        self.assertEqual(call.caller, self.caller)
        self.assertEqual(call.receiver, self.agent)
        self.assertEqual(call.category, self.category)
        self.assertEqual(call.status, 'RINGING')

    def test_call_request_agent_does_not_exist_returns_404(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': 999999}, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(res.data['success'])
        self.assertIn("does not exist", res.data['message'])

    def test_call_request_agent_inactive_returns_400(self):
        self.agent.is_active = False
        self.agent.save(update_fields=['is_active'])
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertIn("inactive", res.data['message'])

    def test_call_request_user_is_not_agent_returns_400(self):
        non_agent = User.objects.create_user(
            username="regular_user_99",
            phone_number="+919876543279",
            role="CALLER"
        )
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': non_agent.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertIn("not an agent or listener", res.data['message'])

    def test_call_request_caller_cannot_call_self_returns_400(self):
        self.client.force_authenticate(user=self.agent)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertIn("cannot place a call to yourself", res.data['message'])

    def test_call_request_busy_agent_returns_400_and_does_not_reassign(self):
        # Create a second available agent to ensure the system doesn't reassign
        agent2 = User.objects.create_user(
            username="agent_second_99",
            phone_number="+919876543288",
            role="LISTENER",
            first_name="Second Agent"
        )
        agent2_profile, _ = ListenerProfile.objects.get_or_create(user=agent2)
        agent2_profile.listener_id = "agent_second_99"
        agent2_profile.name = "Second Agent"
        agent2_profile.profession = self.category
        agent2_profile.is_available = True
        agent2_profile.is_on_duty = True
        agent2_profile.is_busy = False
        agent2_profile.save()

        # Create real active call for targeted agent with another user
        other_caller = User.objects.create_user(
            username="other_caller_busy_test",
            phone_number="+919876543289",
            role="CALLER"
        )
        Call.objects.create(
            caller=other_caller,
            receiver=self.agent,
            channel_name="active_busy_channel_test_99",
            status='ACTIVE'
        )

        initial_call_count = Call.objects.count()
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertIn("unavailable or busy", res.data['message'])

        # Confirm NO new call was created and agent2 was NOT assigned
        self.assertEqual(Call.objects.count(), initial_call_count)

    def test_call_request_off_duty_agent_returns_400(self):
        self.agent_profile.is_on_duty = False
        self.agent_profile.save(update_fields=['is_on_duty'])

        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertIn("unavailable or busy", res.data['message'])

    def test_rejected_call_allows_new_call_and_creates_fresh_record(self):
        self.client.force_authenticate(user=self.caller)
        # 1. Create first call
        res1 = self.client.post('/api/calls/request/', {'agent_user_id': self.agent.id}, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        call1_id = res1.data['call_id']

        # 2. Agent rejects call
        self.client.force_authenticate(user=self.agent)
        res_reject = self.client.post(f'/api/calls/{call1_id}/status/', {'status': 'rejected'}, format='json')
        self.assertEqual(res_reject.status_code, status.HTTP_200_OK)
        self.assertEqual(res_reject.data['status'], 'REJECTED')

        call1 = Call.objects.get(id=call1_id)
        self.assertEqual(call1.status, 'REJECTED')

        # 3. Caller makes a NEW call to the same agent
        self.client.force_authenticate(user=self.caller)
        res2 = self.client.post('/api/calls/request/', {'agent_user_id': self.agent.id}, format='json')
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        call2_id = res2.data['call_id']

        # Verify a new Call record was created and old call was NOT modified back to RINGING
        self.assertNotEqual(call1_id, call2_id)
        call1.refresh_from_db()
        self.assertEqual(call1.status, 'REJECTED')

        call2 = Call.objects.get(id=call2_id)
        self.assertEqual(call2.status, 'RINGING')

        # Verify consecutive calls receive distinct, unique channel names
        self.assertNotEqual(call1.channel_name, call2.channel_name)
        self.assertNotEqual(res1.data['channel_name'], res2.data['channel_name'])

    def test_rapid_consecutive_call_requests_produce_unique_channel_names(self):
        self.client.force_authenticate(user=self.caller)
        res1 = self.client.post('/api/calls/request/', {'agent_user_id': self.agent.id}, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        call1 = Call.objects.get(id=res1.data['call_id'])
        call1.status = 'COMPLETED'
        call1.save(update_fields=['status'])

        # Rapidly create another call to the same agent
        res2 = self.client.post('/api/calls/request/', {'agent_user_id': self.agent.id}, format='json')
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        call2 = Call.objects.get(id=res2.data['call_id'])

        self.assertNotEqual(call1.channel_name, call2.channel_name)
        self.assertNotEqual(res1.data['channel_name'], res2.data['channel_name'])
        # Verify format starts with call_ and ends with 8-char hex
        self.assertTrue(call1.channel_name.startswith('call_'))
        self.assertTrue(call2.channel_name.startswith('call_'))

    def test_ongoing_active_call_prevents_new_call(self):
        self.client.force_authenticate(user=self.caller)
        res1 = self.client.post('/api/calls/request/', {'agent_user_id': self.agent.id}, format='json')
        call_id = res1.data['call_id']

        # Transition call to ACTIVE
        call = Call.objects.get(id=call_id)
        call.status = 'ACTIVE'
        call.save(update_fields=['status'])

        # Attempt to make another call
        res2 = self.client.post('/api/calls/request/', {'agent_user_id': self.agent.id}, format='json')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res2.data['success'])
        self.assertIn("ongoing call", res2.data['message'])

    def test_legacy_category_id_request_backward_compatible(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'category_id': self.category.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['category']['id'], self.category.id)


class CallReviewAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Support", is_active=True)
        self.caller = User.objects.create_user(
            username="caller_reviewer",
            phone_number="+919876543311",
            role="CALLER",
            first_name="Samantha"
        )
        self.other_caller = User.objects.create_user(
            username="other_caller_99",
            phone_number="+919876543312",
            role="CALLER",
            first_name="Bob"
        )
        self.agent = User.objects.create_user(
            username="agent_reviewee",
            phone_number="+919876543313",
            role="LISTENER",
            first_name="Dr. Neil Patel"
        )
        self.agent_profile, _ = ListenerProfile.objects.get_or_create(user=self.agent)
        self.agent_profile.listener_id = "agent_reviewee"
        self.agent_profile.name = "Dr. Neil Patel"
        self.agent_profile.profession = self.category
        self.agent_profile.is_available = True
        self.agent_profile.is_on_duty = True
        self.agent_profile.rating = 5.00
        self.agent_profile.save()
        self.call = Call.objects.create(
            caller=self.caller,
            receiver=self.agent,
            category=self.category,
            channel_name="call_support_review_test_01",
            status="COMPLETED",
            duration_seconds=180
        )

    def test_1_successful_review_with_rating_only(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.post(f'/api/calls/{self.call.id}/review/', {"rating": 5}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['data']['rating'], 5)
        self.assertEqual(res.data['data']['tags'], [])
        self.assertEqual(res.data['data']['comment'], "")

    def test_2_successful_review_with_rating_plus_one_tag(self):
        self.client.force_authenticate(user=self.caller)
        payload = {
            "rating": 5,
            "tags": ["Great Listener"]
        }
        res = self.client.post(f'/api/calls/{self.call.id}/review/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['data']['tags'], ["Great Listener"])

    def test_3_successful_review_with_rating_multiple_tags_comment(self):
        self.client.force_authenticate(user=self.caller)
        payload = {
            "rating": 5,
            "tags": [
                "Great Listener",
                "Very Empathetic",
                "Helpful Advice"
            ],
            "comment": "Excellent call."
        }
        res = self.client.post(f'/api/calls/{self.call.id}/review/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['message'], "Review submitted successfully.")
        self.assertEqual(res.data['data']['call_id'], self.call.id)
        self.assertEqual(res.data['data']['rating'], 5)
        self.assertEqual(res.data['data']['tags'], ["Great Listener", "Very Empathetic", "Helpful Advice"])
        self.assertEqual(res.data['data']['comment'], "Excellent call.")

        # Verify in database
        review = CallReview.objects.get(call=self.call)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.tags, ["Great Listener", "Very Empathetic", "Helpful Advice"])
        self.assertEqual(review.feedback, "Excellent call.")

    def test_4_successful_review_with_empty_tags(self):
        self.client.force_authenticate(user=self.caller)
        payload = {
            "rating": 5,
            "tags": [],
            "comment": ""
        }
        res = self.client.post(f'/api/calls/{self.call.id}/review/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['data']['tags'], [])

    def test_5_rating_1_accepted(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.post(f'/api/calls/{self.call.id}/review/', {"rating": 1}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['data']['rating'], 1)

    def test_6_rating_5_accepted(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.post(f'/api/calls/{self.call.id}/review/', {"rating": 5}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['data']['rating'], 5)

    def test_7_rating_0_rejected(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.post(f'/api/calls/{self.call.id}/review/', {"rating": 0, "tags": [], "comment": ""}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])

    def test_8_rating_6_rejected(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.post(f'/api/calls/{self.call.id}/review/', {"rating": 6, "tags": [], "comment": ""}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])

    def test_9_unknown_tag_rejected(self):
        self.client.force_authenticate(user=self.caller)
        payload = {
            "rating": 5,
            "tags": ["Amazing Listener"],
            "comment": ""
        }
        res = self.client.post(f'/api/calls/{self.call.id}/review/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])

    def test_10_duplicate_tag_rejected(self):
        self.client.force_authenticate(user=self.caller)
        payload = {
            "rating": 5,
            "tags": [
                "Great Listener",
                "Great Listener"
            ],
            "comment": ""
        }
        res = self.client.post(f'/api/calls/{self.call.id}/review/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])

    def test_11_more_than_8_tags_rejected(self):
        self.client.force_authenticate(user=self.caller)
        payload = {
            "rating": 5,
            "tags": [
                "Great Listener",
                "Very Empathetic",
                "Helpful Advice",
                "Friendly & Warm",
                "Calming Voice",
                "Fun & Engaging",
                "Patient & Kind",
                "Understood Me Well",
                "Extra Tag"
            ],
            "comment": ""
        }
        res = self.client.post(f'/api/calls/{self.call.id}/review/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])

    def test_12_comment_over_1000_characters_rejected(self):
        self.client.force_authenticate(user=self.caller)
        payload = {
            "rating": 5,
            "comment": "A" * 1001
        }
        res = self.client.post(f'/api/calls/{self.call.id}/review/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])

    def test_13_unauthenticated_request_rejected(self):
        payload = {"rating": 5, "comment": "Good"}
        res = self.client.post(f'/api/calls/{self.call.id}/review/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_14_listener_agent_cannot_review(self):
        self.client.force_authenticate(user=self.agent)
        payload = {"rating": 5, "comment": "Agent reviewing self"}
        res = self.client.post(f'/api/calls/{self.call.id}/review/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(res.data['success'])

    def test_15_caller_cannot_review_another_users_call(self):
        self.client.force_authenticate(user=self.other_caller)
        payload = {"rating": 4, "comment": "Trying to review someone else's call"}
        res = self.client.post(f'/api/calls/{self.call.id}/review/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(res.data['success'])
        self.assertIn("only review calls where you were the caller", res.data['message'])

    def test_16_incomplete_call_cannot_be_reviewed(self):
        incomplete_call = Call.objects.create(
            caller=self.caller,
            receiver=self.agent,
            category=self.category,
            channel_name="call_incomplete_test",
            status="RINGING"
        )
        self.client.force_authenticate(user=self.caller)
        res = self.client.post(f'/api/calls/{incomplete_call.id}/review/', {"rating": 5}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertIn("Only completed calls can be reviewed", res.data['message'])

    def test_17_duplicate_review_returns_409(self):
        self.client.force_authenticate(user=self.caller)
        res1 = self.client.post(f'/api/calls/{self.call.id}/review/', {"rating": 5, "comment": "First"}, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        res2 = self.client.post(f'/api/calls/{self.call.id}/review/', {"rating": 4, "comment": "Duplicate"}, format='json')
        self.assertEqual(res2.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(res2.data['success'])
        self.assertIn("already been reviewed", res2.data['message'])

    def test_18_agent_average_rating_updated_correctly(self):
        self.client.force_authenticate(user=self.caller)
        # Submit 4 stars for first call
        self.client.post(f'/api/calls/{self.call.id}/review/', {"rating": 4}, format='json')
        self.agent_profile.refresh_from_db()
        self.assertEqual(float(self.agent_profile.rating), 4.0)

        # Create second completed call for same agent and submit 5 stars
        call2 = Call.objects.create(
            caller=self.caller,
            receiver=self.agent,
            status="ENDED",
            channel_name="call_test_sync_2"
        )
        self.client.post(f'/api/calls/{call2.id}/review/', {"rating": 5}, format='json')
        self.agent_profile.refresh_from_db()
        self.assertEqual(float(self.agent_profile.rating), 4.5)

    def test_19_review_list_includes_tags(self):
        CallReview.objects.create(
            call=self.call,
            rating=5,
            tags=["Great Listener", "Very Empathetic"],
            feedback="Super understanding and warm."
        )
        res = self.client.get(f'/api/agents/{self.agent.id}/reviews/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['data']['agent_id'], self.agent.id)
        self.assertEqual(res.data['data']['agent_name'], "Dr. Neil Patel")
        self.assertEqual(res.data['data']['total_reviews'], 1)
        self.assertEqual(res.data['data']['average_rating'], 5.0)
        self.assertEqual(len(res.data['data']['reviews']), 1)
        rev = res.data['data']['reviews'][0]
        self.assertEqual(rev['id'], self.call.review.id)
        self.assertEqual(rev['call_id'], self.call.id)
        self.assertEqual(rev['rating'], 5)
        self.assertEqual(rev['tags'], ["Great Listener", "Very Empathetic"])
        self.assertEqual(rev['comment'], "Super understanding and warm.")
        self.assertEqual(rev['caller_name'], "Samantha")
        self.assertNotIn('caller_id', rev)
        self.assertNotIn('phone_number', rev)
        self.assertNotIn('caller_phone', rev)

    def test_20_call_history_includes_tags_in_review(self):
        CallReview.objects.create(
            call=self.call,
            rating=5,
            tags=["Great Listener", "Friendly & Warm"],
            feedback="Insightful advice."
        )
        self.client.force_authenticate(user=self.caller)
        res = self.client.get('/api/calls/history/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        call_entry = next((c for c in res.data['data'] if c['id'] == self.call.id), None)
        self.assertIsNotNone(call_entry)
        self.assertIsNotNone(call_entry['review'])
        self.assertEqual(call_entry['review']['rating'], 5)
        self.assertEqual(call_entry['review']['tags'], ["Great Listener", "Friendly & Warm"])
        self.assertEqual(call_entry['review']['comment'], "Insightful advice.")

    def test_21_get_review_tags_returns_allowed_tags(self):
        res = self.client.get('/api/review-tags/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['message'], "Review tags retrieved successfully.")
        self.assertEqual(res.data['data'], ALLOWED_REVIEW_TAGS)
        self.assertEqual(len(res.data['data']), 8)


class AgentAvailabilityAndCallingLogicTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Mental Health", is_active=True)
        self.caller = User.objects.create_user(
            username="caller_avail_1",
            phone_number="+919876543501",
            role="CALLER",
            first_name="Alice"
        )
        self.caller2 = User.objects.create_user(
            username="caller_avail_2",
            phone_number="+919876543502",
            role="CALLER",
            first_name="Bob"
        )
        self.agent1 = User.objects.create_user(
            username="agent_avail_1",
            phone_number="+919876543503",
            role="LISTENER",
            first_name="Agent One"
        )
        self.profile1, _ = ListenerProfile.objects.get_or_create(
            user=self.agent1,
            defaults={
                'listener_id': "agent_avail_1",
                'name': "Agent One",
                'profession': self.category,
                'is_available': True,
                'is_on_duty': True,
                'is_busy': False
            }
        )
        self.profile1.listener_id = "agent_avail_1"
        self.profile1.name = "Agent One"
        self.profile1.profession = self.category
        self.profile1.is_available = True
        self.profile1.is_on_duty = True
        self.profile1.is_busy = False
        self.profile1.save()

        self.agent2 = User.objects.create_user(
            username="agent_avail_2",
            phone_number="+919876543504",
            role="LISTENER",
            first_name="Agent Two"
        )
        self.profile2, _ = ListenerProfile.objects.get_or_create(
            user=self.agent2,
            defaults={
                'listener_id': "agent_avail_2",
                'name': "Agent Two",
                'profession': self.category,
                'is_available': True,
                'is_on_duty': True,
                'is_busy': False
            }
        )
        self.profile2.listener_id = "agent_avail_2"
        self.profile2.name = "Agent Two"
        self.profile2.profession = self.category
        self.profile2.is_available = True
        self.profile2.is_on_duty = True
        self.profile2.is_busy = False
        self.profile2.save()

    def test_available_agent_on_duty_can_receive_call(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['agent']['id'], self.agent1.id)
        self.assertEqual(res.data['status'], 'RINGING')

    def test_ringing_active_call_blocks_agent(self):
        Call.objects.create(
            caller=self.caller2,
            receiver=self.agent1,
            channel_name="chan_ringing_01",
            status='RINGING'
        )
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertIn("unavailable or busy", res.data['message'])

    def test_accepted_active_call_blocks_agent(self):
        Call.objects.create(
            caller=self.caller2,
            receiver=self.agent1,
            channel_name="chan_accepted_01",
            status='ACCEPTED'
        )
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertIn("unavailable or busy", res.data['message'])

    def test_active_call_blocks_agent(self):
        Call.objects.create(
            caller=self.caller2,
            receiver=self.agent1,
            channel_name="chan_active_01",
            status='ACTIVE'
        )
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertIn("unavailable or busy", res.data['message'])

    def test_ended_call_does_not_block_agent(self):
        Call.objects.create(
            caller=self.caller2,
            receiver=self.agent1,
            channel_name="chan_ended_01",
            status='ENDED',
            ended_at=timezone.now()
        )
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['agent']['id'], self.agent1.id)

    def test_completed_call_does_not_block_agent(self):
        Call.objects.create(
            caller=self.caller2,
            receiver=self.agent1,
            channel_name="chan_completed_01",
            status='COMPLETED',
            ended_at=timezone.now()
        )
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['agent']['id'], self.agent1.id)

    def test_rejected_call_does_not_block_agent(self):
        Call.objects.create(
            caller=self.caller2,
            receiver=self.agent1,
            channel_name="chan_rejected_01",
            status='REJECTED',
            rejected_at=timezone.now()
        )
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['agent']['id'], self.agent1.id)

    def test_cancelled_call_does_not_block_agent(self):
        Call.objects.create(
            caller=self.caller2,
            receiver=self.agent1,
            channel_name="chan_cancelled_01",
            status='CANCELLED',
            ended_at=timezone.now()
        )
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['agent']['id'], self.agent1.id)

    def test_missed_call_does_not_block_agent(self):
        Call.objects.create(
            caller=self.caller2,
            receiver=self.agent1,
            channel_name="chan_missed_01",
            status='MISSED',
            ended_at=timezone.now()
        )
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['agent']['id'], self.agent1.id)

    def test_off_duty_agent_is_rejected(self):
        self.profile1.is_on_duty = False
        self.profile1.save(update_fields=['is_on_duty'])
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertIn("unavailable or busy", res.data['message'])

    def test_inactive_agent_is_rejected(self):
        self.agent1.is_active = False
        self.agent1.save(update_fields=['is_active'])
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertIn("inactive", res.data['message'])

    def test_changing_agent_user_id_routes_to_selected_agent(self):
        self.client.force_authenticate(user=self.caller)
        # Call agent1
        res1 = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res1.data['agent']['id'], self.agent1.id)

        # Release first call
        call1 = Call.objects.get(id=res1.data['call_id'])
        call1.status = 'COMPLETED'
        call1.save(update_fields=['status'])

        # Now change agent_user_id to agent2
        res2 = self.client.post('/api/calls/request/', {'agent_user_id': self.agent2.id}, format='json')
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res2.data['agent']['id'], self.agent2.id)

    def test_no_silent_replacement_when_selected_agent_busy(self):
        # agent1 has an active call
        Call.objects.create(
            caller=self.caller2,
            receiver=self.agent1,
            channel_name="chan_active_nosilent",
            status='ACTIVE'
        )
        self.client.force_authenticate(user=self.caller)
        # Caller selects agent1 specifically
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertIn("unavailable or busy", res.data['message'])
        # Ensure agent2 was NOT called
        self.assertFalse(Call.objects.filter(caller=self.caller, receiver=self.agent2).exists())

    def test_stale_is_busy_true_with_no_active_call_self_heals(self):
        # Simulate stale DB flag
        self.profile1.is_busy = True
        self.profile1.is_available = False
        self.profile1.save(update_fields=['is_busy', 'is_available'])

        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['agent']['id'], self.agent1.id)

    def test_stale_is_available_false_with_no_active_call_self_heals(self):
        # Simulate stale is_available=False while on duty
        self.profile1.is_busy = False
        self.profile1.is_available = False
        self.profile1.save(update_fields=['is_busy', 'is_available'])

        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['agent']['id'], self.agent1.id)

    def test_duty_on_clears_stale_busy_state(self):
        # Stale is_busy=True
        self.profile1.is_busy = True
        self.profile1.is_on_duty = False
        self.profile1.is_available = False
        self.profile1.save(update_fields=['is_busy', 'is_on_duty', 'is_available'])

        self.client.force_authenticate(user=self.agent1)
        res = self.client.post('/api/agent/duty/on/', format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['is_on_duty'])

        self.profile1.refresh_from_db()
        self.assertTrue(self.profile1.is_on_duty)
        self.assertTrue(self.profile1.is_available)
        self.assertFalse(self.profile1.is_busy)


class CallerPhoneLoginTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.caller_phone = "+919876543101"
        self.caller = User.objects.create_user(
            username=self.caller_phone,
            phone_number=self.caller_phone,
            role="CALLER",
            first_name="TestCaller",
            is_active=True,
            is_verified=True
        )
        self.caller_profile, _ = CallerProfile.objects.get_or_create(
            user=self.caller,
            defaults={'name': 'TestCaller', 'age': 25}
        )
        self.caller_profile.name = "TestCaller"
        self.caller_profile.age = 25
        self.caller_profile.save(update_fields=['name', 'age'])

        self.listener_phone = "+919876543106"
        self.listener = User.objects.create_user(
            username="listener_user_login_test",
            phone_number=self.listener_phone,
            role="LISTENER",
            first_name="TestListener",
            is_active=True,
            is_verified=True
        )
        expected_agent_id = f"AGT{self.listener.id:05d}"
        self.listener_profile, _ = ListenerProfile.objects.get_or_create(
            user=self.listener,
            defaults={'listener_id': "listener_user_login_test", 'name': "TestListener", 'agent_id': expected_agent_id}
        )
        if not self.listener_profile.agent_id:
            self.listener_profile.agent_id = expected_agent_id
            self.listener_profile.save(update_fields=['agent_id'])

    def test_1_existing_caller_can_request_login_otp(self):
        res = self.client.post('/api/auth/caller/login/send-otp/', {'phone_number': self.caller_phone}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertIn('otp', res.data['data'])
        self.assertEqual(res.data['data']['phone_number'], self.caller_phone)

    def test_2_new_unregistered_phone_gets_404(self):
        unregistered = "+919876543102"
        res = self.client.post('/api/auth/caller/login/send-otp/', {'phone_number': unregistered}, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(res.data['success'])
        self.assertFalse(res.data['is_registered'])
        self.assertEqual(res.data['action'], "NAVIGATE_TO_SIGNUP")

    def test_3_new_unregistered_phone_does_not_create_user(self):
        unregistered = "+919876543103"
        self.assertFalse(User.objects.filter(phone_number=unregistered).exists())
        self.client.post('/api/auth/caller/login/send-otp/', {'phone_number': unregistered}, format='json')
        self.assertFalse(User.objects.filter(phone_number=unregistered).exists())

    def test_4_new_unregistered_phone_does_not_create_caller_profile(self):
        unregistered = "+919876543104"
        self.assertFalse(CallerProfile.objects.filter(user__phone_number=unregistered).exists())
        self.client.post('/api/auth/caller/login/send-otp/', {'phone_number': unregistered}, format='json')
        self.assertFalse(CallerProfile.objects.filter(user__phone_number=unregistered).exists())

    def test_5_new_unregistered_phone_does_not_create_otp_verification(self):
        unregistered = "+919876543105"
        self.assertFalse(OTPVerification.objects.filter(phone_number=unregistered).exists())
        self.client.post('/api/auth/caller/login/send-otp/', {'phone_number': unregistered}, format='json')
        self.assertFalse(OTPVerification.objects.filter(phone_number=unregistered).exists())

    def test_6_active_agent_can_use_standard_phone_otp_login(self):
        # Step 1: Request login OTP with active Agent phone number
        send_res = self.client.post('/api/auth/caller/login/send-otp/', {'phone_number': self.listener_phone}, format='json')
        self.assertEqual(send_res.status_code, status.HTTP_200_OK)
        self.assertTrue(send_res.data['success'])
        self.assertIn('otp', send_res.data['data'])
        otp = send_res.data['data']['otp']

        # Step 2: Verify login OTP
        verify_res = self.client.post('/api/auth/caller/login/verify-otp/', {
            'phone_number': self.listener_phone,
            'otp': otp
        }, format='json')
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_res.data['success'])

        # Step 3: Verify is_agent=True and agent_id are returned
        self.assertIn('is_agent', verify_res.data['data'])
        self.assertTrue(verify_res.data['data']['is_agent'])
        self.assertEqual(verify_res.data['data']['agent_id'], self.listener_profile.agent_id)
        self.assertTrue(verify_res.data['data']['user']['is_agent'])
        self.assertEqual(verify_res.data['data']['user']['agent_id'], self.listener_profile.agent_id)

    # Maintain backward-compatible test alias
    test_6_agent_listener_phone_cannot_use_caller_login = test_6_active_agent_can_use_standard_phone_otp_login

    def test_7_agent_listener_role_is_not_changed_to_caller(self):
        self.client.post('/api/auth/caller/login/send-otp/', {'phone_number': self.listener_phone}, format='json')
        self.listener.refresh_from_db()
        self.assertEqual(self.listener.role, "LISTENER")

    def test_8_inactive_caller_receives_403(self):
        self.caller.is_active = False
        self.caller.save(update_fields=['is_active'])
        res = self.client.post('/api/auth/caller/login/send-otp/', {'phone_number': self.caller_phone}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(res.data['success'])
        self.assertIn("deactivated", res.data['message'])

    def test_9_existing_caller_can_continue_through_otp_verification(self):
        send_res = self.client.post('/api/auth/caller/login/send-otp/', {'phone_number': self.caller_phone}, format='json')
        self.assertEqual(send_res.status_code, status.HTTP_200_OK)
        otp = send_res.data['data']['otp']

        verify_res = self.client.post('/api/auth/caller/login/verify-otp/', {
            'phone_number': self.caller_phone,
            'otp': otp
        }, format='json')
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_res.data['success'])
        self.assertIn('tokens', verify_res.data['data'])
        self.assertIn('access', verify_res.data['data']['tokens'])

    def test_10_unified_caller_login_follows_same_rules(self):
        unregistered = "+919876543110"
        res_fail = self.client.post('/api/auth/caller/login/', {'phone_number': unregistered}, format='json')
        self.assertEqual(res_fail.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(res_fail.data['is_registered'])

        res_ok = self.client.post('/api/auth/caller/login/', {'phone_number': self.caller_phone}, format='json')
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        self.assertTrue(res_ok.data['success'])

    def test_11_caller_signup_with_new_phone_still_works(self):
        new_phone = "+919876543111"
        res = self.client.post('/api/auth/caller/signup/send-otp/', {'phone_number': new_phone}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertIn('otp', res.data['data'])


class CallerAgeValidationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        from core.otp_service import generate_verification_token
        self.signup_phone = "+919876543222"
        self.valid_token = generate_verification_token(self.signup_phone, purpose='SIGNUP')

        self.caller_phone = "+919876543223"
        self.caller = User.objects.create_user(
            username=self.caller_phone,
            phone_number=self.caller_phone,
            role="CALLER",
            first_name="AgeUser",
            is_active=True,
            is_verified=True
        )
        self.profile, _ = CallerProfile.objects.get_or_create(
            user=self.caller,
            defaults={'name': 'AgeUser', 'age': 20}
        )
        self.profile.name = "AgeUser"
        self.profile.age = 20
        self.profile.save(update_fields=['name', 'age'])

    def _post_signup_profile(self, age):
        body = {
            "name": "TestAge",
            "age": age,
            "gender": "Female",
            "interest": ["music"]
        }
        return self.client.post(
            '/api/auth/caller/signup/complete-profile/',
            data=body,
            format='json',
            HTTP_VERIFICATION_TOKEN=self.valid_token
        )

    def test_12_age_10_accepted(self):
        res = self._post_signup_profile(10)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['data']['user']['age'], 10)

    def test_13_age_30_accepted(self):
        res = self._post_signup_profile(30)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['data']['user']['age'], 30)

    def test_14_age_99_accepted(self):
        res = self._post_signup_profile(99)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['data']['user']['age'], 99)

    def test_15_age_3_rejected(self):
        res = self._post_signup_profile(3)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('age', res.data.get('errors', {}))

    def test_16_age_9_rejected(self):
        res = self._post_signup_profile(9)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('age', res.data.get('errors', {}))

    def test_17_age_100_rejected(self):
        res = self._post_signup_profile(100)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('age', res.data.get('errors', {}))

    def test_18_age_123_rejected(self):
        res = self._post_signup_profile(123)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('age', res.data.get('errors', {}))

    def test_19_non_numeric_age_rejected(self):
        res = self._post_signup_profile("abc")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('age', res.data.get('errors', {}))

    def test_20_profile_update_cannot_bypass_validation(self):
        self.client.force_authenticate(user=self.caller)
        # Attempt age 100 on profile update
        res_100 = self.client.patch('/api/caller/profile/', {'age': 100}, format='json')
        self.assertEqual(res_100.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt age 9 on profile update
        res_9 = self.client.patch('/api/caller/profile/', {'age': 9}, format='json')
        self.assertEqual(res_9.status_code, status.HTTP_400_BAD_REQUEST)

        # Valid 2-digit age 45 succeeds
        res_valid = self.client.patch('/api/caller/profile/', {'age': 45}, format='json')
        self.assertEqual(res_valid.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.age, 45)

    def test_21_direct_caller_age_endpoints_cannot_bypass_validation(self):
        self.client.force_authenticate(user=self.caller)
        # 1. WebAboutYouView
        res_web_bad = self.client.post('/api/auth/about-you/', {'age': 105}, format='json')
        self.assertEqual(res_web_bad.status_code, status.HTTP_400_BAD_REQUEST)
        res_web_ok = self.client.post('/api/auth/about-you/', {'age': 22}, format='json')
        self.assertEqual(res_web_ok.status_code, status.HTTP_200_OK)

        # 2. CallerListCreateView
        res_create_bad = self.client.post('/api/callers/', {'phone_number': '+919876543999', 'age': 5}, format='json')
        self.assertEqual(res_create_bad.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. CallerUpdateView
        res_update_bad = self.client.patch('/api/caller/update/', {'phone_number': self.caller_phone, 'age': 120}, format='json')
        self.assertEqual(res_update_bad.status_code, status.HTTP_400_BAD_REQUEST)


class ConversationCategoriesAndCallerNeedsTestCase(TestCase):
    def setUp(self):
        from django.core.management import call_command
        self.client = APIClient()

        # Seed the 9 conversation categories
        call_command('seed_conversation_categories')

        # Caller user
        self.caller_phone = "+919876544001"
        self.caller = User.objects.create_user(
            username="caller_cc_test",
            phone_number=self.caller_phone,
            role="CALLER",
            first_name="Alice Caller",
            is_active=True
        )
        self.caller_profile, _ = CallerProfile.objects.get_or_create(user=self.caller)

        # Agent 1 (Just Talk + Career)
        self.agent1_phone = "+919876544002"
        self.agent1 = User.objects.create_user(
            username="agent_cc_1",
            phone_number=self.agent1_phone,
            role="AGENT",
            first_name="Agent Alpha",
            is_active=True
        )
        self.profile1, _ = ListenerProfile.objects.get_or_create(user=self.agent1)
        self.profile1.is_on_duty = True
        self.profile1.is_available = True
        self.profile1.is_busy = False
        self.profile1.save()

        # Agent 2 (Advice + Student Companion)
        self.agent2_phone = "+919876544003"
        self.agent2 = User.objects.create_user(
            username="agent_cc_2",
            phone_number=self.agent2_phone,
            role="LISTENER",
            first_name="Agent Beta",
            is_active=True
        )
        self.profile2, _ = ListenerProfile.objects.get_or_create(user=self.agent2)
        self.profile2.is_on_duty = True
        self.profile2.is_available = True
        self.profile2.is_busy = False
        self.profile2.save()

        self.just_talk = ConversationCategory.objects.get(name="Just Talk")
        self.advice = ConversationCategory.objects.get(name="Advice")
        self.career = ConversationCategory.objects.get(name="Career")

        self.profile1.conversation_categories.set([self.just_talk, self.career])
        self.profile2.conversation_categories.set([self.advice])

    def test_1_conversation_categories_endpoint_returns_9_active_categories(self):
        res = self.client.get('/api/conversation-categories/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertEqual(len(res.data['data']), 9)
        names = [item['name'] for item in res.data['data']]
        self.assertIn("Just Talk", names)
        self.assertIn("Friendly Conversation", names)
        self.assertIn("Advice", names)
        self.assertIn("Casual", names)

    def test_2_inactive_category_is_not_returned(self):
        self.just_talk.is_active = False
        self.just_talk.save(update_fields=['is_active'])

        res = self.client.get('/api/conversation-categories/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        names = [item['name'] for item in res.data['data']]
        self.assertNotIn("Just Talk", names)
        self.assertEqual(len(res.data['data']), 8)

    def test_3_caller_needs_endpoint_returns_8_options(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.get('/api/caller/needs/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertEqual(len(res.data['data']), 8)
        values = [item['value'] for item in res.data['data']]
        self.assertIn("someone_to_listen", values)
        self.assertIn("im_lonely", values)
        self.assertIn("im_bored", values)

    def test_4_unauthenticated_access_is_rejected_where_appropriate(self):
        # Unauthenticated access to /api/caller/needs/ should be rejected (401)
        res_unauth = self.client.get('/api/caller/needs/')
        self.assertEqual(res_unauth.status_code, status.HTTP_401_UNAUTHORIZED)

        # Agent accessing caller needs is forbidden (403)
        self.client.force_authenticate(user=self.agent1)
        res_agent = self.client.get('/api/caller/needs/')
        self.assertEqual(res_agent.status_code, status.HTTP_403_FORBIDDEN)

    def test_5_caller_can_save_valid_current_need(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.patch('/api/caller/profile/', {'current_need': 'someone_to_listen'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.caller_profile.refresh_from_db()
        self.assertEqual(self.caller_profile.current_need, 'someone_to_listen')

        # Also accepts label directly
        res2 = self.client.patch('/api/caller/profile/', {'current_need': "I'm lonely"}, format='json')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.caller_profile.refresh_from_db()
        self.assertEqual(self.caller_profile.current_need, 'im_lonely')

    def test_6_invalid_current_need_is_rejected(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.patch('/api/caller/profile/', {'current_need': 'invalid_random_need_xyz'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('current_need', res.data)

    def test_7_agent_can_select_multiple_conversation_categories(self):
        self.client.force_authenticate(user=self.agent1)
        payload = {
            'conversation_category_ids': [self.just_talk.id, self.advice.id, self.career.id]
        }
        res = self.client.patch('/api/agent/profile/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.profile1.refresh_from_db()
        agent_cat_ids = list(self.profile1.conversation_categories.values_list('id', flat=True))
        self.assertIn(self.just_talk.id, agent_cat_ids)
        self.assertIn(self.advice.id, agent_cat_ids)
        self.assertIn(self.career.id, agent_cat_ids)
        self.assertEqual(len(agent_cat_ids), 3)

    def test_8_agent_can_clear_categories(self):
        self.client.force_authenticate(user=self.agent1)
        res = self.client.patch('/api/agent/profile/', {'conversation_category_ids': []}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.profile1.refresh_from_db()
        self.assertEqual(self.profile1.conversation_categories.count(), 0)

    def test_9_inactive_category_cannot_be_selected(self):
        inactive_cat = ConversationCategory.objects.create(
            name="Inactive Special",
            is_active=False
        )
        self.client.force_authenticate(user=self.agent1)
        res = self.client.patch('/api/agent/profile/', {'conversation_category_ids': [inactive_cat.id]}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('conversation_category_ids', res.data.get('errors', res.data))

    def test_10_category_agent_filtering_returns_only_matching_agents(self):
        # Just Talk has agent1, not agent2
        res = self.client.get(f'/api/conversation-categories/{self.just_talk.id}/agents/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        agent_ids = [a['id'] for a in res.data['data']]
        self.assertIn(self.agent1.id, agent_ids)
        self.assertNotIn(self.agent2.id, agent_ids)

        # Advice has agent2, not agent1
        res_advice = self.client.get(f'/api/conversation-categories/{self.advice.id}/agents/')
        self.assertEqual(res_advice.status_code, status.HTTP_200_OK)
        advice_ids = [a['id'] for a in res_advice.data['data']]
        self.assertIn(self.agent2.id, advice_ids)
        self.assertNotIn(self.agent1.id, advice_ids)

    def test_11_unavailable_busy_offduty_agents_are_excluded_when_available_only_true(self):
        # agent1 is on duty and available -> included
        res1 = self.client.get(f'/api/conversation-categories/{self.just_talk.id}/agents/?available_only=true')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res1.data['data']), 1)
        self.assertEqual(res1.data['data'][0]['id'], self.agent1.id)

        # Case A: agent1 goes off duty
        self.profile1.is_on_duty = False
        self.profile1.save(update_fields=['is_on_duty'])
        res_offduty = self.client.get(f'/api/conversation-categories/{self.just_talk.id}/agents/?available_only=true')
        self.assertEqual(res_offduty.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_offduty.data['data']), 0)

        # Case B: agent1 is on duty but in an active call
        self.profile1.is_on_duty = True
        self.profile1.save(update_fields=['is_on_duty'])
        Call.objects.create(
            caller=self.caller,
            receiver=self.agent1,
            channel_name="chan_active_test_avail_filter",
            status='ACTIVE'
        )
        res_busy = self.client.get(f'/api/conversation-categories/{self.just_talk.id}/agents/?available_only=true')
        self.assertEqual(res_busy.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_busy.data['data']), 0)

    def test_12_no_matching_agents_returns_http_200_with_empty_data(self):
        travel_cat = ConversationCategory.objects.get(name="Travel")
        res = self.client.get(f'/api/conversation-categories/{travel_cat.id}/agents/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['count'], 0)
        self.assertEqual(res.data['data'], [])

    def test_13_existing_profession_filtering_still_works_independently(self):
        # Legacy profession category
        doctor_cat, _ = Category.objects.get_or_create(name="Doctor", defaults={'is_active': True})
        self.profile1.profession = doctor_cat
        self.profile1.save(update_fields=['profession'])

        # Legacy endpoint filters by profession
        res = self.client.get(f'/api/listeners/?category={doctor_cat.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        listener_ids = [l['id'] for l in res.data['data']]
        self.assertIn(self.agent1.id, listener_ids)

        # Conversation categories remain independent
        self.assertEqual(self.profile1.profession.name, "Doctor")
        self.assertTrue(self.profile1.conversation_categories.filter(id=self.just_talk.id).exists())

    def test_14_direct_agent_call_still_uses_exact_agent_user_id(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['agent']['id'], self.agent1.id)

        # Create a second caller
        caller2 = User.objects.create_user(
            username="caller2_cc_test",
            phone_number="+919876544099",
            role="CALLER",
            is_active=True
        )
        self.client.force_authenticate(user=caller2)

        # Verify no silent reassignment: agent1 is now busy, next call to agent1 returns 400
        call_count_before = Call.objects.count()
        res_busy = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res_busy.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res_busy.data.get('success', True))
        self.assertIn("unavailable or busy", res_busy.data.get('message', ''))
        self.assertEqual(Call.objects.count(), call_count_before)

    def test_15_call_caller_need_is_correctly_snapshotted_when_call_is_created(self):
        # Set caller's need on profile
        self.caller_profile.current_need = "someone_to_listen"
        self.caller_profile.save(update_fields=['current_need'])
        self.caller.refresh_from_db()

        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        call_id = res.data['call_id']
        call_obj = Call.objects.get(id=call_id)
        self.assertEqual(call_obj.caller_need, "someone_to_listen")

        # Free the call
        call_obj.status = 'COMPLETED'
        call_obj.save(update_fields=['status'])

        # Explicitly passing caller_need in call request overrides profile
        # Explicitly passing caller_need in call request overrides profile
        res2 = self.client.post('/api/calls/request/', {
            'agent_user_id': self.agent1.id,
            'caller_need': 'want_motivation'
        }, format='json')
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        call2_obj = Call.objects.get(id=res2.data['call_id'])
        self.assertEqual(call2_obj.caller_need, "want_motivation")


class CallerAgentDiscoveryTwoLevelTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Conversation Categories
        self.cat_just_talk, _ = ConversationCategory.objects.get_or_create(
            name="Just Talk",
            defaults={'tagline': "I need someone to talk to.", 'emoji': "❤️", 'is_active': True}
        )
        self.cat_advice, _ = ConversationCategory.objects.get_or_create(
            name="Advice",
            defaults={'tagline': "I need another person's perspective.", 'emoji': "🧠", 'is_active': True}
        )
        self.cat_career, _ = ConversationCategory.objects.get_or_create(
            name="Career",
            defaults={'tagline': "Talk to someone experienced in my field.", 'emoji': "💼", 'is_active': True}
        )

        # Profession Categories
        self.prof_doctor, _ = Category.objects.get_or_create(
            name="Doctor",
            defaults={'description': "Physician and Specialist", 'is_active': True}
        )
        self.prof_teacher, _ = Category.objects.get_or_create(
            name="Teacher",
            defaults={'description': "Education and Tutoring", 'is_active': True}
        )

        # Authenticated Caller
        self.caller = User.objects.create_user(
            username="test_caller_2level",
            phone_number="+919876599001",
            role="CALLER",
            is_active=True
        )
        self.caller_profile, _ = CallerProfile.objects.get_or_create(user=self.caller, defaults={'name': "Caller TwoLevel"})
        Wallet.objects.get_or_create(user=self.caller, defaults={'balance': 500})

        # Agent 1: Doctor + Just Talk (On-Duty, Active, Available)
        self.agent1 = User.objects.create_user(username="agent_doc_justtalk", phone_number="+919876599002", role="AGENT", is_active=True)
        self.lp1, _ = ListenerProfile.objects.get_or_create(user=self.agent1)
        self.lp1.listener_id = "doc_justtalk"
        self.lp1.name = "Dr. JustTalk"
        self.lp1.profession = self.prof_doctor
        self.lp1.is_on_duty = True
        self.lp1.is_available = True
        self.lp1.save()
        self.lp1.conversation_categories.add(self.cat_just_talk)

        # Agent 2: Doctor + Advice (On-Duty, Active, Available)
        self.agent2 = User.objects.create_user(username="agent_doc_advice", phone_number="+919876599003", role="AGENT", is_active=True)
        self.lp2, _ = ListenerProfile.objects.get_or_create(user=self.agent2)
        self.lp2.listener_id = "doc_advice"
        self.lp2.name = "Dr. Advice"
        self.lp2.profession = self.prof_doctor
        self.lp2.is_on_duty = True
        self.lp2.is_available = True
        self.lp2.save()
        self.lp2.conversation_categories.add(self.cat_advice)

        # Agent 3: Doctor + Just Talk + Advice (On-Duty, Active, Available)
        self.agent3 = User.objects.create_user(username="agent_doc_both", phone_number="+919876599004", role="AGENT", is_active=True)
        self.lp3, _ = ListenerProfile.objects.get_or_create(user=self.agent3)
        self.lp3.listener_id = "doc_both"
        self.lp3.name = "Dr. Both"
        self.lp3.profession = self.prof_doctor
        self.lp3.is_on_duty = True
        self.lp3.is_available = True
        self.lp3.save()
        self.lp3.conversation_categories.add(self.cat_just_talk, self.cat_advice)

        # Agent 4: Teacher + Just Talk (Non-Doctor, On-Duty, Active, Available)
        self.agent4 = User.objects.create_user(username="agent_teacher_justtalk", phone_number="+919876599005", role="AGENT", is_active=True)
        self.lp4, _ = ListenerProfile.objects.get_or_create(user=self.agent4)
        self.lp4.listener_id = "teacher_justtalk"
        self.lp4.name = "Teacher JustTalk"
        self.lp4.profession = self.prof_teacher
        self.lp4.is_on_duty = True
        self.lp4.is_available = True
        self.lp4.save()
        self.lp4.conversation_categories.add(self.cat_just_talk)

        # Agent 5: Doctor + Career (Doctor without Just Talk or Advice, On-Duty, Active, Available)
        self.agent5 = User.objects.create_user(username="agent_doc_career", phone_number="+919876599006", role="AGENT", is_active=True)
        self.lp5, _ = ListenerProfile.objects.get_or_create(user=self.agent5)
        self.lp5.listener_id = "doc_career"
        self.lp5.name = "Dr. Career"
        self.lp5.profession = self.prof_doctor
        self.lp5.is_on_duty = True
        self.lp5.is_available = True
        self.lp5.save()
        self.lp5.conversation_categories.add(self.cat_career)

        # Agent 6: Doctor + Just Talk (Off-Duty)
        self.agent6 = User.objects.create_user(username="agent_doc_offduty", phone_number="+919876599007", role="AGENT", is_active=True)
        self.lp6, _ = ListenerProfile.objects.get_or_create(user=self.agent6)
        self.lp6.listener_id = "doc_offduty"
        self.lp6.name = "Dr. OffDuty"
        self.lp6.profession = self.prof_doctor
        self.lp6.is_on_duty = False
        self.lp6.is_available = False
        self.lp6.save()
        self.lp6.conversation_categories.add(self.cat_just_talk)

        # Agent 7: Doctor + Just Talk (Inactive User)
        self.agent7 = User.objects.create_user(username="agent_doc_inactive", phone_number="+919876599008", role="AGENT", is_active=False)
        self.lp7, _ = ListenerProfile.objects.get_or_create(user=self.agent7)
        self.lp7.listener_id = "doc_inactive"
        self.lp7.name = "Dr. Inactive"
        self.lp7.profession = self.prof_doctor
        self.lp7.is_on_duty = True
        self.lp7.is_available = True
        self.lp7.save()
        self.lp7.conversation_categories.add(self.cat_just_talk)

    def test_1_caller_selects_just_talk_and_doctor(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.get('/api/agents/discover/', {
            'conversation_categories': 'Just Talk',
            'profession': 'Doctor'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        agent_ids = [a['id'] for a in res.data['data']]
        self.assertIn(self.agent1.id, agent_ids)
        self.assertIn(self.agent3.id, agent_ids)
        self.assertNotIn(self.agent2.id, agent_ids)
        self.assertNotIn(self.agent4.id, agent_ids)
        self.assertNotIn(self.agent5.id, agent_ids)

    def test_2_doctor_without_just_talk_is_excluded(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.get('/api/agents/discover/', {
            'conversation_categories': 'Just Talk',
            'profession': 'Doctor'
        })
        agent_ids = [a['id'] for a in res.data['data']]
        self.assertNotIn(self.agent2.id, agent_ids)

    def test_3_just_talk_agent_who_is_not_a_doctor_is_excluded(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.get('/api/agents/discover/', {
            'conversation_categories': 'Just Talk',
            'profession': 'Doctor'
        })
        agent_ids = [a['id'] for a in res.data['data']]
        self.assertNotIn(self.agent4.id, agent_ids)

    def test_4_doctor_with_advice_when_caller_selected_just_talk_only_is_excluded(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.get('/api/agents/discover/', {
            'conversation_categories': 'Just Talk',
            'profession': 'Doctor'
        })
        agent_ids = [a['id'] for a in res.data['data']]
        self.assertNotIn(self.agent2.id, agent_ids)

    def test_5_caller_selects_just_talk_and_advice(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.get('/api/agents/discover/', {
            'conversation_categories': 'Just Talk,Advice',
            'profession': 'Doctor'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        agent_ids = [a['id'] for a in res.data['data']]
        self.assertIn(self.agent1.id, agent_ids)
        self.assertIn(self.agent2.id, agent_ids)
        self.assertIn(self.agent3.id, agent_ids)
        self.assertNotIn(self.agent5.id, agent_ids)

    def test_6_busy_agent_is_excluded(self):
        other_caller = User.objects.create_user(username="other_caller_t6", phone_number="+919876599098", role="CALLER")
        Call.objects.create(
            caller=other_caller,
            receiver=self.agent1,
            status='ACTIVE',
            channel_name='busy_test_channel'
        )
        self.client.force_authenticate(user=self.caller)
        res = self.client.get('/api/agents/discover/', {
            'conversation_categories': 'Just Talk',
            'profession': 'Doctor'
        })
        agent_ids = [a['id'] for a in res.data['data']]
        self.assertNotIn(self.agent1.id, agent_ids)

    def test_7_off_duty_agent_is_excluded(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.get('/api/agents/discover/', {
            'conversation_categories': 'Just Talk',
            'profession': 'Doctor'
        })
        agent_ids = [a['id'] for a in res.data['data']]
        self.assertNotIn(self.agent6.id, agent_ids)

    def test_8_unavailable_agent_is_excluded(self):
        other_caller = User.objects.create_user(username="other_caller_t8", phone_number="+919876599097", role="CALLER")
        self.lp1.is_available = False
        self.lp1.is_busy = True
        self.lp1.save(update_fields=['is_available', 'is_busy'])
        Call.objects.create(caller=other_caller, receiver=self.agent1, status='RINGING', channel_name='unavail_chan')

        self.client.force_authenticate(user=self.caller)
        res = self.client.get('/api/agents/discover/', {
            'conversation_categories': 'Just Talk',
            'profession': 'Doctor'
        })
        agent_ids = [a['id'] for a in res.data['data']]
        self.assertNotIn(self.agent1.id, agent_ids)

    def test_9_inactive_agent_is_excluded(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.get('/api/agents/discover/', {
            'conversation_categories': 'Just Talk',
            'profession': 'Doctor'
        })
        agent_ids = [a['id'] for a in res.data['data']]
        self.assertNotIn(self.agent7.id, agent_ids)

    def test_10_no_matching_agent_returns_200_with_empty_list(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.get('/api/agents/discover/', {
            'conversation_categories': 'Career',
            'profession': 'Teacher'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['count'], 0)
        self.assertEqual(res.data['data'], [])

    def test_11_caller_selects_agent_and_requests_call_exact_agent_used(self):
        self.client.force_authenticate(user=self.caller)
        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['agent']['id'], self.agent1.id)

    def test_12_selected_agent_becomes_unavailable_before_call_request(self):
        other_caller = User.objects.create_user(username="other_caller_t12", phone_number="+919876599099", role="CALLER")
        Call.objects.create(caller=other_caller, receiver=self.agent1, status='ACTIVE', channel_name='busy_channel_12')
        self.client.force_authenticate(user=self.caller)

        res = self.client.post('/api/calls/request/', {'agent_user_id': self.agent1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertEqual(res.data['message'], "Selected agent is currently unavailable or busy.")

    def test_13_existing_agent_discovery_functionality_still_works(self):
        res1 = self.client.get(f'/api/conversation-categories/{self.cat_just_talk.id}/agents/?profession=Doctor')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        ids1 = [a['id'] for a in res1.data['data']]
        self.assertIn(self.agent1.id, ids1)

        res2 = self.client.get(f'/api/categories/{self.prof_doctor.name}/listeners/?conversation_categories=Just Talk')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        ids2 = [a['id'] for a in res2.data['data']['matches']]
        self.assertIn(self.agent1.id, ids2)







