"""
Tests for the save dialog UI component.

This module tests the save dialog functionality including validation,
callback integration, and mock-based testing for the save operations.
"""

import pytest
from unittest.mock import Mock
import time
from src.core.macro_data import MacroRecording
from src.ui.save_dialog import SaveDialog


class TestSaveDialog:
    """Test suite for SaveDialog class."""

    # Use the existing tk_root fixture from conftest.py

    @pytest.fixture
    def sample_macro_recording(self):
        """Create a sample MacroRecording for testing."""
        return MacroRecording(
            name='test-macro',
            created_at=time.time(),
            operations=[],
            metadata={'version': '1.0'},
        )

    @pytest.fixture
    def mock_callback(self):
        """Create a mock callback function for testing."""
        return Mock()

    def test_save_dialog_creation(self, tk_root, sample_macro_recording, mock_callback):
        """Test that SaveDialog can be created successfully."""
        # TDD Cycle 1 - Test: Create basic dialog
        dialog = SaveDialog(tk_root, sample_macro_recording, mock_callback)
        assert dialog is not None
        assert dialog.root == tk_root
        assert dialog.macro_data == sample_macro_recording
        assert dialog.save_callback == mock_callback

    def test_save_dialog_ui_elements_present(
        self, tk_root, sample_macro_recording, mock_callback
    ):
        """Test that all required UI elements are present."""
        # TDD Cycle 2 - Test: UI elements exist
        dialog = SaveDialog(tk_root, sample_macro_recording, mock_callback)

        # Check that the dialog has the required attributes for UI elements
        assert hasattr(dialog, 'filename_entry')
        assert hasattr(dialog, 'password_entry')
        assert hasattr(dialog, 'confirm_password_entry')
        assert hasattr(dialog, 'save_button')
        assert hasattr(dialog, 'cancel_button')
        assert hasattr(dialog, 'message_label')

    def test_successful_save_with_callback(
        self, tk_root, sample_macro_recording, mock_callback
    ):
        """Test successful save operation with mock callback."""
        # TDD Cycle 6 - Test: Mock-based save success test
        dialog = SaveDialog(tk_root, sample_macro_recording, mock_callback)

        # Set up test input values
        dialog.filename_entry.insert(0, 'test-macro')
        dialog.password_entry.insert(0, 'password123')
        dialog.confirm_password_entry.insert(0, 'password123')

        # Mock successful callback
        mock_callback.return_value = True

        # Trigger save operation
        dialog._perform_save()

        # Verify callback was called with correct parameters
        mock_callback.assert_called_once_with(
            filename='test-macro.gma.json',
            password='password123',
            macro_data=sample_macro_recording.to_dict(),
        )

        # Verify success message is displayed
        assert '成功' in dialog.message_label.cget('text')

    def test_password_validation_length(
        self, tk_root, sample_macro_recording, mock_callback
    ):
        """Test password validation for minimum length."""
        # TDD Cycle 3 - Test: Password validation
        dialog = SaveDialog(tk_root, sample_macro_recording, mock_callback)

        # Set up test input with short password
        dialog.filename_entry.insert(0, 'test-macro')
        dialog.password_entry.insert(0, 'short')
        dialog.confirm_password_entry.insert(0, 'short')

        # Trigger save operation
        dialog._perform_save()

        # Verify error message for short password
        assert '8文字以上' in dialog.message_label.cget('text')
        # Verify callback was not called
        mock_callback.assert_not_called()

    def test_password_confirmation_mismatch(
        self, tk_root, sample_macro_recording, mock_callback
    ):
        """Test password confirmation validation."""
        # TDD Cycle 4 - Test: Password confirmation validation
        dialog = SaveDialog(tk_root, sample_macro_recording, mock_callback)

        # Set up test input with mismatched passwords
        dialog.filename_entry.insert(0, 'test-macro')
        dialog.password_entry.insert(0, 'password123')
        dialog.confirm_password_entry.insert(0, 'different123')

        # Trigger save operation
        dialog._perform_save()

        # Verify error message for password mismatch
        assert 'パスワードが一致しません' in dialog.message_label.cget('text')
        # Verify callback was not called
        mock_callback.assert_not_called()

    def test_filename_validation_empty(
        self, tk_root, sample_macro_recording, mock_callback
    ):
        """Test filename validation for empty input."""
        # TDD Cycle 5 - Test: Filename validation
        dialog = SaveDialog(tk_root, sample_macro_recording, mock_callback)

        # Set up test input with empty filename
        dialog.filename_entry.insert(0, '')
        dialog.password_entry.insert(0, 'password123')
        dialog.confirm_password_entry.insert(0, 'password123')

        # Trigger save operation
        dialog._perform_save()

        # Verify error message for empty filename
        assert 'ファイル名を入力してください' in dialog.message_label.cget('text')
        # Verify callback was not called
        mock_callback.assert_not_called()

    def test_filename_extension_auto_addition(
        self, tk_root, sample_macro_recording, mock_callback
    ):
        """Test automatic addition of .gma.json extension."""
        # TDD Cycle 5 - Test: Auto extension addition
        dialog = SaveDialog(tk_root, sample_macro_recording, mock_callback)

        # Set up test input without extension
        dialog.filename_entry.insert(0, 'test-macro')
        dialog.password_entry.insert(0, 'password123')
        dialog.confirm_password_entry.insert(0, 'password123')

        # Mock successful callback
        mock_callback.return_value = True

        # Trigger save operation
        dialog._perform_save()

        # Verify callback was called with .gma.json extension added
        mock_callback.assert_called_once_with(
            filename='test-macro.gma.json',
            password='password123',
            macro_data=sample_macro_recording.to_dict(),
        )

    def test_callback_error_handling(
        self, tk_root, sample_macro_recording, mock_callback
    ):
        """Test error handling when callback fails."""
        # TDD Cycle 7 - Test: Mock-based error handling
        dialog = SaveDialog(tk_root, sample_macro_recording, mock_callback)

        # Set up valid test input
        dialog.filename_entry.insert(0, 'test-macro')
        dialog.password_entry.insert(0, 'password123')
        dialog.confirm_password_entry.insert(0, 'password123')

        # Mock callback failure
        mock_callback.side_effect = Exception('File system error')

        # Trigger save operation
        dialog._perform_save()

        # Verify error message is displayed
        assert '保存に失敗しました' in dialog.message_label.cget('text')

        # Dialog should remain open (not destroyed)
        assert dialog.dialog.winfo_exists()

    def test_modal_dialog_behavior(
        self, tk_root, sample_macro_recording, mock_callback
    ):
        """Test that dialog behaves as modal."""
        # TDD Cycle 2 - Test: Modal behavior
        dialog = SaveDialog(tk_root, sample_macro_recording, mock_callback)

        # Check that dialog is configured as modal
        assert dialog.dialog.grab_current() is not None
