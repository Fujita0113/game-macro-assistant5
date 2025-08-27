"""
AES encryption service for secure macro data storage.

This module provides AES-256-GCM encryption functionality for securing
macro recording data with password-based key derivation.
"""

import json
import hashlib
import secrets
from typing import Dict, Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag


class EncryptionService:
    """Service for encrypting and decrypting macro data."""

    # Security constants
    SALT_SIZE = 32  # 256 bits
    NONCE_SIZE = 12  # 96 bits for GCM
    KEY_LENGTH = 32  # 256 bits
    ITERATIONS = 100000  # PBKDF2 iterations

    def __init__(self):
        """Initialize the encryption service."""
        pass

    def encrypt_data(self, data: Dict[str, Any], password: str) -> bytes:
        """
        Encrypt macro data with AES-256-GCM.

        Args:
            data: Dictionary data to encrypt
            password: Password for encryption

        Returns:
            bytes: Encrypted data with salt, nonce, and ciphertext

        Raises:
            EncryptionError: If encryption fails
        """
        try:
            # Convert data to JSON bytes
            json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')

            # Generate random salt and nonce
            salt = secrets.token_bytes(self.SALT_SIZE)
            nonce = secrets.token_bytes(self.NONCE_SIZE)

            # Derive key from password using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=self.KEY_LENGTH,
                salt=salt,
                iterations=self.ITERATIONS,
            )
            key = kdf.derive(password.encode('utf-8'))

            # Encrypt data using AES-GCM
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, json_data, None)

            # Combine salt, nonce, and ciphertext
            encrypted_data = salt + nonce + ciphertext

            return encrypted_data

        except Exception as e:
            raise EncryptionError(f'Failed to encrypt data: {e}') from e

    def decrypt_data(self, encrypted_data: bytes, password: str) -> Dict[str, Any]:
        """
        Decrypt macro data from AES-256-GCM.

        Args:
            encrypted_data: Encrypted data bytes
            password: Password for decryption

        Returns:
            Dict[str, Any]: Decrypted data

        Raises:
            EncryptionError: If decryption fails
            InvalidPasswordError: If password is incorrect
        """
        try:
            # Validate minimum size
            min_size = self.SALT_SIZE + self.NONCE_SIZE
            if len(encrypted_data) < min_size:
                raise EncryptionError('Invalid encrypted data format')

            # Extract salt, nonce, and ciphertext
            salt = encrypted_data[: self.SALT_SIZE]
            nonce = encrypted_data[self.SALT_SIZE : self.SALT_SIZE + self.NONCE_SIZE]
            ciphertext = encrypted_data[self.SALT_SIZE + self.NONCE_SIZE :]

            # Derive key from password using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=self.KEY_LENGTH,
                salt=salt,
                iterations=self.ITERATIONS,
            )
            key = kdf.derive(password.encode('utf-8'))

            # Decrypt data using AES-GCM
            aesgcm = AESGCM(key)
            json_data = aesgcm.decrypt(nonce, ciphertext, None)

            # Parse JSON data
            data = json.loads(json_data.decode('utf-8'))

            return data

        except InvalidTag as e:
            # AES-GCM authentication failed - wrong password
            raise InvalidPasswordError('Incorrect password') from e
        except Exception as e:
            # Other errors
            raise EncryptionError(f'Failed to decrypt data: {e}') from e

    def validate_password(self, password: str) -> bool:
        """
        Validate password strength.

        Args:
            password: Password to validate

        Returns:
            bool: True if password meets requirements

        Raises:
            PasswordValidationError: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise PasswordValidationError('Password must be at least 8 characters long')

        # Additional validation can be added here
        # (uppercase, lowercase, numbers, special characters)

        return True

    def hash_password(self, password: str) -> str:
        """
        Create a hash of the password for verification.

        Args:
            password: Password to hash

        Returns:
            str: SHA-256 hash of the password
        """
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    @staticmethod
    def generate_secure_filename(base_name: str) -> str:
        """
        Generate a secure filename with timestamp and random suffix.

        Args:
            base_name: Base name for the file

        Returns:
            str: Secure filename
        """
        import time

        timestamp = int(time.time())
        random_suffix = secrets.token_hex(4)
        return f'{base_name}_{timestamp}_{random_suffix}.gma.json'


class EncryptionError(Exception):
    """Base exception for encryption operations."""

    pass


class InvalidPasswordError(EncryptionError):
    """Exception raised when password is incorrect."""

    pass


class PasswordValidationError(EncryptionError):
    """Exception raised when password doesn't meet requirements."""

    pass
