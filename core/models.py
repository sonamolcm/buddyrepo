
# pyrefly: ignore [missing-import]
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


# ==========================================
# 1. USER & AUTHENTICATION
# ==========================================
class Interest(models.Model):
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Emoji or icon name, e.g. 🎧, ✈️, 🎮")

    def __str__(self):
        return f"{self.icon} {self.name}" if self.icon else self.name


class PhoneOTP(models.Model):
    phone_number = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phone_number} -> {self.otp}"


class UserManager(DjangoUserManager):
    """
    Custom user manager for Buddy User model.
    Ensures superusers created via `createsuperuser` automatically receive:
      - role = 'ADMIN'
      - is_staff = True
      - is_superuser = True
    And normal users default to role = 'CALLER' unless explicitly specified.
    """

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'CALLER')
        return super().create_user(username, email=email, password=password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('role') != 'ADMIN':
            raise ValueError('Superuser must have role="ADMIN".')

        return super().create_superuser(username, email=email, password=password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = (
        ('CALLER', 'Caller'),
        ('LISTENER', 'Listener'),
        ('AGENT', 'Agent'),
        ('ADMIN', 'Admin'),
        ('USER', 'Caller (Legacy)'),
        ('BUDDY', 'Listener (Legacy)'),
    )
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CALLER', db_index=True)
    phone_number = models.CharField(max_length=17, unique=True, null=True, blank=True, db_index=True)
    is_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    interests = models.ManyToManyField(Interest, blank=True, related_name='users')
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='core_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='core_user_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    is_profile_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.is_staff = True
            if self.role in ('CALLER', 'USER'):
                self.role = 'ADMIN'
        super().save(*args, **kwargs)

    @property
    def is_caller(self):
        return self.role in ('CALLER', 'USER')

    @property
    def is_listener(self):
        return self.role in ('LISTENER', 'BUDDY', 'AGENT')

    @property
    def is_agent(self):
        return self.is_listener

    @property
    def is_admin(self):
        return self.role == 'ADMIN' or self.is_staff

    @property
    def agent_profile(self):
        return getattr(self, 'listener_profile', None)

    def __str__(self):
        return f"{self.username} ({self.role})"



class CallerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='caller_profile')
    name = models.CharField(max_length=100, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=User.GENDER_CHOICES, null=True, blank=True)
    language = models.CharField(max_length=50, blank=True, default='English')
    interests = models.JSONField(default=list, blank=True)
    profile_picture = models.ImageField(upload_to='callers/', null=True, blank=True)
    is_online = models.BooleanField(default=False)
    profile_visible_in_feed = models.BooleanField(default=True)
    ghost_calling_mode = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Caller: {self.name or self.user.username} ({self.user.phone_number})"


class ListenerProfile(models.Model):
    RATE_CHOICES = (
        (3, '3 Coins/sec'),
        (5, '5 Coins/sec'),
        (10, '10 Coins/sec'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='listener_profile')
    listener_id = models.CharField(max_length=30, unique=True, db_index=True)
    name = models.CharField(max_length=100, blank=True)
    profession = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='listeners')
    bio = models.TextField(blank=True)
    gender = models.CharField(max_length=20, choices=User.GENDER_CHOICES, null=True, blank=True)
    language = models.CharField(max_length=100, default='English', blank=True)
    interests = models.JSONField(default=list, blank=True)
    profile_picture = models.ImageField(upload_to='listeners/', null=True, blank=True)
    rate_per_second = models.PositiveIntegerField(default=3, choices=RATE_CHOICES, help_text="Coins charged per second of call")
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    total_calls = models.PositiveIntegerField(default=0)
    total_earned_coins = models.PositiveIntegerField(default=0)
    is_on_duty = models.BooleanField(default=False)
    is_busy = models.BooleanField(default=False)
    is_available = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def rate_per_minute(self):
        return self.rate_per_second * 60

    @rate_per_minute.setter
    def rate_per_minute(self, value):
        if value:
            self.rate_per_second = max(1, round(value / 60))

    @property
    def display_name(self):
        return self.name or self.user.first_name or self.user.username

    def sync_availability(self):
        self.is_available = self.is_on_duty and not self.is_busy
        return self.is_available

    def __str__(self):
        return f"Agent [{self.listener_id}]: {self.display_name}"


AgentProfile = ListenerProfile


class OTPVerification(models.Model):
    PURPOSE_CHOICES = (
        ('SIGNUP', 'Signup'),
        ('LOGIN', 'Login'),
    )
    phone_number = models.CharField(max_length=17, db_index=True)
    otp_hash = models.CharField(max_length=128)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES, default='SIGNUP')
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['phone_number', 'purpose']),
        ]

    def __str__(self):
        return f"{self.phone_number} ({self.purpose}) - Verified: {self.is_verified}"



# ==========================================
# 2. CATEGORIES (PROFESSIONS FOR CALLERS)
# ==========================================
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# ==========================================
# 3. BUDDIES
# ==========================================
class BuddyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='buddy_profile')
    profession = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='buddies'
    )
    bio = models.TextField(blank=True)
    languages = models.CharField(max_length=200, default='English', help_text="Comma-separated languages")
    rate_per_minute = models.PositiveIntegerField(default=5, help_text="Coins charged per minute of call")
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    total_calls = models.PositiveIntegerField(default=0)
    is_online = models.BooleanField(default=False)
    is_busy = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Buddy: {self.user.username} - {self.profession.name if self.profession else 'No Category'}"


# ==========================================
# 4. COINS & WALLET
# ==========================================
class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.PositiveIntegerField(default=50, help_text="Current coin balance")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet: {self.balance} coins"


class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('CREDIT', 'Credit (Purchased/Earned)'),
        ('DEBIT', 'Debit (Spent on Call)'),
    )
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.PositiveIntegerField()
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type}: {self.amount} coins ({self.wallet.user.username})"


# Signal: Auto-create Profile whenever a User is created or updated
@receiver(post_save, sender=User)
def create_related_profile(sender, instance, created, **kwargs):
    if instance.role in ('CALLER', 'USER'):
        CallerProfile.objects.get_or_create(
            user=instance,
            defaults={
                'name': instance.first_name or instance.username,
                'age': instance.age,
                'gender': instance.gender,
            }
        )
    elif instance.role in ('LISTENER', 'BUDDY', 'AGENT'):
        profile, _ = ListenerProfile.objects.get_or_create(
            user=instance,
            defaults={
                'listener_id': instance.username,
                'name': instance.first_name or instance.username,
                'language': 'English',
                'gender': instance.gender or 'Other',
                'interests': ["Friendly Chat", "Emotional Support"],
                'is_available': False,
                'is_on_duty': False,
                'rate_per_second': 3,
                'rating': 5.00,
            }
        )
        # Ensure listener_id matches username if empty
        if not profile.listener_id:
            profile.listener_id = instance.username
            profile.save(update_fields=['listener_id'])
        AgentWallet.objects.get_or_create(agent=instance, defaults={'balance': 0})



# ==========================================
# 5. CALLS & CALL HISTORY
# ==========================================
class Call(models.Model):
    CALL_TYPES = (
        ('AUDIO', 'Audio Call'),
        ('VIDEO', 'Video Call'),
    )
    CALL_STATUS = (
        ('PENDING', 'Pending'),
        ('RINGING', 'Ringing'),
        ('ACCEPTED', 'Accepted'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
        ('MISSED', 'Missed'),
        ('ENDED', 'Ended'),
    )
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outgoing_calls')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incoming_calls')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='calls')
    channel_name = models.CharField(max_length=100, unique=True, help_text="WebRTC / Agora channel ID")
    call_type = models.CharField(max_length=10, choices=CALL_TYPES, default='AUDIO')
    status = models.CharField(max_length=20, choices=CALL_STATUS, default='RINGING')
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    coins_deducted = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        cat_name = self.category.name if self.category else "General"
        return f"Call {self.id} [{cat_name}]: {self.caller.username} -> {self.receiver.username} ({self.status})"


class CallReview(models.Model):
    call = models.OneToOneField(Call, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveSmallIntegerField(default=5, help_text="1 to 5 stars")
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for Call #{self.call.id}: {self.rating} stars"


# ==========================================
# 6. NOTIFICATIONS
# ==========================================
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('CALL', 'Call Notification'),
        ('WALLET', 'Wallet Notification'),
        ('SYSTEM', 'System Alert'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(max_length=15, choices=NOTIFICATION_TYPES, default='SYSTEM')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification to {self.user.username}: {self.title}"


# ==========================================
# 7. CALLER FAVORITES
# ==========================================
class CallerFavorite(models.Model):
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='caller_favorites')
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('caller', 'agent')
        ordering = ['-created_at']

    def __str__(self):
        return f"Caller {self.caller.username} -> Favorite Agent {self.agent.username}"


# ==========================================
# 8. AGENT DUTY SESSIONS, WALLET, EARNINGS & PAYOUTS
# ==========================================
class AgentDutySession(models.Model):
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='duty_sessions')
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Duty {self.agent.username}: {self.started_at} - {self.ended_at or 'Active'}"


class AgentWallet(models.Model):
    agent = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_wallet')
    balance = models.PositiveIntegerField(default=0, help_text="Current withdrawable coin balance")
    total_earned = models.PositiveIntegerField(default=0, help_text="Lifetime earned coins")
    total_paid_out = models.PositiveIntegerField(default=0, help_text="Lifetime paid out coins")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AgentWallet ({self.agent.username}): {self.balance} coins"

    @property
    def total_withdrawn(self):
        return self.total_paid_out

    @total_withdrawn.setter
    def total_withdrawn(self, value):
        self.total_paid_out = value


class AgentEarning(models.Model):
    EARNING_TYPES = (
        ('VOICE', 'Voice Call'),
        ('VIDEO', 'Video Call'),
        ('BONUS', 'Bonus'),
        ('ADJUSTMENT', 'Adjustment'),
    )
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earnings')
    call = models.ForeignKey('Call', null=True, blank=True, on_delete=models.SET_NULL, related_name='agent_earnings')
    earning_type = models.CharField(max_length=20, choices=EARNING_TYPES, default='VOICE')
    coins = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.agent.username} +{self.coins} coins ({self.earning_type})"

    @property
    def amount(self):
        return self.coins

    @amount.setter
    def amount(self, value):
        self.coins = value


class AgentPayout(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    )
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payouts')
    coins = models.PositiveIntegerField(help_text="Coins to withdraw")
    amount_inr = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Equivalent amount in INR")
    payout_method = models.CharField(max_length=50, default='UPI')
    payout_details = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"Payout #{self.id} for {self.agent.username}: {self.coins} coins ({self.status})"

    @property
    def amount(self):
        return self.coins

    @amount.setter
    def amount(self, value):
        self.coins = value

    @property
    def created_at(self):
        return self.requested_at


