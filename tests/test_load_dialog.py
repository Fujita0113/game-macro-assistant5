"""
Test module for load dialog functionality.

This module tests the macro file loading dialog with password protection
and error handling according to issue #16 requirements.
"""

from unittest.mock import patch
from tkinter import filedialog, messagebox
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from core.file_encryption import PasswordValidationError


class TestLoadDialogFileSelection:
    """Test file selection functionality of load dialog."""

    def test_should_open_file_dialog_when_load_requested(self):
        """Test that file dialog opens when load is requested."""
        with patch.object(filedialog, 'askopenfilename') as mock_dialog:
            mock_dialog.return_value = 'test.gma.json'

            from ui.load_dialog import LoadDialog

            dialog = LoadDialog()

            result = dialog.open_file()
            assert mock_dialog.called
            assert result == 'test.gma.json'


class TestLoadDialogPasswordInput:
    """Test password input functionality of load dialog."""

    def test_should_prompt_for_password_when_file_selected(self):
        """Test that password prompt appears after file selection."""
        with patch('tkinter.simpledialog.askstring') as mock_password:
            mock_password.return_value = 'password123'

            from ui.load_dialog import LoadDialog

            dialog = LoadDialog()

            result = dialog.prompt_password()
            assert mock_password.called
            assert result == 'password123'


class TestLoadDialogPasswordRetries:
    """Test password retry functionality of load dialog."""

    def test_should_retry_password_on_wrong_password_up_to_3_times(self):
        """Test that dialog allows up to 3 password attempts."""
        with (
            patch.object(filedialog, 'askopenfilename') as mock_dialog,
            patch('tkinter.simpledialog.askstring') as mock_password,
            patch.object(messagebox, 'showerror'),
            patch('os.path.exists') as mock_exists,
        ):
            mock_dialog.return_value = 'test.gma.json'
            mock_exists.return_value = True
            mock_password.side_effect = [
                'wrong1',
                'wrong2',
                'wrong3',
            ]  # 3 wrong passwords

            from ui.load_dialog import LoadDialog

            dialog = LoadDialog()

            # Mock the file manager to raise password errors
            with patch.object(dialog.file_manager, 'load_macro_file') as mock_load:
                mock_load.side_effect = PasswordValidationError('Invalid password')

                result = dialog.load_with_retry('test.gma.json')
                assert result is None  # Should fail after 3 attempts
                assert mock_password.call_count == 3


class TestLoadDialogErrorHandling:
    """Test error handling functionality of load dialog."""

    def test_should_show_error_when_file_not_found(self):
        """Test that error message is shown when file does not exist."""
        with (
            patch('os.path.exists') as mock_exists,
            patch.object(messagebox, 'showerror') as mock_error,
        ):
            mock_exists.return_value = False

            from ui.load_dialog import LoadDialog

            dialog = LoadDialog()

            result = dialog.load_with_retry('nonexistent.gma.json')
            assert result is None
            mock_error.assert_called_with('エラー', 'ファイルが見つかりません')
