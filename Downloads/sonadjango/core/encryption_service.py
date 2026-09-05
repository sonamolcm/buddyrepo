from cryptography.fernet import Fernet
from django.conf import settings


class EncryptionService:

    def __init__(self):
        self.cipher = Fernet(settings.ENCRYPTION_KEY)

    def encrypt(self, value):
        return self.cipher.encrypt(
            value.encode()
        ).decode()

    def decrypt(self, value):
        return self.cipher.decrypt(
            value.encode()
        ).decode()

    