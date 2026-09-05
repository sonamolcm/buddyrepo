
# pyrefly: ignore [missing-import]
from django.db import models
# pyrefly: ignore [missing-import]
from django.contrib.auth.models import AbstractUser
# pyrefly: ignore [missing-import]
from django.db.models.signals import post_save
# pyrefly: ignore [missing-import]
from django.dispatch import receiver


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


class User(AbstractUser):
    ROLE_CHOICES = (
        ('CALLER', 'Caller'),
        ('LISTENER', 'Listener'),
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

    @property
    def is_caller(self):
        return self.role in ('CALLER', 'USER')

    @property
    def is_listener(self):
        return self.role in ('LISTENER', 'BUDDY')

    @property
    def is_admin(self):
        return self.role == 'ADMIN' or self.is_staff

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Caller: {self.name or self.user.username} ({self.user.phone_number})"


class ListenerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='listener_profile')
    listener_id = models.CharField(max_length=30, unique=True, db_index=True)
    name = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=20, choices=User.GENDER_CHOICES, null=True, blank=True)
    language = models.CharField(max_length=100, default='English', blank=True)
    interests = models.JSONField(default=list, blank=True)
    profile_picture = models.ImageField(upload_to='listeners/', null=True, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Listener [{self.listener_id}]: {self.name or self.user.username}"


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


# Signal: Auto-create Profile whenever a User is created
@receiver(post_save, sender=User)
def create_related_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role in ('CALLER', 'USER'):
            CallerProfile.objects.get_or_create(
                user=instance,
                defaults={
                    'name': instance.first_name or instance.username,
                    'age': instance.age,
                    'gender': instance.gender,
                }
            )
        elif instance.role in ('LISTENER', 'BUDDY'):
            ListenerProfile.objects.get_or_create(
                user=instance,
                defaults={
                    'listener_id': instance.username,
                    'language': 'English',
                }
            )


# ==========================================
# 5. CALLS & CALL HISTORY
# ==========================================
class Call(models.Model):
    CALL_TYPES = (
        ('AUDIO', 'Audio Call'),
        ('VIDEO', 'Video Call'),
    )
    CALL_STATUS = (
        ('RINGING', 'Ringing'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('MISSED', 'Missed'),
        ('ENDED', 'Ended'),
    )
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outgoing_calls')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incoming_calls')
    channel_name = models.CharField(max_length=100, unique=True, help_text="WebRTC / Agora channel ID")
    call_type = models.CharField(max_length=10, choices=CALL_TYPES, default='AUDIO')
    status = models.CharField(max_length=15, choices=CALL_STATUS, default='RINGING')
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    coins_deducted = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Call {self.id}: {self.caller.username} -> {self.receiver.username} ({self.status})"


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

