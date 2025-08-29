"""
Tests for the save dialog UI functionality.

Test cases cover:
1. Normal save operation
2. Password validation (minimum length)
3. Password confirmation validation
4. File name validation
"""

import unittest
from unittest.mock import Mock
import tkinter as tk
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ui.save_dialog import SaveDialog
from core.macro_data import MacroRecording, OperationBlock


class TestSaveDialog(unittest.TestCase):
    """Test cases for SaveDialog functionality."""

    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests

        # Create sample macro recording
        self.macro_recording = Mock(spec=MacroRecording)
        self.macro_recording.name = 'test-macro'
        self.macro_recording.operations = [Mock(spec=OperationBlock)]

    def tearDown(self):
        """Clean up after tests."""
        if self.root:
            self.root.destroy()

    def test_normal_save_operation_success(self):
        """Test: ユーザーが新しいマクロを正常に保存する"""
        # Create dialog
        dialog = SaveDialog(self.root, self.macro_recording)

        # Set valid input values
        dialog.filename_entry.insert(0, 'test-macro')
        dialog.password_entry.insert(0, 'password123')
        dialog.password_confirm_entry.insert(0, 'password123')

        # Simulate save button click
        dialog._on_save()

        # Verify the dialog indicates successful save
        self.assertEqual(dialog.result, 'saved')

    def test_password_validation_minimum_length(self):
        """Test: パスワードバリデーションが正しく動作する - 8文字未満でエラー"""
        # Create dialog
        dialog = SaveDialog(self.root, self.macro_recording)

        # Set invalid password (less than 8 characters)
        dialog.filename_entry.insert(0, 'test-macro')
        dialog.password_entry.insert(0, '123')  # Only 3 characters
        dialog.password_confirm_entry.insert(0, '123')

        # Simulate save button click
        dialog._on_save()

        # Should show error message and not close dialog
        self.assertEqual(
            dialog.error_label.cget('text'), 'パスワードは8文字以上で入力してください'
        )
        self.assertIsNone(dialog.result)  # Dialog should still be open

    def test_password_confirmation_validation(self):
        """Test: パスワード確認が正しく動作する - 不一致でエラー"""
        # Create dialog
        dialog = SaveDialog(self.root, self.macro_recording)

        # Set mismatched passwords
        dialog.filename_entry.insert(0, 'test-macro')
        dialog.password_entry.insert(0, 'password123')
        dialog.password_confirm_entry.insert(0, 'different123')

        # Simulate save button click
        dialog._on_save()

        # Should show error message and not close dialog
        self.assertEqual(dialog.error_label.cget('text'), 'パスワードが一致しません')
        self.assertIsNone(dialog.result)  # Dialog should still be open

    def test_filename_validation(self):
        """Test: ファイル名バリデーション - 空のファイル名でエラー"""
        # Create dialog
        dialog = SaveDialog(self.root, self.macro_recording)

        # Set empty filename
        dialog.filename_entry.insert(0, '')  # Empty filename
        dialog.password_entry.insert(0, 'password123')
        dialog.password_confirm_entry.insert(0, 'password123')

        # Simulate save button click
        dialog._on_save()

        # Should show error message and not close dialog
        self.assertEqual(
            dialog.error_label.cget('text'), 'ファイル名を入力してください'
        )
        self.assertIsNone(dialog.result)  # Dialog should still be open


if __name__ == '__main__':
    unittest.main()
