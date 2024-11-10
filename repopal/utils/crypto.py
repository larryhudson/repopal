"""Utilities for encrypting and decrypting sensitive data"""

import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class CredentialEncryption:
    """Handles encryption and decryption of service credentials"""

    def __init__(self, master_key: str, salt: Optional[bytes] = None):
        """Initialize with master key and optional salt"""
        if salt is None:
            salt = b'repopal'  # Default salt, should be overridden in production
        
        # Derive a key from the master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        """Encrypt a string value"""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        """Decrypt an encrypted string value"""
        return self.fernet.decrypt(encrypted.encode()).decode()
