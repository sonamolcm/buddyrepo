from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
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
    AgentPayout
)

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
            defaults={'listener_id': 'agent_dash_01', 'rate_per_second': 5}
        )
        self.wallet, _ = AgentWallet.objects.get_or_create(agent=self.agent, defaults={'balance': 150, 'total_earned': 300})
        self.client.force_authenticate(user=self.agent)

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
        })
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
        })
        self.assertEqual(bad_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 150)


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
        ListenerProfile.objects.create(
            user=u1,
            listener_id="dr_smith",
            name="Dr. Alice Smith",
            profession=doctor_cat,
            bio="Cardiologist and wellness guide",
            rate_per_second=5,
            rating=4.9,
            total_calls=15
        )

        u2 = User.objects.create_user(username="dr_house", password="Pass123!Safe", role="LISTENER", first_name="Dr. Gregory House", is_active=True)
        ListenerProfile.objects.create(
            user=u2,
            listener_id="dr_house",
            name="Dr. Gregory House",
            profession=doctor_cat,
            bio="Diagnostic medicine and health counselor",
            rate_per_second=10,
            rating=5.0,
            total_calls=40
        )

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
        self.client = APIClient()
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
