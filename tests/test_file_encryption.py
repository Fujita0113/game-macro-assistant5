"""
Test module for file encryption and password protection functionality.

This module tests the secure storage and retrieval of macro files with
password protection and encryption as required by the specifications.
"""

import json
import pytest
import tempfile
import os

from src.core.file_encryption import MacroFileManager, PasswordValidationError


class TestMacroFileManager:
    """Test cases for MacroFileManager encryption/decryption."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = MacroFileManager()
        self.test_password = 'test_password_123'
        self.short_password = 'short'
        self.test_data = {
            'macro_name': 'test_macro',
            'events': [
                {'type': 'mouse_click', 'button': 'left', 'x': 100, 'y': 200},
                {'type': 'key_press', 'key': 'a'},
            ],
            'created_at': '2024-01-01T00:00:00',
        }

    def test_encrypt_macro_file(self):
        """Test that macro data can be encrypted with a password."""
        encrypted_data = self.manager.encrypt_file(self.test_password, self.test_data)

        # Encrypted data should be bytes
        assert isinstance(encrypted_data, bytes)

        # Encrypted data should be different from original
        original_json = json.dumps(self.test_data).encode()
        assert encrypted_data != original_json

        # Encrypted data should not be empty
        assert len(encrypted_data) > 0

    def test_decrypt_macro_file(self):
        """Test that encrypted macro data can be decrypted with correct password."""
        # First encrypt the data
        encrypted_data = self.manager.encrypt_file(self.test_password, self.test_data)

        # Then decrypt it
        decrypted_data = self.manager.decrypt_file(self.test_password, encrypted_data)

        # Decrypted data should match original
        assert decrypted_data == self.test_data

    def test_decrypt_with_wrong_password(self):
        """Test that decryption fails with incorrect password."""
        encrypted_data = self.manager.encrypt_file(self.test_password, self.test_data)

        with pytest.raises(PasswordValidationError) as exc_info:
            self.manager.decrypt_file('wrong_password', encrypted_data)

        assert 'Invalid password' in str(exc_info.value)

    def test_password_length_validation(self):
        """Test that passwords shorter than 8 characters are rejected."""
        with pytest.raises(PasswordValidationError) as exc_info:
            self.manager.encrypt_file(self.short_password, self.test_data)

        assert 'Password must be at least 8 characters' in str(exc_info.value)

    def test_empty_password_validation(self):
        """Test that empty passwords are rejected."""
        with pytest.raises(PasswordValidationError) as exc_info:
            self.manager.encrypt_file('', self.test_data)

        assert 'Password must be at least 8 characters' in str(exc_info.value)

    def test_save_macro_file(self):
        """Test saving encrypted macro to file."""
        with tempfile.NamedTemporaryFile(suffix='.gma.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            self.manager.save_macro_file(tmp_path, self.test_password, self.test_data)

            # File should exist
            assert os.path.exists(tmp_path)

            # File should have .gma.json extension
            assert tmp_path.endswith('.gma.json')

            # File should contain encrypted data (not plain JSON)
            with open(tmp_path, 'rb') as f:
                file_content = f.read()
                assert file_content != json.dumps(self.test_data).encode()

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_load_macro_file(self):
        """Test loading and decrypting macro from file."""
        with tempfile.NamedTemporaryFile(suffix='.gma.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Save file first
            self.manager.save_macro_file(tmp_path, self.test_password, self.test_data)

            # Then load it
            loaded_data = self.manager.load_macro_file(tmp_path, self.test_password)

            # Should match original data
            assert loaded_data == self.test_data

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_password_attempts_tracking(self):
        """Test that password attempts are tracked and limited to 3."""
        with tempfile.NamedTemporaryFile(suffix='.gma.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Save file first
            self.manager.save_macro_file(tmp_path, self.test_password, self.test_data)

            # Try with wrong password 3 times
            for attempt in range(3):
                with pytest.raises(PasswordValidationError):
                    self.manager.load_macro_file(tmp_path, 'wrong_password')

            # Fourth attempt should raise MaxAttemptsExceededError
            with pytest.raises(PasswordValidationError) as exc_info:
                self.manager.load_macro_file(tmp_path, 'wrong_password')

            assert 'Maximum password attempts exceeded' in str(exc_info.value)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_password_attempts_reset_on_success(self):
        """Test that password attempts reset after successful login."""
        with tempfile.NamedTemporaryFile(suffix='.gma.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Save file first
            self.manager.save_macro_file(tmp_path, self.test_password, self.test_data)

            # Try with wrong password twice
            for attempt in range(2):
                with pytest.raises(PasswordValidationError):
                    self.manager.load_macro_file(tmp_path, 'wrong_password')

            # Then succeed with correct password
            loaded_data = self.manager.load_macro_file(tmp_path, self.test_password)
            assert loaded_data == self.test_data

            # Should be able to try wrong password again (counter reset)
            with pytest.raises(PasswordValidationError):
                self.manager.load_macro_file(tmp_path, 'wrong_password')

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_file_extension_enforcement(self):
        """Test that .gma.json extension is enforced."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            with pytest.raises(ValueError) as exc_info:
                self.manager.save_macro_file(
                    tmp_path, self.test_password, self.test_data
                )

            assert 'File must have .gma.json extension' in str(exc_info.value)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_corrupted_file_handling(self):
        """Test handling of corrupted encrypted files."""
        with tempfile.NamedTemporaryFile(suffix='.gma.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Write corrupted data to file
            with open(tmp_path, 'wb') as f:
                f.write(b'corrupted_data_not_encrypted')

            with pytest.raises(PasswordValidationError) as exc_info:
                self.manager.load_macro_file(tmp_path, self.test_password)

            assert 'File appears to be corrupted' in str(exc_info.value)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestPasswordValidationError:
    """Test cases for PasswordValidationError exception."""

    def test_error_message_preservation(self):
        """Test that error messages are preserved correctly."""
        message = 'Test error message'
        error = PasswordValidationError(message)

        assert str(error) == message
        assert error.args[0] == message

    def test_error_inheritance(self):
        """Test that PasswordValidationError inherits from Exception."""
        error = PasswordValidationError('test')
        assert isinstance(error, Exception)


if __name__ == '__main__':
    pytest.main([__file__])
