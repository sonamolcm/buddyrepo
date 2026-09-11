# pyright: reportMissingImports=false
# pyrefly: ignore [missing-import]
import os
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

_firebase_app = None


def get_firebase_app():
    """
    Safely and lazily initializes the Firebase Admin SDK app instance once.
    Reuses existing default app if already initialized.
    Returns the app instance or None if not configured/available.
    """
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError:
        logger.info("firebase-admin package is not installed or unavailable. FCM notifications disabled.")
        return None

    # Check if Firebase is already initialized
    try:
        _firebase_app = firebase_admin.get_app()
        return _firebase_app
    except ValueError:
        # Default app has not been initialized yet
        pass

    # Read credentials from settings or environment variables
    cred_json_str = getattr(settings, 'FIREBASE_CREDENTIALS_JSON', '') or os.environ.get('FIREBASE_CREDENTIALS_JSON', '')
    cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', '') or os.environ.get('FIREBASE_CREDENTIALS_PATH', '')
    if cred_path:
        cred_path = str(cred_path).strip().strip("'").strip('"')

    cred = None
    if cred_json_str and cred_json_str.strip():
        try:
            cert_dict = json.loads(cred_json_str.strip())
            cred = credentials.Certificate(cert_dict)
        except Exception as exc:
            logger.error("Failed to parse FIREBASE_CREDENTIALS_JSON: %s", str(exc))
    elif cred_path and os.path.exists(cred_path):
        try:
            cred = credentials.Certificate(cred_path)
        except Exception as exc:
            logger.error("Failed to load FIREBASE_CREDENTIALS_PATH: %s", str(exc))

    if cred is None:
        try:
            # Fall back to Google Application Default Credentials if present
            cred = credentials.ApplicationDefault()
        except Exception:
            cred = None

    if cred is None:
        logger.info("Firebase credentials not configured. FCM sending is disabled.")
        return None

    try:
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully.")
        return _firebase_app
    except Exception as exc:
        logger.error("Error initializing Firebase Admin SDK: %s", str(exc))
        return None


def send_incoming_call_fcm(
    fcm_token: str | None,
    call_id: int | str,
    channel_name: str,
    caller_id: int | str,
    caller_name: str,
    call_type: str = "audio",
) -> tuple[bool, str]:
    """
    Sends an FCM data push notification for an incoming call to an Agent.

    Notification data payload:
    {
        "type": "incoming_call",
        "call_id": "<call.id>",
        "channel_name": "<call.channel_name>",
        "caller_id": "<caller.id>",
        "caller_name": "<caller name>",
        "call_type": "audio"
    }

    Returns:
        (success: bool, message: str)
    """
    token = (fcm_token or "").strip()
    if not token:
        logger.info("Agent has no FCM device token. Skipping push notification.")
        return False, "Agent has no FCM token"

    app = get_firebase_app()
    if not app:
        logger.info("Firebase Admin SDK not initialized. Skipping FCM notification.")
        return False, "Firebase Admin SDK not initialized"

    try:
        from firebase_admin import messaging
    except ImportError:
        logger.warning("firebase_admin.messaging is not available.")
        return False, "messaging module unavailable"

    data_payload = {
        "type": "incoming_call",
        "call_id": str(call_id),
        "channel_name": str(channel_name),
        "caller_id": str(caller_id),
        "caller_name": str(caller_name or "Caller"),
        "call_type": "audio",
    }

    try:
        message = messaging.Message(
            data=data_payload,
            token=token,
            android=messaging.AndroidConfig(
                priority="high",
                data=data_payload,
            ),
        )
        response = messaging.send(message, app=app)
        logger.info("FCM incoming call notification sent successfully: %s", response)
        return True, "FCM sent successfully"
    except Exception as exc:
        logger.warning("Failed to send incoming call FCM notification: %s", str(exc))
        return False, f"FCM send failed: {str(exc)}"


def check_firebase_status() -> dict:
    """
    Diagnostic helper to safely verify Firebase Admin SDK initialization
    and project connection without exposing private keys or secrets.
    """
    cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', '') or os.environ.get('FIREBASE_CREDENTIALS_PATH', '')
    if cred_path:
        cred_path = str(cred_path).strip().strip("'").strip('"')

    file_exists = bool(cred_path and os.path.exists(cred_path))

    try:
        import firebase_admin
    except ImportError:
        return {
            "sdk_installed": False,
            "initialized": False,
            "project_id": None,
            "credentials_file_found": file_exists,
            "message": "firebase-admin Python package is not installed."
        }

    app = get_firebase_app()
    if not app:
        return {
            "sdk_installed": True,
            "initialized": False,
            "project_id": None,
            "credentials_file_found": file_exists,
            "message": "Firebase Admin SDK could not be initialized. Check credentials file path."
        }

    project_id = getattr(app, 'project_id', None)
    return {
        "sdk_installed": True,
        "initialized": True,
        "project_id": project_id,
        "credentials_file_found": file_exists,
        "message": "Firebase Admin SDK initialized successfully."
    }

