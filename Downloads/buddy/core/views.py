# pyright: reportMissingImports=false
# pyrefly: ignore [missing-import]
import random
from django.conf import settings  # type: ignore
from django.shortcuts import render  # type: ignore
from django.contrib.auth import authenticate, logout as django_logout  # type: ignore
# pyrefly: ignore [missing-import]
from django.db import transaction  # type: ignore
from django.db.models import Q  # type: ignore
# pyrefly: ignore [missing-import]
from rest_framework import status, permissions  # type: ignore
# pyrefly: ignore [missing-import]
from rest_framework.views import APIView  # type: ignore
# pyrefly: ignore [missing-import]
from rest_framework.response import Response  # type: ignore
# pyrefly: ignore [missing-import]
from rest_framework_simplejwt.tokens import RefreshToken, TokenError  # type: ignore

# pyrefly: ignore [missing-import]
from .models import User, CallerProfile, ListenerProfile, Interest, PhoneOTP, Category  # type: ignore
from .permissions import IsAdminUser  # type: ignore
# pyrefly: ignore [missing-import]
from .otp_service import (  # type: ignore
    create_and_send_otp,
    verify_stored_otp,
    validate_verification_token,
    generate_verification_token
)
# pyrefly: ignore [missing-import]
from .serializers import (  # type: ignore
    CallerSignupSendOTPSerializer,
    CallerSignupVerifyOTPSerializer,
    CallerSignupCompleteProfileSerializer,
    CallerLoginSendOTPSerializer,
    CallerLoginVerifyOTPSerializer,
    ListenerLoginSerializer,
    CallerProfileSerializer,
    ListenerProfileSerializer,
    UserDetailSerializer,
    CategorySerializer,
)



# ===================================================
# 1. CALLER SIGNUP FLOW VIEWS
# ===================================================
class CallerSignupSendOTPView(APIView):
    """
    Caller Signup Step 1: Enter phone number and send signup OTP.
    Rule: Checks whether this phone number is already registered as a CALLER.
    If already registered: Rejects with 409 Conflict.
    If not registered: Hashes and stores OTP with expiry, sends via OTP provider.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            "success": True,
            "message": "Send OTP endpoint is active. Please send a POST request with JSON body: {\"phone_number\": \"+919876543210\"}",
            "method": "POST"
        }, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            serializer = CallerSignupSendOTPSerializer(data=request.data)
            if not serializer.is_valid():
                phone_errors = serializer.errors.get('phone_number', [])
                if any('already registered' in str(e) for e in phone_errors):
                    return Response({
                        "success": False,
                        "message": "Phone number is already registered. Please choose another number."
                    }, status=status.HTTP_409_CONFLICT)
                return Response({
                    "success": False,
                    "message": "Validation failed.",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            phone_number = serializer.validated_data['phone_number'].strip()

            # 2. Generate, hash, and send OTP
            success, message, otp_code = create_and_send_otp(phone_number, purpose='SIGNUP')

            response_data = {
                "phone_number": phone_number,
            }
            if settings.DEBUG:
                response_data["otp"] = otp_code

            return Response({
                "success": True,
                "message": f"OTP sent successfully to {phone_number}",
                "data": response_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Internal error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CallerSignupVerifyOTPView(APIView):
    """
    Caller Signup Step 2: Verify 6-digit OTP code for Signup.
    Checks expiry, attempt limits, and hash match.
    Issues a temporary signed verification_token for Step 3.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            "success": True,
            "message": "Verify OTP endpoint is active. Send POST with {\"phone_number\": \"+91...\", \"otp\": \"123456\"}",
            "method": "POST"
        }, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            serializer = CallerSignupVerifyOTPSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "success": False,
                    "message": "Invalid input.",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            phone_number = serializer.validated_data['phone_number'].strip()
            otp = serializer.validated_data['otp'].strip()

            result = verify_stored_otp(phone_number, otp, purpose='SIGNUP')
            if isinstance(result, tuple) and len(result) == 3:
                success, message, token = result
            elif isinstance(result, tuple) and len(result) == 2:
                success, message = result
                token = generate_verification_token(phone_number, 'SIGNUP') if success else ""
            else:
                success, message, token = False, "Unknown verification error.", ""

            if not success:
                return Response({
                    "success": False,
                    "message": message
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "success": True,
                "message": "Phone number verified successfully. Please complete your profile.",
                "data": {
                    "phone_number": phone_number,
                    "verification_token": token
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Server error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CallerSignupCompleteProfileView(APIView):
    """
    Caller Signup Step 3: Profile Setup after successful OTP verification.
    Saves Name, Age, Gender, Language, and Interests.
    Creates User and CallerProfile, issues JWT access and refresh tokens.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CallerSignupCompleteProfileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data['verification_token']
        provided_phone = (serializer.validated_data.get('phone_number') or '').strip()

        # Validate signed verification token and automatically extract verified phone number
        is_valid_token, token_err, verified_phone = validate_verification_token(
            token,
            expected_phone=provided_phone if provided_phone else None,
            expected_purpose='SIGNUP'
        )
        if not is_valid_token:
            return Response({
                "success": False,
                "message": token_err
            }, status=status.HTTP_400_BAD_REQUEST)

        phone_number = verified_phone

        # Database safety check against race conditions
        if User.objects.filter(phone_number=phone_number).exists():
            return Response({
                "success": False,
                "message": "Phone number is already registered. Please choose another number."
            }, status=status.HTTP_409_CONFLICT)

        name = serializer.validated_data['name'].strip()
        age = serializer.validated_data['age']
        gender = serializer.validated_data['gender']
        language = serializer.validated_data.get('language', 'English')
        interests = serializer.validated_data.get('interests', [])

        with transaction.atomic():
            user = User.objects.create_user(
                username=phone_number,
                phone_number=phone_number,
                role='CALLER',
                first_name=name,
                is_verified=True,
                is_profile_completed=True
            )
            caller_profile, _ = CallerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'name': name,
                    'age': age,
                    'gender': gender,
                    'language': language,
                    'interests': interests
                }
            )
            caller_profile.name = name
            caller_profile.age = age
            caller_profile.gender = gender
            caller_profile.language = language
            caller_profile.interests = interests
            caller_profile.save()

        # Issue JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            "success": True,
            "message": "Caller account created successfully.",
            "data": {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "phone_number": user.phone_number,
                    "role": user.role,
                    "name": caller_profile.name,
                    "age": caller_profile.age,
                    "gender": caller_profile.gender,
                    "language": caller_profile.language,
                    "interests": caller_profile.interests,
                    "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
                },
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }
            }
        }, status=status.HTTP_201_CREATED)


# ===================================================
# 2. CALLER LOGIN FLOW VIEWS
# ===================================================
class CallerLoginSendOTPView(APIView):
    """
    Caller Login Step 1: Send Login OTP.
    Rule: Checks whether the phone number belongs to a registered CALLER.
    If not registered: Returns 404 Not Found.
    If registered: Generates and sends OTP with purpose='LOGIN'.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CallerLoginSendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number'].strip()

        # Check whether phone number belongs to a registered Caller
        user = User.objects.filter(phone_number=phone_number).first()
        if user is None or not getattr(user, 'is_caller', False):
            return Response({
                "success": False,
                "message": "Phone number is not registered. Please sign up first."
            }, status=status.HTTP_404_NOT_FOUND)

        if not user.is_active:
            return Response({
                "success": False,
                "message": "Your account has been deactivated. Please contact support."
            }, status=status.HTTP_403_FORBIDDEN)

        success, message, otp_code = create_and_send_otp(phone_number, purpose='LOGIN')

        response_data = {
            "phone_number": phone_number,
        }
        if settings.DEBUG:
            response_data["otp"] = otp_code

        return Response({
            "success": True,
            "message": f"Login OTP sent successfully to {phone_number}",
            "data": response_data
        }, status=status.HTTP_200_OK)


class CallerLoginVerifyOTPView(APIView):
    """
    Caller Login Step 2: Verify Login OTP & Authenticate.
    Verifies OTP with purpose='LOGIN', enforces expiry and max attempts.
    Returns JWT access and refresh tokens along with caller profile.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CallerLoginVerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Invalid input.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number'].strip()
        otp = serializer.validated_data['otp'].strip()

        success, message, _ = verify_stored_otp(phone_number, otp, purpose='LOGIN')
        if not success:
            return Response({
                "success": False,
                "message": "Invalid or expired OTP"
            }, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(phone_number=phone_number).first()
        if user is None or not getattr(user, 'is_caller', False):
            return Response({
                "success": False,
                "message": "No caller account found with this phone number."
            }, status=status.HTTP_404_NOT_FOUND)

        if not user.is_active:
            return Response({
                "success": False,
                "message": "This account is inactive."
            }, status=status.HTTP_403_FORBIDDEN)

        # Retrieve caller profile
        caller_profile, _ = CallerProfile.objects.get_or_create(
            user=user,
            defaults={
                'name': user.first_name or user.username,
                'age': user.age,
                'gender': user.gender,
            }
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            "success": True,
            "message": "Login successful",
            "data": {
                "user": {
                    "id": user.id,
                    "role": "CALLER",
                    "phone_number": user.phone_number,
                    "name": caller_profile.name,
                    "age": caller_profile.age,
                    "gender": caller_profile.gender,
                    "language": caller_profile.language,
                    "interests": caller_profile.interests
                },
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }
            }
        }, status=status.HTTP_200_OK)


# ===================================================
# 3. LISTENER LOGIN FLOW VIEW
# ===================================================
class ListenerLoginView(APIView):
    """
    Listener Login API:
    Authenticates Listener using Listener ID / Username + Password.
    Password verified securely via Django's PBKDF2 check_password.
    Returns JWT access & refresh tokens and listener profile.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            "success": True,
            "message": "Listener Login endpoint is active. Please send an HTTP POST request with JSON body containing 'username' and 'password'.",
            "method": "POST",
            "endpoint": "/api/auth/listener/login/",
            "sample_body": {
                "username": "LISTENER_001",
                "password": "your_listener_password"
            }
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ListenerLoginSerializer(data=request.data)
        if not serializer.is_valid():
            detail_err = serializer.errors.get('detail')
            err_msg = detail_err[0] if detail_err else "Invalid listener credentials"
            return Response({
                "success": False,
                "message": str(err_msg)
            }, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data['user']

        # Retrieve listener profile
        listener_profile, _ = ListenerProfile.objects.get_or_create(
            user=user,
            defaults={
                'listener_id': user.username,
                'language': 'English',
            }
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            "success": True,
            "message": "Login successful",
            "data": {
                "user": {
                    "id": user.id,
                    "role": "LISTENER",
                    "username": user.username,
                    "listener_id": listener_profile.listener_id,
                    "language": listener_profile.language,
                    "is_available": listener_profile.is_available
                },
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }
            }
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    User Logout API:
    Supports logging out for both Callers and Listeners.
    Accepts optional JWT 'refresh' token in the JSON request body.
    Blacklists the refresh token (if blacklist app is enabled) and resets Listener online availability.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            "success": True,
            "message": "Logout endpoint is active. Please send a POST request with optional JSON body: {\"refresh\": \"<refresh_token>\"}",
            "method": "POST",
            "endpoint": "/api/auth/logout/"
        }, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh') or request.data.get('refresh_token')
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except AttributeError:
                    # Token blacklist app is not enabled in settings/INSTALLED_APPS
                    pass
                except TokenError:
                    # Token is invalid or already expired/blacklisted
                    pass

            # If user is authenticated and is a listener, set availability to False
            if request.user and request.user.is_authenticated:
                if getattr(request.user, 'is_listener', False):
                    ListenerProfile.objects.filter(user=request.user).update(is_available=False)

            # Terminate Django session if present
            try:
                django_logout(request)
            except Exception:
                pass

            return Response({
                "success": True,
                "message": "Logged out successfully."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "message": f"Logout failed: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)


# ===================================================
# 4. PROFILE VIEW
# ===================================================
class ProfileView(APIView):
    """
    Caller & User Profile API:
    - GET /api/profile/ (or /api/caller/profile/):
      Returns the caller's complete profile: User ID, phone number, name, age, gender,
      language, interests, profile picture, is_online, created_at, updated_at.
    - PUT / PATCH /api/profile/:
      Allows the caller to update their own profile fields.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role in ('CALLER', 'USER'):
            profile, _ = CallerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'name': user.first_name or user.username,
                    'age': user.age,
                    'gender': user.gender,
                }
            )
            serializer = CallerProfileSerializer(profile)
            return Response({
                "success": True,
                "message": "Caller profile retrieved successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        elif user.role in ('LISTENER', 'BUDDY'):
            profile, _ = ListenerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'listener_id': user.username,
                    'language': 'English',
                }
            )
            serializer = ListenerProfileSerializer(profile)
            return Response({
                "success": True,
                "message": "Listener profile retrieved successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        # Fallback for Admin or legacy user
        serializer = UserDetailSerializer(user)
        return Response({
            "success": True,
            "message": "User profile retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        return self._update(request, partial=True)

    def put(self, request):
        return self._update(request, partial=False)

    def _update(self, request, partial=True):
        user = request.user
        if user.role in ('CALLER', 'USER'):
            profile, _ = CallerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'name': user.first_name or user.username,
                    'age': user.age,
                    'gender': user.gender,
                }
            )
            serializer = CallerProfileSerializer(profile, data=request.data, partial=partial)
            if not serializer.is_valid():
                return Response({
                    "success": False,
                    "message": "Validation failed.",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response({
                "success": True,
                "message": "Caller profile updated successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        elif user.role in ('LISTENER', 'BUDDY'):
            profile, _ = ListenerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'listener_id': user.username,
                    'language': 'English',
                }
            )
            serializer = ListenerProfileSerializer(profile, data=request.data, partial=partial)
            if not serializer.is_valid():
                return Response({
                    "success": False,
                    "message": "Validation failed.",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response({
                "success": True,
                "message": "Listener profile updated successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        serializer = UserDetailSerializer(user, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({
            "success": True,
            "message": "User profile updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def delete(self, request):
        """
        Permanently delete the authenticated user's account and profile data.
        """
        user = request.user
        user_id = user.id
        ident = user.username or getattr(user, 'phone_number', '') or f"User #{user_id}"
        user.delete()
        return Response({
            "success": True,
            "message": f"Account '{ident}' (ID: {user_id}) and all associated data have been permanently deleted."
        }, status=status.HTTP_200_OK)


UserProfileView = ProfileView


class DeleteAccountView(APIView):
    """
    Account Deletion API:
    Permanently deletes the currently authenticated user's account and all associated profiles/data.
    Supports both DELETE and POST methods.
    Required for Google Play Store / Apple App Store account deletion policies.

    DELETE /api/auth/delete-account/
    Headers:
      Authorization: Bearer <access_token>
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user
        user_id = user.id
        ident = user.username or getattr(user, 'phone_number', '') or f"User #{user_id}"
        user.delete()
        return Response({
            "success": True,
            "message": f"Account '{ident}' (ID: {user_id}) and all associated data have been permanently deleted."
        }, status=status.HTTP_200_OK)

    def post(self, request):
        return self.delete(request)


# ===================================================
# 5. METADATA: WORLD LANGUAGES & INTERESTS DROPDOWNS
# ===================================================
WORLD_LANGUAGES = [
    {"code": "en", "name": "English", "native_name": "English"},
    {"code": "ml", "name": "Malayalam", "native_name": "മലയാളം"},
    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
    {"code": "ta", "name": "Tamil", "native_name": "தமிழ்"},
    {"code": "te", "name": "Telugu", "native_name": "తెలుగు"},
    {"code": "kn", "name": "Kannada", "native_name": "ಕನ್ನಡ"},
    {"code": "bn", "name": "Bengali", "native_name": "বাংলা"},
    {"code": "mr", "name": "Marathi", "native_name": "मराठी"},
    {"code": "gu", "name": "Gujarati", "native_name": "ગુજરાતી"},
    {"code": "pa", "name": "Punjabi", "native_name": "ਪੰਜਾਬੀ"},
    {"code": "ur", "name": "Urdu", "native_name": "اردو"},
    {"code": "es", "name": "Spanish", "native_name": "Español"},
    {"code": "fr", "name": "French", "native_name": "Français"},
    {"code": "de", "name": "German", "native_name": "Deutsch"},
    {"code": "ar", "name": "Arabic", "native_name": "العربية"},
    {"code": "zh", "name": "Mandarin Chinese", "native_name": "中文"},
    {"code": "ja", "name": "Japanese", "native_name": "日本語"},
    {"code": "ko", "name": "Korean", "native_name": "한국어"},
    {"code": "pt", "name": "Portuguese", "native_name": "Português"},
    {"code": "ru", "name": "Russian", "native_name": "Русский"},
    {"code": "it", "name": "Italian", "native_name": "Italiano"},
    {"code": "tr", "name": "Turkish", "native_name": "Türkçe"},
    {"code": "id", "name": "Indonesian", "native_name": "Bahasa Indonesia"},
    {"code": "vi", "name": "Vietnamese", "native_name": "Tiếng Việt"},
]

DEFAULT_INTERESTS = [
    {"name": "Music", "icon": "🎵"},
    {"name": "Movies & TV", "icon": "🎬"},
    {"name": "Gaming", "icon": "🎮"},
    {"name": "Travel & Places", "icon": "✈️"},
    {"name": "Sports & Cricket", "icon": "⚽"},
    {"name": "Food & Cooking", "icon": "🍕"},
    {"name": "Technology & Coding", "icon": "💻"},
    {"name": "Books & Reading", "icon": "📚"},
    {"name": "Fitness & Gym", "icon": "🏋️"},
    {"name": "Art & Design", "icon": "🎨"},
    {"name": "Photography", "icon": "📸"},
    {"name": "Nature & Outdoors", "icon": "🌿"},
    {"name": "Pets & Animals", "icon": "🐾"},
    {"name": "Business & Startups", "icon": "💼"},
    {"name": "Anime & Manga", "icon": "🍙"},
    {"name": "Philosophy & Life", "icon": "💭"},
]


class LanguageListView(APIView):
    """
    Returns a comprehensive list of world languages for the dropdown in profile setup.
    Public endpoint.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            "success": True,
            "count": len(WORLD_LANGUAGES),
            "data": WORLD_LANGUAGES
        }, status=status.HTTP_200_OK)


class InterestListView(APIView):
    """
    Returns available interests with emoji icons for multi-select chips in profile setup.
    Public endpoint. Automatically auto-seeds default interests if table is empty.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        interests = list(Interest.objects.values('id', 'name', 'icon'))
        if not interests:
            to_create = [Interest(name=item['name'], icon=item['icon']) for item in DEFAULT_INTERESTS]
            Interest.objects.bulk_create(to_create, ignore_conflicts=True)
            interests = list(Interest.objects.values('id', 'name', 'icon'))

        return Response({
            "success": True,
            "count": len(interests),
            "data": interests
        }, status=status.HTTP_200_OK)




# ===================================================
# 6.1 CATEGORIES API (FOR CALLER PROFESSIONS)
# ===================================================
class CategoryListCreateView(APIView):
    """
    GET /api/categories/
    - Return only categories where is_active=True.
    - Authenticated users can access.

    POST /api/categories/
    - Admin only.
    - Set is_active=True automatically for newly created category.
    - Handle duplicate names properly and return HTTP 400.
    """
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [IsAdminUser()]

    def get(self, request):
        categories = Category.objects.filter(is_active=True).order_by('id')
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        category = serializer.save(is_active=True)
        return Response(CategorySerializer(category).data, status=status.HTTP_201_CREATED)


class CategoryDetailView(APIView):
    """
    GET /api/categories/<id>/
    - Return the category only if is_active=True.
    - If it doesn't exist or is inactive, return HTTP 404.
    - Authenticated users can access.

    PUT /api/categories/<id>/
    PATCH /api/categories/<id>/
    - Admin only.
    - Allow updating name, description, is_active.

    DELETE /api/categories/<id>/
    - Admin only.
    - Soft delete: category.is_active = False; category.save().
    - Return a suitable success response.
    """
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [IsAdminUser()]

    def get(self, request, id):
        category = Category.objects.filter(pk=id, is_active=True).first()
        if not category:
            return Response(
                {"detail": "Category not found or is inactive."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CategorySerializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        return self._update(request, id, partial=False)

    def patch(self, request, id):
        return self._update(request, id, partial=True)

    def _update(self, request, id, partial=True):
        category = Category.objects.filter(pk=id).first()
        if not category:
            return Response(
                {"detail": "Category not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CategorySerializer(category, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        updated_category = serializer.save()
        return Response(CategorySerializer(updated_category).data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        category = Category.objects.filter(pk=id).first()
        if not category:
            return Response(
                {"detail": "Category not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        category.is_active = False
        category.save(update_fields=['is_active', 'updated_at'])
        return Response(
            {"message": "Category deleted successfully."},
            status=status.HTTP_200_OK
        )


CategoryListView = CategoryListCreateView




# ===================================================
# 7. WEB COMPATIBILITY AUTH VIEWS
# ===================================================


class WebSendOTPView(APIView):
    """
    Handles OTP generation for the web onboarding simulator (/api/auth/send-otp/).
    Accepts { phone_number, mode }.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = (request.data.get('phone_number') or '').strip()
        mode = request.data.get('mode', 'signup')

        if not phone:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate a test OTP (defaults to '1234' for simulator ease)
        otp = '1234'
        PhoneOTP.objects.update_or_create(phone_number=phone, defaults={'otp': otp})

        user_exists = User.objects.filter(phone_number=phone).exists()

        return Response({
            'message': f'Verification code sent to {phone}',
            'account_exists': user_exists,
            'otp': otp
        }, status=status.HTTP_200_OK)


class WebVerifyOTPView(APIView):
    """
    Verifies 4-digit or 6-digit OTP for the web onboarding simulator (/api/auth/verify-otp/).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = (request.data.get('phone_number') or '').strip()
        otp = (request.data.get('otp') or '').strip()

        if not phone or not otp:
            return Response({'error': 'Phone number and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)

        otp_record = PhoneOTP.objects.filter(phone_number=phone, otp=otp).first()
        if not otp_record and otp != '1234':
            return Response({'error': 'Invalid verification code.'}, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(
            phone_number=phone,
            defaults={
                'username': phone,
                'role': 'CALLER',
                'is_verified': True,
                'is_active': True,
            }
        )

        # Ensure CallerProfile exists
        caller_profile, _ = CallerProfile.objects.get_or_create(
            user=user,
            defaults={'language': 'English'}
        )

        refresh = RefreshToken.for_user(user)

        # Determine next step for the simulator
        if caller_profile.name or getattr(user, 'first_name', ''):
            next_step = "HOME"
        else:
            next_step = "ABOUT_YOU"

        return Response({
            'message': 'Verification successful',
            'is_new_user': created,
            'next_step': next_step,
            'user': {
                'id': user.id,
                'first_name': caller_profile.name or getattr(user, 'first_name', '') or user.username,
                'phone_number': user.phone_number,
                'role': user.role,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)


class WebAboutYouView(APIView):
    """
    Saves profile details (name, age, gender) from simulator step 3 (/api/auth/about-you/).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        first_name = (request.data.get('first_name') or '').strip()
        age = request.data.get('age')
        gender = request.data.get('gender')

        user = request.user
        if hasattr(user, 'first_name'):
            user.first_name = first_name
        if hasattr(user, 'age') and age:
            user.age = int(age)
        if hasattr(user, 'gender') and gender:
            user.gender = gender
        user.save()

        caller_profile, _ = CallerProfile.objects.get_or_create(user=user)
        if first_name:
            caller_profile.name = first_name
        if age:
            caller_profile.age = int(age)
        if gender:
            caller_profile.gender = gender
        caller_profile.save()

        return Response({
            'success': True,
            'message': 'Profile details updated',
            'next_step': 'INTERESTS'
        }, status=status.HTTP_200_OK)


class WebLoginView(APIView):
    """
    Standard username & password login for web UI (/api/auth/login/).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = (request.data.get('username') or '').strip()
        password = request.data.get('password') or ''

        if not username or not password:
            return Response({'detail': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Allow user to log in via username or phone_number
        user = authenticate(request, username=username, password=password)
        if not user:
            # Try looking up by phone_number
            phone_user = User.objects.filter(phone_number=username).first()
            if phone_user and phone_user.check_password(password):
                user = phone_user

        if not user or not user.is_active:
            return Response({'detail': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Login successful',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'first_name': getattr(user, 'first_name', ''),
            }
        }, status=status.HTTP_200_OK)


# ===================================================
# 8. ADMIN LISTENER MANAGEMENT API (HEADLESS REST API)
# ===================================================
class AdminCreateListenerView(APIView):
    """
    Admin API to create a new Listener username & password:
    POST /api/admin/listeners/create/
    Body:
    {
        "username": "LISTENER_001",
        "password": "ListenerPass123!",
        "language": "English"
    }
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            "endpoint": "/api/admin/listeners/create/",
            "method": "POST",
            "description": "Admin endpoint to provision a new Listener username and password.",
            "sample_body": {
                "username": "LISTENER_001",
                "password": "ListenerPass123!",
                "language": "English"
            }
        }, status=status.HTTP_200_OK)

    def post(self, request):
        username = (request.data.get('username') or request.data.get('listener_id') or '').strip()
        password = request.data.get('password') or ''
        language = (request.data.get('language') or 'English').strip()

        errors = {}
        if not username:
            errors['username'] = ["Listener username is required."]
        elif User.objects.filter(username__iexact=username).exists():
            errors['username'] = [f"Username '{username}' already exists. Please choose another."]

        if not password:
            errors['password'] = ["Password is required."]
        elif len(password) < 6:
            errors['password'] = ["Password must be at least 6 characters."]

        if errors:
            return Response({
                "success": False,
                "message": "Validation failed",
                "errors": errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create user with role='LISTENER'
        user = User(
            username=username,
            role='LISTENER',
            is_active=True,
            is_verified=True
        )
        user.set_password(password)  # Secure PBKDF2 hashing
        user.save()

        # Create linked ListenerProfile
        profile, _ = ListenerProfile.objects.get_or_create(
            user=user,
            defaults={
                'listener_id': username,
                'language': language,
                'is_available': True
            }
        )
        profile.listener_id = username
        profile.language = language
        profile.is_available = True
        profile.save()

        return Response({
            "success": True,
            "message": f"Listener '{username}' created successfully.",
            "data": {
                "id": user.id,
                "username": user.username,
                "listener_id": profile.listener_id,
                "role": user.role,
                "language": profile.language,
                "is_active": user.is_active,
                "is_available": profile.is_available,
                "created_at": user.created_at
            }
        }, status=status.HTTP_201_CREATED)


class AdminListenerListView(APIView):
    """
    Admin API to list all listeners:
    GET /api/admin/listeners/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        listeners = User.objects.filter(role='LISTENER').select_related('listener_profile').order_by('-created_at')
        data = []
        for u in listeners:
            prof = getattr(u, 'listener_profile', None)
            data.append({
                "id": u.id,
                "username": u.username,
                "listener_id": prof.listener_id if prof else u.username,
                "language": prof.language if prof else "English",
                "is_active": u.is_active,
                "is_available": prof.is_available if prof else True,
                "created_at": u.created_at
            })
        return Response({
            "success": True,
            "count": len(data),
            "data": data
        }, status=status.HTTP_200_OK)


class AdminDeleteListenerView(APIView):
    """
    Admin API to delete a Listener by username or ID:
    DELETE /api/admin/listeners/delete/
    POST /api/admin/listeners/delete/
    Query or Body: {"username": "LISTENER_001"} or {"id": 1}
    """
    permission_classes = [permissions.AllowAny]

    def _delete_listener(self, request, identifier=None):
        ident = (
            identifier or 
            request.data.get('username') or 
            request.data.get('listener_id') or 
            request.data.get('id') or 
            request.query_params.get('username') or 
            request.query_params.get('listener_id') or 
            request.query_params.get('id') or 
            ''
        )
        ident_str = str(ident).strip()

        if not ident_str:
            return Response({
                "success": False,
                "message": "Please provide a listener username, listener_id, or id to delete."
            }, status=status.HTTP_400_BAD_REQUEST)

        query = None
        if ident_str.isdigit():
            query = User.objects.filter(id=int(ident_str)).first()

        if not query:
            query = User.objects.filter(username__iexact=ident_str).first()

        if not query:
            prof = ListenerProfile.objects.filter(listener_id__iexact=ident_str).first()
            if prof:
                query = prof.user

        if not query:
            available = list(User.objects.filter(Q(role__in=['LISTENER', 'BUDDY']) | Q(listener_profile__isnull=False)).values_list('username', flat=True))
            return Response({
                "success": False,
                "message": f"Listener '{ident_str}' not found.",
                "available_listeners": available
            }, status=status.HTTP_404_NOT_FOUND)

        target_name = query.username
        target_id = query.id
        query.delete()

        return Response({
            "success": True,
            "message": f"Listener '{target_name}' (ID: {target_id}) and profile have been permanently deleted."
        }, status=status.HTTP_200_OK)

    def delete(self, request, identifier=None):
        return self._delete_listener(request, identifier)

    def post(self, request, identifier=None):
        return self._delete_listener(request, identifier)


# ===================================================
# 9. COMPLETE CRUD FOR CALLER
# ===================================================
class CallerListCreateView(APIView):
    """
    Caller CRUD - List, Create & Delete by Body:
    - GET    /api/callers/ : List all callers
    - POST   /api/callers/ : Create a new caller
    - DELETE /api/callers/ : Delete a caller by JSON body: {"id": 1} or {"phone_number": "+91..."}
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        callers = User.objects.filter(role__in=['CALLER', 'USER']).select_related('caller_profile').order_by('-created_at')
        data = []
        for u in callers:
            cp = getattr(u, 'caller_profile', None)
            data.append({
                "id": u.id,
                "phone_number": u.phone_number,
                "name": cp.name if cp else (u.first_name or u.username),
                "age": cp.age if cp else u.age,
                "gender": cp.gender if cp else u.gender,
                "language": cp.language if cp else "English",
                "interests": cp.interests if cp else [],
                "is_online": cp.is_online if cp else False,
                "is_verified": u.is_verified,
                "created_at": u.created_at,
            })
        return Response({
            "success": True,
            "count": len(data),
            "data": data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        phone_number = (request.data.get('phone_number') or '').strip()
        if not phone_number:
            return Response({
                "success": False,
                "message": "phone_number is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(phone_number=phone_number).exists():
            return Response({
                "success": False,
                "message": f"Caller with phone number '{phone_number}' already exists."
            }, status=status.HTTP_409_CONFLICT)

        name = (request.data.get('name') or '').strip()
        age = request.data.get('age')
        gender = request.data.get('gender')
        language = (request.data.get('language') or 'English').strip()
        interests = request.data.get('interests') or []
        if isinstance(interests, str):
            interests = [i.strip() for i in interests.split(',') if i.strip()]

        username = phone_number
        if User.objects.filter(username=username).exists():
            username = f"{phone_number}_{random.randint(1000, 9999)}"

        user = User.objects.create_user(
            username=username,
            phone_number=phone_number,
            role='CALLER',
            first_name=name,
            is_verified=True,
            is_profile_completed=True
        )
        if request.data.get('password'):
            user.set_password(request.data.get('password'))
            user.save()

        profile, _ = CallerProfile.objects.get_or_create(
            user=user,
            defaults={
                'name': name,
                'age': int(age) if age else None,
                'gender': gender,
                'language': language,
                'interests': interests,
            }
        )

        return Response({
            "success": True,
            "message": f"Caller {phone_number} created successfully.",
            "data": {
                "id": user.id,
                "phone_number": user.phone_number,
                "name": profile.name,
                "age": profile.age,
                "gender": profile.gender,
                "language": profile.language,
                "interests": profile.interests,
                "created_at": user.created_at,
            }
        }, status=status.HTTP_201_CREATED)

    def delete(self, request):
        caller_id = request.data.get('id') or request.query_params.get('id')
        phone_number = (request.data.get('phone_number') or request.query_params.get('phone_number') or '').strip()

        user = None
        if caller_id:
            user = User.objects.filter(id=caller_id, role__in=['CALLER', 'USER']).first()
        elif phone_number:
            user = User.objects.filter(phone_number=phone_number, role__in=['CALLER', 'USER']).first()

        if not user:
            return Response({
                "success": False,
                "message": "Caller not found. Provide a valid 'id' or 'phone_number'."
            }, status=status.HTTP_404_NOT_FOUND)

        target_id = user.id
        target_phone = user.phone_number
        user.delete()

        return Response({
            "success": True,
            "message": f"Caller (ID: {target_id}, Phone: {target_phone}) and profile deleted successfully."
        }, status=status.HTTP_200_OK)


class CallerDetailView(APIView):
    """
    Caller CRUD - Retrieve, Update & Delete by Identifier (ID or Phone):
    - GET    /api/callers/<identifier>/ : Retrieve caller details
    - PUT    /api/callers/<identifier>/ : Update caller
    - PATCH  /api/callers/<identifier>/ : Partial update
    - DELETE /api/callers/<identifier>/ : Delete caller
    - POST   /api/callers/<identifier>/delete/ : Delete caller
    """
    permission_classes = [permissions.AllowAny]

    def _get_caller(self, identifier):
        if not identifier:
            return None
        ident_str = str(identifier).strip()
        if ident_str.isdigit():
            user = User.objects.filter(id=int(ident_str)).first()
            if user:
                return user
        user = User.objects.filter(phone_number=ident_str).first()
        if not user:
            user = User.objects.filter(username__iexact=ident_str).first()
        return user

    def get(self, request, identifier):
        user = self._get_caller(identifier)
        if not user:
            available = list(User.objects.values('id', 'username', 'role', 'phone_number')[:15])
            return Response({
                "success": False,
                "message": f"Caller '{identifier}' not found.",
                "existing_users": available
            }, status=status.HTTP_404_NOT_FOUND)

        cp, _ = CallerProfile.objects.get_or_create(user=user, defaults={'name': user.first_name or user.username})
        return Response({
            "success": True,
            "data": {
                "id": user.id,
                "phone_number": user.phone_number,
                "name": cp.name,
                "age": cp.age,
                "gender": cp.gender,
                "language": cp.language,
                "interests": cp.interests,
                "is_online": cp.is_online,
                "created_at": user.created_at,
            }
        }, status=status.HTTP_200_OK)

    def patch(self, request, identifier):
        return self._update(request, identifier, partial=True)

    def put(self, request, identifier):
        return self._update(request, identifier, partial=False)

    def _update(self, request, identifier, partial=True):
        user = self._get_caller(identifier)
        if not user:
            return Response({"success": False, "message": "Caller not found."}, status=status.HTTP_404_NOT_FOUND)

        cp, _ = CallerProfile.objects.get_or_create(user=user)

        data = request.data
        if 'name' in data:
            cp.name = data['name']
            user.first_name = data['name']
        if 'age' in data:
            cp.age = int(data['age']) if data['age'] else None
        if 'gender' in data:
            cp.gender = data['gender']
        if 'language' in data:
            cp.language = data['language']
        if 'interests' in data:
            interests = data['interests']
            if isinstance(interests, str):
                interests = [i.strip() for i in interests.split(',') if i.strip()]
            cp.interests = interests
        if 'is_online' in data:
            cp.is_online = bool(data['is_online'])
        if 'phone_number' in data and data['phone_number']:
            new_phone = str(data['phone_number']).strip()
            if new_phone != user.phone_number:
                if User.objects.filter(phone_number=new_phone).exclude(id=user.id).exists():
                    return Response({"success": False, "message": "Phone number already taken by another user."}, status=status.HTTP_409_CONFLICT)
                user.phone_number = new_phone
                user.username = new_phone

        user.save()
        cp.save()

        return Response({
            "success": True,
            "message": "Caller updated successfully.",
            "data": {
                "id": user.id,
                "phone_number": user.phone_number,
                "name": cp.name,
                "age": cp.age,
                "gender": cp.gender,
                "language": cp.language,
                "interests": cp.interests,
                "is_online": cp.is_online,
            }
        }, status=status.HTTP_200_OK)

    def delete(self, request, identifier=None):
        ident = identifier or request.data.get('phone_number') or request.data.get('id') or request.query_params.get('phone_number') or request.query_params.get('id')
        user = self._get_caller(ident)
        if not user:
            available = list(User.objects.values('id', 'username', 'role', 'phone_number')[:15])
            return Response({
                "success": False,
                "message": f"Caller '{ident}' not found in database.",
                "existing_users": available
            }, status=status.HTTP_404_NOT_FOUND)

        user_id = user.id
        phone = user.phone_number or user.username
        user.delete()
        return Response({
            "success": True,
            "message": f"Caller '{phone}' (ID: {user_id}) and profile deleted successfully."
        }, status=status.HTTP_200_OK)

    def post(self, request, identifier=None):
        return self.delete(request, identifier)


class CallerDeleteView(APIView):
    """
    DELETE /api/callers/<int:user_id>/delete/
    Deletes (deactivates) a caller account by user_id.
    - Sets user.is_active = False (soft delete)
    - Sets user.caller_profile.is_online = False
    - If ?permanent=true, permanently deletes user
    """
    permission_classes = [permissions.AllowAny]

    def delete(self, request, user_id):
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({
                "success": False,
                "message": "Caller not found."
            }, status=status.HTTP_404_NOT_FOUND)

        if user.role not in ('CALLER', 'USER'):
            return Response({
                "success": False,
                "message": "User is not a caller."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Permanent deletion if requested
        permanent = (
            request.query_params.get('permanent', '').lower() in ('true', '1') or
            (isinstance(request.data, dict) and request.data.get('permanent') is True)
        )
        if permanent:
            user.delete()
            return Response({
                "success": True,
                "message": "Caller deleted successfully."
            }, status=status.HTTP_200_OK)

        # Deactivate caller (soft delete)
        user.is_active = False
        user.save(update_fields=['is_active'])

        if hasattr(user, 'caller_profile') and user.caller_profile:
            user.caller_profile.is_online = False
            user.caller_profile.save(update_fields=['is_online'])

        return Response({
            "success": True,
            "message": "Caller deleted successfully."
        }, status=status.HTTP_200_OK)

    def post(self, request, user_id):
        return self.delete(request, user_id)


class ListenerDeleteView(APIView):
    """
    DELETE /api/listeners/<int:user_id>/delete/
    DELETE /api/listeners/<str:identifier>/delete/
    Deletes (deactivates) a listener account by user_id or username.
    - Sets user.is_active = False (soft delete)
    - Sets listener_profile.is_available = False
    - If ?permanent=true, permanently deletes user
    """
    permission_classes = [permissions.AllowAny]

    def delete(self, request, user_id=None, identifier=None):
        target = user_id or identifier or request.data.get('username') or request.data.get('id')
        if not target:
            return Response({
                "success": False,
                "message": "Listener identifier is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        ident_str = str(target).strip()
        user = None
        if ident_str.isdigit():
            user = User.objects.filter(id=int(ident_str)).first()
        if not user:
            user = User.objects.filter(username__iexact=ident_str).first()
        if not user:
            prof = ListenerProfile.objects.filter(listener_id__iexact=ident_str).first()
            if prof:
                user = prof.user

        if not user:
            return Response({
                "success": False,
                "message": "Listener not found."
            }, status=status.HTTP_404_NOT_FOUND)

        if user.role not in ('LISTENER', 'BUDDY') and not hasattr(user, 'listener_profile'):
            return Response({
                "success": False,
                "message": "User is not a listener."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Permanent deletion if requested
        permanent = (
            request.query_params.get('permanent', '').lower() in ('true', '1') or
            (isinstance(request.data, dict) and request.data.get('permanent') is True)
        )
        if permanent:
            user.delete()
            return Response({
                "success": True,
                "message": "Listener deleted successfully."
            }, status=status.HTTP_200_OK)

        # Deactivate listener (soft delete)
        user.is_active = False
        user.save(update_fields=['is_active'])

        if hasattr(user, 'listener_profile') and user.listener_profile:
            user.listener_profile.is_available = False
            user.listener_profile.save(update_fields=['is_available'])

        return Response({
            "success": True,
            "message": "Listener deleted successfully."
        }, status=status.HTTP_200_OK)

    def post(self, request, user_id=None, identifier=None):
        return self.delete(request, user_id, identifier)


class CallerDeleteDirectView(APIView):
    """
    Dedicated endpoint to delete a caller by ID or Phone:
    Handles GET (direct browser click/URL visit), POST, and DELETE!
    """
    permission_classes = [permissions.AllowAny]

    def _do_delete(self, request, identifier):
        ident_str = str(identifier).strip()
        user = None
        if ident_str.isdigit():
            user = User.objects.filter(id=int(ident_str)).first()
        if not user:
            user = User.objects.filter(phone_number=ident_str).first()
        if not user:
            user = User.objects.filter(username__iexact=ident_str).first()

        if not user:
            available = list(User.objects.values('id', 'username', 'role', 'phone_number')[:15])
            return Response({
                "success": False,
                "message": f"User/Caller '{identifier}' not found in database.",
                "existing_users": available
            }, status=status.HTTP_404_NOT_FOUND)

        target_id = user.id
        target_name = user.username or user.phone_number
        user.delete()
        return Response({
            "success": True,
            "message": f"Caller '{target_name}' (ID: {target_id}) and all associated profile data deleted successfully."
        }, status=status.HTTP_200_OK)

    def get(self, request, identifier):
        return self._do_delete(request, identifier)

    def post(self, request, identifier):
        return self._do_delete(request, identifier)

    def delete(self, request, identifier):
        return self._do_delete(request, identifier)


class ListenerDeleteDirectView(APIView):
    """
    Dedicated endpoint to delete a listener by ID or Username:
    Handles GET (direct browser click/URL visit), POST, and DELETE!
    """
    permission_classes = [permissions.AllowAny]

    def _do_delete(self, request, identifier):
        ident_str = str(identifier).strip()
        user = None
        if ident_str.isdigit():
            user = User.objects.filter(id=int(ident_str)).first()
        if not user:
            user = User.objects.filter(username__iexact=ident_str).first()
        if not user:
            prof = ListenerProfile.objects.filter(listener_id__iexact=ident_str).first()
            if prof:
                user = prof.user

        if not user:
            available = list(User.objects.values('id', 'username', 'role')[:15])
            return Response({
                "success": False,
                "message": f"Listener '{identifier}' not found in database.",
                "existing_users": available
            }, status=status.HTTP_404_NOT_FOUND)

        target_id = user.id
        target_name = user.username
        user.delete()
        return Response({
            "success": True,
            "message": f"Listener '{target_name}' (ID: {target_id}) and all associated profile data deleted successfully."
        }, status=status.HTTP_200_OK)

    def get(self, request, identifier):
        return self._do_delete(request, identifier)

    def post(self, request, identifier):
        return self._do_delete(request, identifier)

    def delete(self, request, identifier):
        return self._do_delete(request, identifier)



# ===================================================
# 10. COMPLETE CRUD FOR LISTENER
# ===================================================
class ListenerListCreateView(APIView):
    """
    Listener CRUD - List, Create & Delete by Body:
    - GET    /api/listeners/ : List all listeners
    - POST   /api/listeners/ : Create a new listener
    - DELETE /api/listeners/ : Delete a listener by JSON body: {"id": 1} or {"username": "..."}
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        listeners = User.objects.filter(role__in=['LISTENER', 'BUDDY']).select_related('listener_profile').order_by('-created_at')
        data = []
        for u in listeners:
            prof = getattr(u, 'listener_profile', None)
            data.append({
                "id": u.id,
                "username": u.username,
                "listener_id": prof.listener_id if prof else u.username,
                "name": prof.name if prof else (u.first_name or u.username),
                "gender": prof.gender if prof else u.gender,
                "language": prof.language if prof else "English",
                "interests": prof.interests if prof else [],
                "is_active": u.is_active,
                "is_available": prof.is_available if prof else True,
                "created_at": u.created_at
            })
        return Response({
            "success": True,
            "count": len(data),
            "data": data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        username = (request.data.get('username') or request.data.get('listener_id') or '').strip()
        password = request.data.get('password') or ''
        name = (request.data.get('name') or '').strip()
        language = (request.data.get('language') or 'English').strip()
        gender = request.data.get('gender')
        interests = request.data.get('interests') or []
        if isinstance(interests, str):
            interests = [i.strip() for i in interests.split(',') if i.strip()]
        is_available = request.data.get('is_available', True)
        if isinstance(is_available, str):
            is_available = is_available.lower() in ('true', '1', 'yes')

        if not username:
            return Response({"success": False, "message": "username / listener_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({"success": False, "message": "password is required."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists() or ListenerProfile.objects.filter(listener_id=username).exists():
            return Response({"success": False, "message": f"Listener '{username}' already exists."}, status=status.HTTP_409_CONFLICT)

        user = User.objects.create_user(
            username=username,
            password=password,
            role='LISTENER',
            first_name=name,
            is_verified=True,
            is_active=True
        )

        profile, _ = ListenerProfile.objects.get_or_create(
            user=user,
            defaults={
                'listener_id': username,
                'name': name,
                'language': language,
                'gender': gender,
                'interests': interests,
                'is_available': is_available
            }
        )

        return Response({
            "success": True,
            "message": f"Listener '{username}' created successfully.",
            "data": {
                "id": user.id,
                "username": user.username,
                "listener_id": profile.listener_id,
                "name": profile.name,
                "language": profile.language,
                "gender": profile.gender,
                "interests": profile.interests,
                "is_available": profile.is_available,
                "created_at": user.created_at
            }
        }, status=status.HTTP_201_CREATED)

    def delete(self, request):
        listener_id = request.data.get('id') or request.query_params.get('id')
        username = (request.data.get('username') or request.data.get('listener_id') or request.query_params.get('username') or '').strip()

        user = None
        if listener_id:
            user = User.objects.filter(id=listener_id, role__in=['LISTENER', 'BUDDY']).first()
        elif username:
            user = User.objects.filter(username=username, role__in=['LISTENER', 'BUDDY']).first()
            if not user:
                prof = ListenerProfile.objects.filter(listener_id=username).first()
                if prof:
                    user = prof.user

        if not user:
            return Response({"success": False, "message": "Listener not found. Provide valid 'id' or 'username'."}, status=status.HTTP_404_NOT_FOUND)

        target_id = user.id
        target_user = user.username
        user.delete()

        return Response({
            "success": True,
            "message": f"Listener '{target_user}' (ID: {target_id}) and profile deleted successfully."
        }, status=status.HTTP_200_OK)


class ListenerDetailView(APIView):
    """
    Listener CRUD - Retrieve, Update & Delete by Identifier (ID or Username):
    - GET    /api/listeners/<identifier>/ : Retrieve listener details
    - PUT    /api/listeners/<identifier>/ : Update listener
    - PATCH  /api/listeners/<identifier>/ : Partial update
    - DELETE /api/listeners/<identifier>/ : Delete listener
    - POST   /api/listeners/<identifier>/delete/ : Delete listener
    """
    permission_classes = [permissions.AllowAny]

    def _get_listener(self, identifier):
        if not identifier:
            return None
        ident_str = str(identifier).strip()
        if ident_str.isdigit():
            user = User.objects.filter(id=int(ident_str)).first()
            if user:
                return user
        user = User.objects.filter(username__iexact=ident_str).first()
        if not user:
            prof = ListenerProfile.objects.filter(listener_id__iexact=ident_str).first()
            if prof:
                user = prof.user
        return user

    def get(self, request, identifier):
        user = self._get_listener(identifier)
        if not user:
            available = list(User.objects.filter(Q(role__in=['LISTENER', 'BUDDY']) | Q(listener_profile__isnull=False)).values_list('username', flat=True))
            return Response({"success": False, "message": f"Listener '{identifier}' not found.", "available_listeners": available}, status=status.HTTP_404_NOT_FOUND)

        lp, _ = ListenerProfile.objects.get_or_create(user=user, defaults={'listener_id': user.username})
        return Response({
            "success": True,
            "data": {
                "id": user.id,
                "username": user.username,
                "listener_id": lp.listener_id,
                "name": lp.name,
                "gender": lp.gender,
                "language": lp.language,
                "interests": lp.interests,
                "is_active": user.is_active,
                "is_available": lp.is_available,
                "created_at": user.created_at,
            }
        }, status=status.HTTP_200_OK)

    def patch(self, request, identifier):
        return self._update(request, identifier, partial=True)

    def put(self, request, identifier):
        return self._update(request, identifier, partial=False)

    def _update(self, request, identifier, partial=True):
        user = self._get_listener(identifier)
        if not user:
            return Response({"success": False, "message": "Listener not found."}, status=status.HTTP_404_NOT_FOUND)

        lp, _ = ListenerProfile.objects.get_or_create(user=user, defaults={'listener_id': user.username})

        data = request.data
        if 'name' in data:
            lp.name = data['name']
            user.first_name = data['name']
        if 'gender' in data:
            lp.gender = data['gender']
        if 'language' in data:
            lp.language = data['language']
        if 'interests' in data:
            interests = data['interests']
            if isinstance(interests, str):
                interests = [i.strip() for i in interests.split(',') if i.strip()]
            lp.interests = interests
        if 'is_available' in data:
            val = data['is_available']
            lp.is_available = val if isinstance(val, bool) else str(val).lower() in ('true', '1', 'yes')
        if 'is_active' in data:
            val = data['is_active']
            user.is_active = val if isinstance(val, bool) else str(val).lower() in ('true', '1', 'yes')
        if 'password' in data and data['password']:
            user.set_password(data['password'])

        user.save()
        lp.save()

        return Response({
            "success": True,
            "message": "Listener updated successfully.",
            "data": {
                "id": user.id,
                "username": user.username,
                "listener_id": lp.listener_id,
                "name": lp.name,
                "gender": lp.gender,
                "language": lp.language,
                "interests": lp.interests,
                "is_active": user.is_active,
                "is_available": lp.is_available,
            }
        }, status=status.HTTP_200_OK)

    def delete(self, request, identifier=None):
        ident = identifier or request.data.get('username') or request.data.get('listener_id') or request.data.get('id') or request.query_params.get('username') or request.query_params.get('id')
        if not ident:
            return Response({
                "success": False,
                "message": "Please provide a listener username, listener_id, or id to delete."
            }, status=status.HTTP_400_BAD_REQUEST)

        user = self._get_listener(ident)
        if not user:
            available = list(User.objects.filter(Q(role__in=['LISTENER', 'BUDDY']) | Q(listener_profile__isnull=False)).values_list('username', flat=True))
            return Response({
                "success": False,
                "message": f"Listener '{ident}' not found.",
                "available_listeners": available
            }, status=status.HTTP_404_NOT_FOUND)

        user_id = user.id
        username = user.username
        user.delete()
        return Response({
            "success": True,
            "message": f"Listener '{username}' (ID: {user_id}) and profile deleted successfully."
        }, status=status.HTTP_200_OK)

    def post(self, request, identifier=None):
        return self.delete(request, identifier)




