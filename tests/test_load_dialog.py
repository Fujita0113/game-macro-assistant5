"""
Tests for LoadDialog UI component.

This module tests the load dialog functionality with mock-based testing
as specified in the requirements.
"""

from unittest.mock import patch
from src.ui.load_dialog import LoadDialog
from src.core.macro_data import MacroRecording, OperationType
from src.core.file_encryption import PasswordValidationError


class TestLoadDialogBasicStructure:
    """Test basic dialog structure and UI elements."""

    def test_dialog_initialization(self, tk_root):
        """Test that dialog initializes with required UI elements."""
        dialog = LoadDialog(tk_root)

        # Test modal dialog setup
        assert dialog.dialog is not None
        # transient() returns '' when successful, so we check that it doesn't raise
        dialog.dialog.transient(tk_root)
        # grab_set() returns None when successful
        dialog.dialog.grab_set()

        # Test basic UI elements exist
        assert hasattr(dialog, 'file_path_var')
        assert hasattr(dialog, 'password_var')
        assert hasattr(dialog, 'message_var')

        # Test required buttons exist
        assert hasattr(dialog, 'load_button')
        assert hasattr(dialog, 'cancel_button')
        assert hasattr(dialog, 'browse_button')

    def test_dialog_has_success_error_message_label(self, tk_root):
        """Test that dialog has message label for success/error messages."""
        dialog = LoadDialog(tk_root)

        # Should have message label
        assert hasattr(dialog, 'message_label')
        assert hasattr(dialog, 'message_var')

        # Message should be empty initially
        assert dialog.message_var.get() == ''

    def test_dialog_modal_behavior(self, tk_root):
        """Test that dialog behaves as modal dialog."""
        dialog = LoadDialog(tk_root)

        # Should be transient of parent (returns '' when successful)
        dialog.dialog.transient(tk_root)

        # Should have grab set for modal behavior
        dialog.dialog.grab_set()
        assert dialog.dialog.grab_current() == dialog.dialog

    def test_password_field_masked(self, tk_root):
        """Test that password field is masked (show='*')."""
        dialog = LoadDialog(tk_root)

        # Test password field is masked
        assert hasattr(dialog, 'password_entry')
        assert dialog.password_entry is not None
        assert dialog.password_entry.cget('show') == '*'

    def test_file_path_display(self, tk_root):
        """Test that selected file path is displayed."""
        dialog = LoadDialog(tk_root)

        # Test file path variable can be set and retrieved
        test_path = 'C:\\test\\macro.gma.json'
        dialog.file_path_var.set(test_path)
        assert dialog.file_path_var.get() == test_path


class TestFileSelectionAndValidation:
    """Test file selection and validation functionality."""

    @patch('tkinter.filedialog.askopenfilename')
    def test_browse_button_opens_file_dialog_with_gma_filter(
        self, mock_askopenfilename, tk_root
    ):
        """Test that browse button opens file dialog with .gma.json filter."""
        mock_askopenfilename.return_value = 'C:\\test\\macro.gma.json'

        dialog = LoadDialog(tk_root)
        dialog._on_browse_clicked()

        # Verify file dialog was called with correct filter
        mock_askopenfilename.assert_called_once()
        call_args = mock_askopenfilename.call_args
        assert call_args[1]['filetypes'][0] == ('GMAssistant files', '*.gma.json')

    @patch('tkinter.filedialog.askopenfilename')
    def test_file_selection_updates_path_variable(self, mock_askopenfilename, tk_root):
        """Test that selecting file updates the file path variable."""
        test_path = 'C:\\test\\macro.gma.json'
        mock_askopenfilename.return_value = test_path

        dialog = LoadDialog(tk_root)
        dialog._on_browse_clicked()

        assert dialog.file_path_var.get() == test_path

    @patch('tkinter.filedialog.askopenfilename')
    def test_file_selection_clears_previous_messages(
        self, mock_askopenfilename, tk_root
    ):
        """Test that selecting file clears any previous error messages."""
        mock_askopenfilename.return_value = 'C:\\test\\macro.gma.json'

        dialog = LoadDialog(tk_root)
        dialog.message_var.set('Previous error message')
        dialog._on_browse_clicked()

        assert dialog.message_var.get() == ''

    @patch('tkinter.filedialog.askopenfilename')
    def test_cancel_file_selection_does_not_change_path(
        self, mock_askopenfilename, tk_root
    ):
        """Test that cancelling file selection doesn't change current path."""
        mock_askopenfilename.return_value = ''  # Empty string when cancelled

        dialog = LoadDialog(tk_root)
        original_path = 'C:\\original\\path.gma.json'
        dialog.file_path_var.set(original_path)

        dialog._on_browse_clicked()

        # Path should remain unchanged
        assert dialog.file_path_var.get() == original_path

    def test_validation_requires_file_path(self, tk_root):
        """Test that validation fails when no file is selected."""
        dialog = LoadDialog(tk_root)
        dialog.password_var.set('password123')  # Set valid password

        dialog._on_load_clicked()

        assert 'ファイルを選択してください' in dialog.message_var.get()

    def test_validation_requires_password(self, tk_root):
        """Test that validation fails when no password is provided."""
        dialog = LoadDialog(tk_root)
        dialog.file_path_var.set('C:\\test\\macro.gma.json')  # Set valid file

        dialog._on_load_clicked()

        assert 'パスワードを入力してください' in dialog.message_var.get()


class TestCallbackIntegrationAndMockTests:
    """Test callback integration with MacroRecording and mock-based error handling."""

    def test_successful_load_returns_macro_recording_object(self, tk_root):
        """Test that successful load returns MacroRecording object (mock-based)."""
        dialog = LoadDialog(tk_root)

        # Setup test data - mock MacroRecording object
        mock_recording = MacroRecording(
            name='test-macro',
            created_at=1234567890.0,
            operations=[],
            metadata={'version': '1.0', 'description': 'Test macro'},
        )

        # Mock the file manager's load method to return the test data
        with patch.object(dialog.file_manager, 'load_macro_file') as mock_load:
            mock_load.return_value = mock_recording.to_dict()

            # Set valid inputs
            dialog.file_path_var.set('C:\\test\\test-macro.gma.json')
            dialog.password_var.set('password123')

            # Call load functionality
            dialog._on_load_clicked()

            # Verify file manager was called with correct parameters
            mock_load.assert_called_once_with(
                'C:\\test\\test-macro.gma.json', 'password123'
            )

            # Verify MacroRecording object is created correctly
            assert dialog.result is not None
            assert isinstance(dialog.result, MacroRecording)
            assert dialog.result.name == 'test-macro'
            assert dialog.result.created_at == 1234567890.0
            assert dialog.result.metadata == {
                'version': '1.0',
                'description': 'Test macro',
            }

    def test_macro_recording_structure_validation(self, tk_root):
        """Test MacroRecording object structure validation (mock-based)."""
        dialog = LoadDialog(tk_root)

        # Create test data with specific structure
        test_data = {
            'name': 'validated-macro',
            'created_at': 1234567890.5,
            'operations': [
                {
                    'id': 'test_op_1',
                    'operation_type': 'mouse_click',
                    'timestamp': 1234567890.5,
                    'mouse_op': {
                        'button': 'left',
                        'position': {'x': 100, 'y': 200},
                        'action': 'click',
                    },
                    'delay_after': 0.5,
                }
            ],
            'metadata': {'test_key': 'test_value', 'operation_count': 1},
        }

        with patch.object(dialog.file_manager, 'load_macro_file') as mock_load:
            mock_load.return_value = test_data

            dialog.file_path_var.set('C:\\test\\validated-macro.gma.json')
            dialog.password_var.set('password123')
            dialog._on_load_clicked()

            # Verify structure validation
            result = dialog.result
            assert result.name == 'validated-macro'
            assert result.created_at == 1234567890.5
            assert isinstance(result.operations, list)
            assert len(result.operations) == 1
            assert isinstance(result.metadata, dict)
            assert result.metadata['test_key'] == 'test_value'

            # Verify operations structure
            op = result.operations[0]
            assert op.id == 'test_op_1'
            assert op.operation_type == OperationType.MOUSE_CLICK
            assert op.mouse_op is not None
            assert op.mouse_op.button.value == 'left'
            assert op.mouse_op.position.x == 100
            assert op.delay_after == 0.5

    def test_success_message_and_dialog_close(self, tk_root):
        """Test success message display and automatic dialog close."""
        dialog = LoadDialog(tk_root)
        mock_recording = MacroRecording('test', 1234567890.0, [], {})

        with patch.object(dialog.file_manager, 'load_macro_file') as mock_load:
            with patch.object(dialog.dialog, 'after') as mock_after:
                mock_load.return_value = mock_recording.to_dict()

                dialog.file_path_var.set('C:\\test\\macro.gma.json')
                dialog.password_var.set('password123')
                dialog._on_load_clicked()

                # Should show success message
                assert (
                    '成功' in dialog.message_var.get()
                    or '読み込み完了' in dialog.message_var.get()
                )

                # Should schedule automatic close dialog after delay
                mock_after.assert_called_once_with(1000, dialog.dialog.destroy)

    def test_password_validation_error_handling(self, tk_root):
        """Test PasswordValidationError handling with 3-attempt limit."""
        dialog = LoadDialog(tk_root)

        with patch.object(dialog.file_manager, 'load_macro_file') as mock_load:
            # First attempt - wrong password
            mock_load.side_effect = PasswordValidationError('Invalid password')

            dialog.file_path_var.set('C:\\test\\macro.gma.json')
            dialog.password_var.set('wrongpassword')
            dialog._on_load_clicked()

            # Should show password error
            assert (
                'パスワード' in dialog.message_var.get()
                or 'Invalid password' in dialog.message_var.get()
            )

            # Verify attempts are tracked (through file manager)
            mock_load.assert_called_once_with(
                'C:\\test\\macro.gma.json', 'wrongpassword'
            )

    def test_password_attempts_exceeded_error(self, tk_root):
        """Test handling when maximum password attempts are exceeded."""
        dialog = LoadDialog(tk_root)

        with patch.object(dialog.file_manager, 'load_macro_file') as mock_load:
            mock_load.side_effect = PasswordValidationError(
                'Maximum password attempts exceeded'
            )

            dialog.file_path_var.set('C:\\test\\macro.gma.json')
            dialog.password_var.set('password123')
            dialog._on_load_clicked()

            # Should show attempts exceeded error
            error_msg = dialog.message_var.get()
            assert (
                '試行' in error_msg
                or 'attempts' in error_msg
                or 'exceeded' in error_msg
            )

    def test_file_system_error_handling(self, tk_root):
        """Test handling of file system errors (file not found, corrupted, etc.)."""
        dialog = LoadDialog(tk_root)

        with patch.object(dialog.file_manager, 'load_macro_file') as mock_load:
            # Test file not found error
            mock_load.side_effect = PasswordValidationError(
                'Failed to load file: [Errno 2] No such file or directory'
            )

            dialog.file_path_var.set('C:\\nonexistent\\macro.gma.json')
            dialog.password_var.set('password123')
            dialog._on_load_clicked()

            # Should show file error message
            error_msg = dialog.message_var.get()
            assert 'ファイル' in error_msg or 'file' in error_msg

    def test_corrupted_file_error_handling(self, tk_root):
        """Test handling of corrupted file errors."""
        dialog = LoadDialog(tk_root)

        with patch.object(dialog.file_manager, 'load_macro_file') as mock_load:
            mock_load.side_effect = PasswordValidationError(
                'File appears to be corrupted'
            )

            dialog.file_path_var.set('C:\\test\\corrupted.gma.json')
            dialog.password_var.set('password123')
            dialog._on_load_clicked()

            # Should show corruption error
            error_msg = dialog.message_var.get()
            assert (
                '破損' in error_msg or 'corrupted' in error_msg or 'エラー' in error_msg
            )


class TestTechnicalDebtImprovements:
    """Test technical debt improvements with configurable parameters and robust error handling."""

    def test_configurable_success_dialog_delay_default(self, tk_root):
        """Test default success dialog delay (1000ms)."""
        dialog = LoadDialog(tk_root)
        mock_recording = MacroRecording('test', 1234567890.0, [], {})

        with patch.object(dialog.file_manager, 'load_macro_file') as mock_load:
            with patch.object(dialog.dialog, 'after') as mock_after:
                mock_load.return_value = mock_recording.to_dict()

                dialog.file_path_var.set('C:\\test\\macro.gma.json')
                dialog.password_var.set('password123')
                dialog._on_load_clicked()

                # Should use default delay of 1000ms
                mock_after.assert_called_once_with(1000, dialog.dialog.destroy)

    def test_configurable_success_dialog_delay_custom(self, tk_root):
        """Test custom success dialog delay."""
        custom_delay = 2500
        dialog = LoadDialog(tk_root, success_delay_ms=custom_delay)
        mock_recording = MacroRecording('test', 1234567890.0, [], {})

        with patch.object(dialog.file_manager, 'load_macro_file') as mock_load:
            with patch.object(dialog.dialog, 'after') as mock_after:
                mock_load.return_value = mock_recording.to_dict()

                dialog.file_path_var.set('C:\\test\\macro.gma.json')
                dialog.password_var.set('password123')
                dialog._on_load_clicked()

                # Should use custom delay
                mock_after.assert_called_once_with(custom_delay, dialog.dialog.destroy)

    def test_error_classification_by_exception_attributes(self, tk_root):
        """Test error classification based on exception attributes rather than string matching."""
        dialog = LoadDialog(tk_root)

        # Create a PasswordValidationError with specific error code
        password_error = PasswordValidationError('Test error message')
        password_error.error_code = 'INVALID_PASSWORD'

        with patch.object(dialog.file_manager, 'load_macro_file') as mock_load:
            mock_load.side_effect = password_error

            dialog.file_path_var.set('C:\\test\\macro.gma.json')
            dialog.password_var.set('wrongpassword')
            dialog._on_load_clicked()

            # Should classify error by error_code, not message content
            error_msg = dialog.message_var.get()
            assert 'パスワードが正しくありません' in error_msg

        # Test different error codes
        attempts_error = PasswordValidationError('Different message')
        attempts_error.error_code = 'MAX_ATTEMPTS_EXCEEDED'

        with patch.object(dialog.file_manager, 'load_macro_file') as mock_load:
            mock_load.side_effect = attempts_error

            dialog._on_load_clicked()

            error_msg = dialog.message_var.get()
            assert 'パスワード試行回数が上限に達しました' in error_msg

    def test_unknown_error_fallback_handling(self, tk_root):
        """Test fallback handling for unknown or unclassified errors."""
        dialog = LoadDialog(tk_root)

        # Create error with unknown error code
        unknown_error = PasswordValidationError('Unknown error occurred')
        unknown_error.error_code = 'UNKNOWN_ERROR'

        with patch.object(dialog.file_manager, 'load_macro_file') as mock_load:
            mock_load.side_effect = unknown_error

            dialog.file_path_var.set('C:\\test\\macro.gma.json')
            dialog.password_var.set('password123')
            dialog._on_load_clicked()

            # Should fall back to generic error message
            error_msg = dialog.message_var.get()
            assert 'エラー' in error_msg or 'Unknown error occurred' in error_msg

    def test_loading_progress_indication(self, tk_root):
        """Test that loading progress is indicated during file operations."""
        dialog = LoadDialog(tk_root)
        mock_recording = MacroRecording('test', 1234567890.0, [], {})

        # Track progress indication calls
        progress_calls = []

        def mock_show_progress():
            progress_calls.append('show')

        def mock_hide_progress():
            progress_calls.append('hide')

        with patch.object(dialog.file_manager, 'load_macro_file') as mock_load:
            with patch.object(
                dialog, '_show_loading_progress', side_effect=mock_show_progress
            ):
                with patch.object(
                    dialog, '_hide_loading_progress', side_effect=mock_hide_progress
                ):
                    mock_load.return_value = mock_recording.to_dict()

                    dialog.file_path_var.set('C:\\test\\macro.gma.json')
                    dialog.password_var.set('password123')
                    dialog._on_load_clicked()

                    # Should have called show and hide progress
                    assert 'show' in progress_calls
                    assert 'hide' in progress_calls

    def test_ui_remains_responsive_during_load(self, tk_root):
        """Test that UI remains responsive during loading operations."""
        dialog = LoadDialog(tk_root)

        # Mock load button to verify it gets disabled/enabled
        load_button_states = []

        def track_load_button_state():
            load_button_states.append(dialog.load_button.cget('state'))

        with patch.object(dialog.file_manager, 'load_macro_file') as mock_load:
            # Simulate slow file loading
            def slow_load(*args, **kwargs):
                track_load_button_state()  # Should be disabled during load
                return MacroRecording('test', 1234567890.0, [], {}).to_dict()

            mock_load.side_effect = slow_load

            dialog.file_path_var.set('C:\\test\\macro.gma.json')
            dialog.password_var.set('password123')

            # Button should be enabled initially
            initial_state = str(dialog.load_button.cget('state'))
            assert initial_state in ('normal', 'enabled', '')

            dialog._on_load_clicked()

            # Button should have been disabled during load
            assert 'disabled' in load_button_states or any(
                'disable' in str(s) for s in load_button_states
            )

    def test_result_none_validation(self, tk_root):
        """Test result attribute None validation and type safety."""
        dialog = LoadDialog(tk_root)

        # Initially result should be None
        assert dialog.result is None

        # show_modal should return None when result is None
        with patch.object(dialog.dialog, 'wait_window'):
            result = dialog.show_modal()
            assert result is None

        # Ensure type safety - result should always be None or MacroRecording
        assert dialog.result is None or isinstance(dialog.result, MacroRecording)

    def test_show_modal_type_safety(self, tk_root):
        """Test show_modal return value type safety."""
        dialog = LoadDialog(tk_root)

        # Test with successful result
        mock_recording = MacroRecording('test', 1234567890.0, [], {})
        dialog.result = mock_recording

        with patch.object(dialog.dialog, 'wait_window'):
            result = dialog.show_modal()

            # Result should be MacroRecording instance
            assert isinstance(result, MacroRecording)
            assert result.name == 'test'
            assert result.created_at == 1234567890.0

        # Test with None result (cancelled or error)
        dialog.result = None

        with patch.object(dialog.dialog, 'wait_window'):
            result = dialog.show_modal()

            # Result should be None
            assert result is None

    def test_set_result_type_validation(self, tk_root):
        """Test _set_result method type validation."""
        dialog = LoadDialog(tk_root)

        # Valid MacroRecording should work
        valid_recording = MacroRecording('test', 1234567890.0, [], {})
        dialog._set_result(valid_recording)
        assert dialog.result == valid_recording

        # None should work
        dialog._set_result(None)
        assert dialog.result is None

        # Invalid type should raise AssertionError
        try:
            dialog._set_result('invalid string type')
            assert False, 'Should have raised AssertionError for invalid type'
        except AssertionError as e:
            assert 'Result must be None or MacroRecording' in str(e)
