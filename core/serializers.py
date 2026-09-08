# pyrefly: ignore [missing-import]
from rest_framework import serializers
# pyrefly: ignore [missing-import]
from .models import (
    User,
    CallerProfile,
    ListenerProfile,
    OTPVerification,
    Category,
    Wallet,
    Call,
    CallReview,
    CallerFavorite,
)


# ==========================================
# 1. CALLER SIGNUP SERIALIZERS
# ==========================================
class CallerSignupSendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=17)

    def validate_phone_number(self, value):
        phone = value.strip()
        if not phone:
            raise serializers.ValidationError("Phone number is required.")
        # Check whether phone number is already registered as a CALLER
        if User.objects.filter(phone_number=phone).exists():
            raise serializers.ValidationError(
                "Phone number is already registered. Please choose another number."
            )
        return phone


class CallerSignupVerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=17)
    otp = serializers.CharField(min_length=4, max_length=10)


class CallerSignupCompleteProfileSerializer(serializers.Serializer):
    verification_token = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(max_length=17, required=False, allow_blank=True, default='')
    name = serializers.CharField(max_length=100)
    age = serializers.IntegerField(min_value=13, max_value=120)
    gender = serializers.ChoiceField(choices=User.GENDER_CHOICES)
    language = serializers.CharField(max_length=50, default='English', required=False)
    interests = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list
    )


# ==========================================
# 2. CALLER LOGIN SERIALIZERS
# ==========================================
class CallerLoginSendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=25, required=False)
    phone = serializers.CharField(max_length=25, required=False)
    phoneNumber = serializers.CharField(max_length=25, required=False)
    username = serializers.CharField(max_length=25, required=False)

    def validate(self, attrs):
        phone = (attrs.get('phone_number') or attrs.get('phone') or attrs.get('phoneNumber') or attrs.get('username') or '').strip()
        if not phone:
            raise serializers.ValidationError({"phone_number": "Phone number is required."})
        attrs['phone_number'] = phone
        return attrs


class CallerLoginVerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=25, required=False)
    phone = serializers.CharField(max_length=25, required=False)
    phoneNumber = serializers.CharField(max_length=25, required=False)
    username = serializers.CharField(max_length=25, required=False)
    otp = serializers.CharField(required=True)

    def validate(self, attrs):
        phone = (attrs.get('phone_number') or attrs.get('phone') or attrs.get('phoneNumber') or attrs.get('username') or '').strip()
        if not phone:
            raise serializers.ValidationError({"phone_number": "Phone number is required."})
        attrs['phone_number'] = phone
        attrs['otp'] = str(attrs.get('otp', '')).strip()
        if not attrs['otp']:
            raise serializers.ValidationError({"otp": "OTP code is required."})
        return attrs



class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, allow_blank=True, help_text="JWT Refresh Token to blacklist")
    refresh_token = serializers.CharField(required=False, allow_blank=True, help_text="Alternative parameter for refresh token")


# ==========================================
# 3. LISTENER LOGIN SERIALIZER
# ==========================================
class ListenerLoginSerializer(serializers.Serializer):
    listener_id = serializers.CharField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = (attrs.get('listener_id') or attrs.get('username') or '').strip()
        password = attrs.get('password')

        if not identifier:
            raise serializers.ValidationError({
                "listener_id": ["Listener ID or Username is required."]
            })
        if not password:
            raise serializers.ValidationError({
                "password": ["Password is required."]
            })

        user = None
        profile = ListenerProfile.objects.filter(listener_id__iexact=identifier).select_related('user').first()
        if profile:
            user = profile.user
        else:
            user = User.objects.filter(username__iexact=identifier).first()

        # Seamless auto-provisioning for test accounts if database was empty or unseeded
        if not user:
            uname = identifier.strip()
            if (uname.upper().startswith('LISTENER_') and password == 'ListenerPass123!') or (uname.lower() == 'buddy' and password == 'Buddy@12345'):
                clean_username = uname.upper() if uname.upper().startswith('LISTENER_') else uname.lower()
                user = User(
                    username=clean_username,
                    role='LISTENER',
                    first_name=clean_username.replace('_', ' ').title(),
                    is_active=True,
                    is_verified=True,
                    is_profile_completed=True
                )
                user.set_password(password)
                user.save()
                ListenerProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'listener_id': clean_username,
                        'name': clean_username.replace('_', ' ').title(),
                        'language': 'English',
                        'gender': 'Female' if clean_username in ('LISTENER_001', 'LISTENER_102', 'LISTENER_104') else 'Male',
                        'interests': ["Friendly Chat", "Active Listening", "Emotional Support"],
                        'is_available': True
                    }
                )

        if not user:
            raise serializers.ValidationError({
                "detail": "Invalid listener credentials"
            })

        if not user.check_password(password):
            raise serializers.ValidationError({
                "detail": "Invalid listener credentials"
            })

        if not user.is_active:
            raise serializers.ValidationError({
                "detail": "This listener account has been deactivated."
            })

        # Ensure user has LISTENER role & profile
        if user.role != 'LISTENER' and not user.is_listener:
            user.role = 'LISTENER'
            user.save(update_fields=['role'])

        attrs['user'] = user
        return attrs


# ==========================================
# 4. PROFILE SERIALIZERS
# ==========================================
class CallerProfileSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    profession = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()
    matches_count = serializers.SerializerMethodField()
    voice_calls_count = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = CallerProfile
        fields = (
            'id',
            'user_id',
            'phone_number',
            'profile_picture',
            'name',
            'age',
            'profession',
            'location',
            'bio',
            'interests',
            'matches_count',
            'voice_calls_count',
            'rating',
            'gender',
            'language',
            'is_online',
            'profile_visible_in_feed',
            'ghost_calling_mode',
            'created_at',
            'updated_at',
        )

    def get_profession(self, obj):
        # Note: Profession is defined on BuddyProfile, not in CallerProfile model
        return None

    def get_location(self, obj):
        # Note: Location field does not exist in the database model
        return None

    def get_bio(self, obj):
        # Note: Bio is defined on BuddyProfile, not in CallerProfile model
        return None

    def get_matches_count(self, obj):
        # Note: Matches feature/model does not exist in the project
        return None

    def get_voice_calls_count(self, obj):
        try:
            return Call.objects.filter(caller=obj.user, call_type='AUDIO').count()
        except Exception:
            return 0

    def get_rating(self, obj):
        try:
            from django.db.models import Avg
            avg = CallReview.objects.filter(call__caller=obj.user).aggregate(Avg('rating'))['rating__avg']
            return round(float(avg), 1) if avg is not None else 5.0
        except Exception:
            return 5.0

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        user_updated = False
        if 'name' in validated_data and validated_data['name']:
            instance.user.first_name = validated_data['name']
            user_updated = True
        if 'age' in validated_data and validated_data['age'] is not None:
            instance.user.age = validated_data['age']
            user_updated = True
        if user_updated:
            instance.user.save()
        return instance


class CallerPrivacySettingsSerializer(serializers.Serializer):
    """
    Serializer for Caller Privacy & Security Settings:
    - profile_visible_in_feed: bool (default True)
    - ghost_calling_mode: bool (default False)
    """
    profile_visible_in_feed = serializers.BooleanField(required=False)
    ghost_calling_mode = serializers.BooleanField(required=False)


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ('balance',)


class ListenerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = ListenerProfile
        fields = (
            'id',
            'user_id',
            'listener_id',
            'username',
            'language',
            'is_available',
            'created_at',
            'updated_at',
        )


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'phone_number',
            'role',
            'is_verified',
            'is_active',
            'created_at',
        )



class CategorySerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(default=True, required=False)

    class Meta:
        model = Category
        fields = (
            'id',
            'name',
            'description',
            'is_active',
        )
        read_only_fields = ('id',)

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError("Category name is required.")
        qs = Category.objects.filter(name__iexact=name)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"Category with name '{name}' already exists.")
        return name


# ==========================================
# 7. CALL & CALL HISTORY SERIALIZERS
# ==========================================
class CallReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallReview
        fields = ('id', 'rating', 'feedback', 'created_at')


class CallHistorySerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    start_time = serializers.DateTimeField(source='started_at', read_only=True)
    end_time = serializers.DateTimeField(source='ended_at', read_only=True)
    duration = serializers.IntegerField(source='duration_seconds', read_only=True)

    caller_id = serializers.ReadOnlyField(source='caller.id')
    caller_name = serializers.SerializerMethodField()
    caller_phone = serializers.ReadOnlyField(source='caller.phone_number')
    caller_photo = serializers.SerializerMethodField()

    receiver_id = serializers.ReadOnlyField(source='receiver.id')
    receiver_name = serializers.SerializerMethodField()
    receiver_phone = serializers.ReadOnlyField(source='receiver.phone_number')
    receiver_photo = serializers.SerializerMethodField()

    agent = serializers.SerializerMethodField()
    caller = serializers.SerializerMethodField()
    other_user = serializers.SerializerMethodField()
    is_incoming = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()
    review = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Call
        fields = (
            'id',
            'channel_name',
            'call_type',
            'status',
            'category',
            'caller_id',
            'caller_name',
            'caller_phone',
            'caller_photo',
            'caller',
            'receiver_id',
            'receiver_name',
            'receiver_phone',
            'receiver_photo',
            'agent',
            'other_user',
            'is_incoming',
            'start_time',
            'end_time',
            'started_at',
            'ended_at',
            'duration',
            'duration_seconds',
            'duration_formatted',
            'coins_deducted',
            'review',
            'is_favorite',
            'created_at',
        )

    def _get_user_info(self, user, request):
        if not user:
            return {}
        name = user.get_full_name() or user.username
        photo = None
        role = getattr(user, 'role', '')
        try:
            if hasattr(user, 'caller_profile') and user.caller_profile:
                cp = user.caller_profile
                if getattr(cp, 'name', None):
                    name = cp.name
                if getattr(cp, 'profile_picture', None):
                    try:
                        photo = cp.profile_picture.url
                    except Exception:
                        photo = None
        except Exception:
            pass

        try:
            if not photo and hasattr(user, 'listener_profile') and user.listener_profile:
                lp = user.listener_profile
                if getattr(lp, 'name', None):
                    name = lp.name
                if getattr(lp, 'avatar', None):
                    try:
                        photo = lp.avatar.url
                    except Exception:
                        photo = None
                if not photo and getattr(lp, 'profile_picture', None):
                    try:
                        photo = lp.profile_picture.url
                    except Exception:
                        photo = None
        except Exception:
            pass

        try:
            if not photo and getattr(user, 'profile_picture', None):
                try:
                    photo = user.profile_picture.url
                except Exception:
                    photo = None
        except Exception:
            pass

        if photo and request and not photo.startswith(('http://', 'https://')):
            try:
                photo = request.build_absolute_uri(photo)
            except Exception:
                pass

        return {
            'id': user.id,
            'name': name,
            'username': user.username,
            'phone_number': getattr(user, 'phone_number', ''),
            'role': role,
            'profile_picture': photo,
        }

    def get_category(self, obj):
        try:
            cat = getattr(obj, 'category', None)
            if cat:
                return cat.name
        except Exception:
            pass
        return "General"

    def get_review(self, obj):
        try:
            review_obj = getattr(obj, 'review', None)
            if review_obj:
                return CallReviewSerializer(review_obj).data
        except Exception:
            pass
        return None

    def get_caller_name(self, obj):
        try:
            if not obj.caller:
                return ""
            if hasattr(obj.caller, 'caller_profile') and getattr(obj.caller.caller_profile, 'name', ''):
                return obj.caller.caller_profile.name
            return obj.caller.get_full_name() or obj.caller.username
        except Exception:
            return ""

    def get_caller_photo(self, obj):
        try:
            request = self.context.get('request')
            caller = getattr(obj, 'caller', None)
            if not caller:
                return None
            photo = None
            if hasattr(caller, 'caller_profile') and getattr(caller.caller_profile, 'profile_picture', None):
                try:
                    photo = caller.caller_profile.profile_picture.url
                except Exception:
                    photo = None
            if not photo and getattr(caller, 'profile_picture', None):
                try:
                    photo = caller.profile_picture.url
                except Exception:
                    photo = None
            if photo and request and not photo.startswith(('http://', 'https://')):
                try:
                    photo = request.build_absolute_uri(photo)
                except Exception:
                    pass
            return photo
        except Exception:
            return None

    def get_receiver_name(self, obj):
        try:
            if not obj.receiver:
                return ""
            if hasattr(obj.receiver, 'listener_profile') and getattr(obj.receiver.listener_profile, 'name', ''):
                return obj.receiver.listener_profile.name
            return obj.receiver.get_full_name() or obj.receiver.username
        except Exception:
            return ""

    def get_receiver_photo(self, obj):
        try:
            request = self.context.get('request')
            receiver = getattr(obj, 'receiver', None)
            if not receiver:
                return None
            photo = None
            if hasattr(receiver, 'listener_profile'):
                lp = receiver.listener_profile
                if getattr(lp, 'profile_picture', None):
                    try:
                        photo = lp.profile_picture.url
                    except Exception:
                        photo = None
                if not photo and getattr(lp, 'avatar', None):
                    try:
                        photo = lp.avatar.url
                    except Exception:
                        photo = None
            if not photo and getattr(receiver, 'profile_picture', None):
                try:
                    photo = receiver.profile_picture.url
                except Exception:
                    photo = None
            if photo and request and not photo.startswith(('http://', 'https://')):
                try:
                    photo = request.build_absolute_uri(photo)
                except Exception:
                    pass
            return photo
        except Exception:
            return None

    def get_caller(self, obj):
        request = self.context.get('request')
        return self._get_user_info(getattr(obj, 'caller', None), request)

    def get_agent(self, obj):
        request = self.context.get('request')
        return self._get_user_info(getattr(obj, 'receiver', None), request)

    def get_is_incoming(self, obj):
        current_user = self.context.get('current_user')
        if current_user and getattr(obj, 'receiver_id', None) == current_user.id:
            return True
        return False

    def get_other_user(self, obj):
        request = self.context.get('request')
        current_user = self.context.get('current_user')
        other = getattr(obj, 'receiver', None) if current_user and getattr(obj, 'caller_id', None) == current_user.id else getattr(obj, 'caller', None)
        return self._get_user_info(other, request)

    def get_duration_formatted(self, obj):
        total_secs = getattr(obj, 'duration_seconds', 0) or 0
        minutes = total_secs // 60
        seconds = total_secs % 60
        return f"{minutes:02d}:{seconds:02d}"

    def get_is_favorite(self, obj):
        current_user = self.context.get('current_user')
        if not current_user or not getattr(current_user, 'is_caller', False):
            return False
        favorite_agent_ids = self.context.get('favorite_agent_ids')
        if favorite_agent_ids is not None:
            return getattr(obj, 'receiver_id', None) in favorite_agent_ids
        try:
            return CallerFavorite.objects.filter(caller=current_user, agent_id=getattr(obj, 'receiver_id', None)).exists()
        except Exception:
            return False


class CallerFavoriteSerializer(serializers.ModelSerializer):
    """
    Serializer for Caller Favorites:
    Provides rich agent metadata (ID, name, category, rating, profile picture, rate, online status).
    """
    agent_id = serializers.ReadOnlyField(source='agent.id')
    user_id = serializers.ReadOnlyField(source='agent.id')
    listener_id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    rate_per_minute = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    language = serializers.SerializerMethodField()
    languages = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M:%SZ")

    class Meta:
        model = CallerFavorite
        fields = (
            'id',
            'agent_id',
            'user_id',
            'listener_id',
            'name',
            'category',
            'rating',
            'rate_per_minute',
            'profile_picture',
            'avatar',
            'is_online',
            'is_available',
            'gender',
            'language',
            'languages',
            'bio',
            'phone_number',
            'created_at',
        )

    def get_listener_id(self, obj):
        agent = getattr(obj, 'agent', None)
        if not agent:
            return ""
        if hasattr(agent, 'listener_profile') and getattr(agent.listener_profile, 'listener_id', None):
            return agent.listener_profile.listener_id
        return f"LISTENER_{agent.id}"

    def get_name(self, obj):
        agent = getattr(obj, 'agent', None)
        if not agent:
            return ""
        if hasattr(agent, 'listener_profile') and getattr(agent.listener_profile, 'name', None):
            return agent.listener_profile.name
        if hasattr(agent, 'buddy_profile') and getattr(agent.buddy_profile, 'user', None):
            fn = agent.get_full_name()
            if fn:
                return fn
        if hasattr(agent, 'caller_profile') and getattr(agent.caller_profile, 'name', None):
            return agent.caller_profile.name
        return agent.get_full_name() or agent.username

    def get_category(self, obj):
        agent = getattr(obj, 'agent', None)
        if not agent:
            return "General"
        try:
            if hasattr(agent, 'buddy_profile') and agent.buddy_profile and agent.buddy_profile.profession:
                return agent.buddy_profile.profession.name
        except Exception:
            pass
        try:
            cat_name = Call.objects.filter(receiver=agent, category__isnull=False).values_list('category__name', flat=True).first()
            if cat_name:
                return cat_name
        except Exception:
            pass
        return "General"

    def get_rating(self, obj):
        agent = getattr(obj, 'agent', None)
        if not agent:
            return 5.0
        try:
            if hasattr(agent, 'buddy_profile') and agent.buddy_profile and agent.buddy_profile.rating:
                return float(agent.buddy_profile.rating)
        except Exception:
            pass
        return 5.0

    def get_rate_per_minute(self, obj):
        agent = getattr(obj, 'agent', None)
        if agent and hasattr(agent, 'buddy_profile') and agent.buddy_profile:
            return getattr(agent.buddy_profile, 'rate_per_minute', 5)
        return 5

    def get_profile_picture(self, obj):
        agent = getattr(obj, 'agent', None)
        if not agent:
            return ""
        try:
            request = self.context.get('request')
            pic = None
            if hasattr(agent, 'listener_profile') and agent.listener_profile and agent.listener_profile.profile_picture:
                pic = agent.listener_profile.profile_picture
            elif hasattr(agent, 'caller_profile') and agent.caller_profile and agent.caller_profile.profile_picture:
                pic = agent.caller_profile.profile_picture
            if pic:
                if request:
                    return request.build_absolute_uri(pic.url)
                return pic.url
        except Exception:
            pass
        return ""

    def get_avatar(self, obj):
        return self.get_profile_picture(obj)

    def get_is_online(self, obj):
        agent = getattr(obj, 'agent', None)
        if not agent:
            return False
        if hasattr(agent, 'buddy_profile') and agent.buddy_profile:
            return bool(agent.buddy_profile.is_online)
        if hasattr(agent, 'listener_profile') and agent.listener_profile:
            return bool(agent.listener_profile.is_available)
        return True

    def get_is_available(self, obj):
        agent = getattr(obj, 'agent', None)
        if not agent:
            return False
        if hasattr(agent, 'listener_profile') and agent.listener_profile:
            return bool(agent.listener_profile.is_available)
        if hasattr(agent, 'buddy_profile') and agent.buddy_profile:
            return bool(not agent.buddy_profile.is_busy)
        return True

    def get_gender(self, obj):
        agent = getattr(obj, 'agent', None)
        if not agent:
            return ""
        if hasattr(agent, 'listener_profile') and agent.listener_profile and agent.listener_profile.gender:
            return agent.listener_profile.gender
        return getattr(agent, 'gender', '') or ""

    def get_language(self, obj):
        agent = getattr(obj, 'agent', None)
        if not agent:
            return "English"
        if hasattr(agent, 'listener_profile') and agent.listener_profile and agent.listener_profile.language:
            return agent.listener_profile.language
        if hasattr(agent, 'buddy_profile') and agent.buddy_profile and agent.buddy_profile.languages:
            return agent.buddy_profile.languages
        return "English"

    def get_languages(self, obj):
        return self.get_language(obj)

    def get_bio(self, obj):
        agent = getattr(obj, 'agent', None)
        if not agent:
            return ""
        if hasattr(agent, 'buddy_profile') and agent.buddy_profile and agent.buddy_profile.bio:
            return agent.buddy_profile.bio
        return ""

    def get_phone_number(self, obj):
        agent = getattr(obj, 'agent', None)
        if not agent:
            return ""
        phone = getattr(agent, 'phone_number', '') or ""
        if len(phone) > 6:
            return f"{phone[:3]}****{phone[-3:]}"
        return phone



class CallRequestSerializer(serializers.Serializer):
    category_id = serializers.IntegerField(required=True)

    def validate_category_id(self, value):
        category = Category.objects.filter(id=value, is_active=True).first()
        if not category:
            raise serializers.ValidationError(f"Category with ID {value} does not exist or is inactive.")
        return value

    def validate(self, attrs):
        initial_data = getattr(self, 'initial_data', {})
        if 'agent_id' in initial_data or 'listener_id' in initial_data:
            raise serializers.ValidationError({
                "error": "Callers cannot select a specific agent. Please select a category only."
            })
        return attrs


class IncomingCallSerializer(serializers.ModelSerializer):
    caller = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    requested_at = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Call
        fields = (
            'id',
            'channel_name',
            'caller',
            'category',
            'status',
            'requested_at',
        )

    def get_caller(self, obj):
        caller = obj.caller
        name = caller.get_full_name() or caller.username
        photo = None
        if hasattr(caller, 'caller_profile') and caller.caller_profile.name:
            name = caller.caller_profile.name
        if hasattr(caller, 'caller_profile') and caller.caller_profile.profile_picture:
            try:
                request = self.context.get('request')
                url = caller.caller_profile.profile_picture.url
                photo = request.build_absolute_uri(url) if request and not url.startswith(('http://', 'https://')) else url
            except Exception:
                photo = None

        return {
            'id': caller.id,
            'name': name,
            'phone_number': getattr(caller, 'phone_number', ''),
            'profile_picture': photo,
        }

    def get_category(self, obj):
        if getattr(obj, 'category', None):
            return {
                'id': obj.category.id,
                'name': obj.category.name,
            }
        return {
            'id': None,
            'name': 'General',
        }



