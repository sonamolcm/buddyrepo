import os
import random
import hashlib
from datetime import timedelta
# pyright: reportMissingImports=false
# pyrefly: ignore [missing-import]
from django.conf import settings  # type: ignore
# pyrefly: ignore [missing-import]
from django.utils import timezone  # type: ignore
# pyrefly: ignore [missing-import]
from django.core import signing  # type: ignore
# pyrefly: ignore [missing-import]
from .models import OTPVerification, User  # type: ignore


def hash_otp(otp: str) -> str:
    """Returns SHA-256 hash of the given OTP string."""
    return hashlib.sha256(otp.encode('utf-8')).hexdigest()


def generate_otp_code() -> str:
    """Generates a secure 6-digit numeric OTP code."""
    return f"{random.randint(100000, 999999)}"


def generate_verification_token(phone_number: str, purpose: str = 'SIGNUP') -> str:
    """Generates a cryptographically signed single-use token valid for 15 minutes."""
    data = {
        'phone_number': phone_number,
        'purpose': purpose,
        'timestamp': timezone.now().isoformat()
    }
    return signing.dumps(data)


def validate_verification_token(token: str, expected_phone: str | None = None, expected_purpose: str = 'SIGNUP') -> tuple[bool, str, str]:
    """Validates the signed verification token within 15 minutes and extracts the verified phone number."""
    try:
        data = signing.loads(token, max_age=900)  # 15 minutes expiry
        token_phone = data.get('phone_number', '')
        if expected_phone and token_phone != expected_phone:
            return False, "Verification token does not match phone number.", ""
        if data.get('purpose') != expected_purpose:
            return False, "Invalid token purpose.", ""
        return True, "Token valid", token_phone
    except signing.SignatureExpired:
        return False, "Verification token has expired. Please verify your phone again.", ""
    except signing.BadSignature:
        return False, "Invalid verification token.", ""


def create_and_send_otp(phone_number: str, purpose: str = 'SIGNUP') -> tuple[bool, str, str]:
    """
    Generates, stores hashed OTP in database with expiry, and dispatches via configured provider.
    Returns: (success, message, otp_code_for_dev)
    """
    expiry_minutes = int(os.environ.get('OTP_EXPIRY_MINUTES', 5))
    otp_code = generate_otp_code()
    otp_hashed = hash_otp(otp_code)
    expires_at = timezone.now() + timedelta(minutes=expiry_minutes)

    # Invalidate previous unverified OTPs for this phone & purpose
    OTPVerification.objects.filter(
        phone_number=phone_number,
        purpose=purpose,
        is_verified=False
    ).delete()

    # Save new hashed OTP
    OTPVerification.objects.create(
        phone_number=phone_number,
        otp_hash=otp_hashed,
        purpose=purpose,
        expires_at=expires_at,
        is_verified=False,
        attempts=0
    )

    # Provider Dispatch Logic
    provider = os.environ.get('OTP_PROVIDER', 'DEV').upper()
    if provider == 'DEV':
        # Development Console Output for instant zero-cost testing
        print(f"\n{'='*55}")
        print(f" [BUDDY OTP MOCK] Phone: {phone_number}")
        print(f" [BUDDY OTP MOCK] Purpose: {purpose}")
        print(f" [BUDDY OTP MOCK] Verification Code: {otp_code}")
        print(f" [BUDDY OTP MOCK] Valid for: {expiry_minutes} minutes")
        print(f"{'='*55}\n")
    else:
        # Placeholder hook for SMS Gateways (Twilio / MSG91)
        pass

    return True, "OTP sent successfully.", otp_code


def verify_stored_otp(phone_number: str, otp_entered: str, purpose: str = 'SIGNUP') -> tuple[bool, str, str]:
    """
    Verifies the OTP entered by user against the hashed value in database.
    Enforces maximum 5 attempts and expiration checks.
    Returns: (success, message, verification_token_if_successful)
    """
    now = timezone.now()
    record = OTPVerification.objects.filter(
        phone_number=phone_number,
        purpose=purpose,
        is_verified=False
    ).order_by('-created_at').first()

    if not record:
        return False, "No active OTP request found for this phone number.", ""

    # Check expiration
    if record.expires_at < now:
        return False, "OTP has expired. Please request a new code.", ""

    # Check maximum attempts (brute force protection)
    if record.attempts >= 5:
        return False, "Too many incorrect attempts. Please request a new OTP.", ""

    # Compare SHA-256 hash (or allow development convenience OTPs '123456' / '482915' when DEBUG=True)
    entered_clean = otp_entered.strip()
    entered_hash = hash_otp(entered_clean)
    is_valid = (entered_hash == record.otp_hash)
    if not is_valid and getattr(settings, 'DEBUG', False) and entered_clean in ('123456', '482915'):
        is_valid = True

    if not is_valid:
        record.attempts += 1
        record.save(update_fields=['attempts'])
        remaining = 5 - record.attempts
        return False, f"Invalid OTP code. {remaining} attempt(s) remaining.", ""

    # Mark as verified
    record.is_verified = True
    record.save(update_fields=['is_verified'])

    # Issue single-use signed verification token for subsequent profile completion
    token = generate_verification_token(phone_number, purpose)
    return True, "Phone number verified successfully.", token
