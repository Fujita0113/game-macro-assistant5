"""
File encryption and password protection module.

This module provides secure storage and retrieval of macro files with
password protection and encryption using cryptography library.
"""

import json
import os
from typing import Dict, Any
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


class PasswordValidationError(Exception):
    """Exception raised for password validation failures."""

    pass


class MacroFileManager:
    """Manager for encrypting and decrypting macro files."""

    def __init__(self):
        """Initialize the file manager."""
        # Track password attempts per file path
        self._password_attempts = {}

    def _validate_password(self, password: str) -> None:
        """Validate password meets minimum requirements."""
        if not password or len(password) < 8:
            raise PasswordValidationError('Password must be at least 8 characters long')

    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def _check_password_attempts(self, file_path: str) -> None:
        """Check if password attempts exceed maximum (3)."""
        attempts = self._password_attempts.get(file_path, 0)
        if attempts >= 3:
            raise PasswordValidationError('Maximum password attempts exceeded')

    def _increment_password_attempts(self, file_path: str) -> None:
        """Increment password attempts for a file."""
        self._password_attempts[file_path] = (
            self._password_attempts.get(file_path, 0) + 1
        )

    def _reset_password_attempts(self, file_path: str) -> None:
        """Reset password attempts for a file after successful access."""
        if file_path in self._password_attempts:
            del self._password_attempts[file_path]

    def encrypt_file(self, password: str, data: Dict[str, Any]) -> bytes:
        """Encrypt macro data with password."""
        self._validate_password(password)

        # Generate random salt
        salt = os.urandom(16)

        # Derive key from password
        key = self._derive_key_from_password(password, salt)

        # Create Fernet cipher
        cipher = Fernet(key)

        # Convert data to JSON and encrypt
        json_data = json.dumps(data).encode()
        encrypted_data = cipher.encrypt(json_data)

        # Prepend salt to encrypted data
        return salt + encrypted_data

    def decrypt_file(self, password: str, encrypted_data: bytes) -> Dict[str, Any]:
        """Decrypt macro data with password."""
        self._validate_password(password)

        # Check minimum data length (16 bytes salt + some encrypted data)
        if len(encrypted_data) < 32:
            raise PasswordValidationError('File appears to be corrupted')

        try:
            # Extract salt from beginning of data
            salt = encrypted_data[:16]
            actual_encrypted_data = encrypted_data[16:]

            # Derive key from password
            key = self._derive_key_from_password(password, salt)

            # Create Fernet cipher
            cipher = Fernet(key)

            # Decrypt data
            decrypted_data = cipher.decrypt(actual_encrypted_data)

            # Convert back to dictionary
            return json.loads(decrypted_data.decode())

        except InvalidToken:
            # This is specifically a wrong password error
            raise PasswordValidationError('Invalid password')
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Data decrypted but is not valid JSON
            raise PasswordValidationError('File appears to be corrupted')
        except Exception:
            # This could be other corruption issues
            raise PasswordValidationError('File appears to be corrupted')

    def save_macro_file(
        self, file_path: str, password: str, data: Dict[str, Any]
    ) -> None:
        """Save macro data to encrypted file."""
        if not file_path.endswith('.gma.json'):
            raise ValueError('File must have .gma.json extension')

        encrypted_data = self.encrypt_file(password, data)

        with open(file_path, 'wb') as f:
            f.write(encrypted_data)

    def load_macro_file(self, file_path: str, password: str) -> Dict[str, Any]:
        """Load macro data from encrypted file."""
        self._check_password_attempts(file_path)

        try:
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()

            # Try to decrypt
            decrypted_data = self.decrypt_file(password, encrypted_data)

            # Success - reset attempts counter
            self._reset_password_attempts(file_path)
            return decrypted_data

        except PasswordValidationError:
            # Increment attempts on password failure
            self._increment_password_attempts(file_path)
            raise
        except Exception as e:
            # Other errors (file not found, etc.)
            raise PasswordValidationError(f'Failed to load file: {str(e)}')
