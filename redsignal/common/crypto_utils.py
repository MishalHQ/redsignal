"""
Cryptographic utilities for RedSignal platform.
Provides encryption, decryption, and key management for secure communications.
"""

import os
import base64
import hashlib
from typing import Tuple, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..common.logger import get_logger

logger = get_logger(__name__)


class CryptoManager:
    """Handles encryption and decryption operations."""

    def __init__(self):
        self.symmetric_key: Optional[bytes] = None
        self.private_key: Optional[rsa.RSAPrivateKey] = None
        self.public_key: Optional[rsa.RSAPublicKey] = None

    def generate_symmetric_key(self) -> str:
        """Generate a new symmetric encryption key."""
        key = Fernet.generate_key()
        self.symmetric_key = key
        return base64.urlsafe_b64encode(key).decode()

    def set_symmetric_key(self, key_string: str):
        """Set symmetric key from string."""
        try:
            self.symmetric_key = base64.urlsafe_b64decode(key_string.encode())
        except Exception as e:
            logger.error(f"Failed to set symmetric key: {e}")
            raise ValueError("Invalid key format")

    def encrypt_symmetric(self, data: str) -> str:
        """Encrypt data using symmetric encryption."""
        if not self.symmetric_key:
            raise ValueError("No symmetric key available")

        try:
            fernet = Fernet(self.symmetric_key)
            encrypted_data = fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Symmetric encryption failed: {e}")
            raise

    def decrypt_symmetric(self, encrypted_data: str) -> str:
        """Decrypt data using symmetric encryption."""
        if not self.symmetric_key:
            raise ValueError("No symmetric key available")

        try:
            fernet = Fernet(self.symmetric_key)
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Symmetric decryption failed: {e}")
            raise

    def generate_rsa_keypair(self, key_size: int = 2048) -> Tuple[str, str]:
        """Generate RSA key pair and return as PEM strings."""
        try:
            # Generate private key
            self.private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=key_size
            )

            # Get public key
            self.public_key = self.private_key.public_key()

            # Serialize keys
            private_pem = (
                self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
                .decode()
            )

            public_pem = (
                self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
                .decode()
            )

            return private_pem, public_pem

        except Exception as e:
            logger.error(f"RSA key generation failed: {e}")
            raise

    def load_private_key(self, private_key_pem: str):
        """Load private key from PEM string."""
        try:
            self.private_key = serialization.load_pem_private_key(
                private_key_pem.encode(), password=None
            )
            self.public_key = self.private_key.public_key()
        except Exception as e:
            logger.error(f"Failed to load private key: {e}")
            raise

    def load_public_key(self, public_key_pem: str):
        """Load public key from PEM string."""
        try:
            self.public_key = serialization.load_pem_public_key(public_key_pem.encode())
        except Exception as e:
            logger.error(f"Failed to load public key: {e}")
            raise

    def encrypt_asymmetric(self, data: str) -> str:
        """Encrypt data using RSA public key."""
        if not self.public_key:
            raise ValueError("No public key available")

        try:
            encrypted_data = self.public_key.encrypt(
                data.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Asymmetric encryption failed: {e}")
            raise

    def decrypt_asymmetric(self, encrypted_data: str) -> str:
        """Decrypt data using RSA private key."""
        if not self.private_key:
            raise ValueError("No private key available")

        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.private_key.decrypt(
                decoded_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Asymmetric decryption failed: {e}")
            raise

    def derive_key_from_password(
        self, password: str, salt: Optional[bytes] = None
    ) -> Tuple[bytes, bytes]:
        """Derive encryption key from password using PBKDF2."""
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        key = kdf.derive(password.encode())
        return key, salt

    def hash_data(self, data: str, algorithm: str = "sha256") -> str:
        """Hash data using specified algorithm."""
        try:
            if algorithm == "md5":
                hash_obj = hashlib.md5()
            elif algorithm == "sha1":
                hash_obj = hashlib.sha1()
            elif algorithm == "sha256":
                hash_obj = hashlib.sha256()
            elif algorithm == "sha512":
                hash_obj = hashlib.sha512()
            else:
                raise ValueError(f"Unsupported hash algorithm: {algorithm}")

            hash_obj.update(data.encode())
            return hash_obj.hexdigest()

        except Exception as e:
            logger.error(f"Hashing failed: {e}")
            raise


def create_crypto_manager() -> CryptoManager:
    """Factory function to create crypto manager."""
    return CryptoManager()

