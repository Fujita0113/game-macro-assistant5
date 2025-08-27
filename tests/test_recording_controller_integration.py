"""
Unit tests for recording controller integration with visual editor.
"""

import os
import sys
import time
from unittest.mock import Mock, patch

# Add project root and src to path for imports
project_root = os.path.join(os.path.dirname(__file__), '..')
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from ui.recording_controller import RecordingController
from core.macro_data import (
    MacroRecording,
    create_mouse_click_operation,
    create_key_operation,
    MouseButton,
    Position,
)


class TestRecordingControllerVisualEditorIntegration:
    """Test integration between recording controller and visual editor."""

    def setup_method(self):
        """Set up test fixtures."""
        # Try headless display setup first for better CI/CD compatibility
        from tests.utils.display_setup import setup_headless_display

        setup_headless_display()

        # Create test macro
        self.test_macro = MacroRecording(
            name='Test Recording',
            created_at=time.time(),
            operations=[
                create_mouse_click_operation(MouseButton.LEFT, Position(10, 20)),
                create_key_operation('space', 'press'),
                create_mouse_click_operation(MouseButton.RIGHT, Position(30, 40)),
            ],
            metadata={'created_by': 'Test'},
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        # Force cleanup and small delay to prevent resource conflicts
        import gc

        gc.collect()
        time.sleep(0.01)

    @patch('ui.recording_controller.VisualEditor')
    def test_open_visual_editor(self, mock_visual_editor_class):
        """Test opening visual editor with macro recording."""
        # Setup mocks
        mock_editor = Mock()
        mock_visual_editor_class.return_value = mock_editor

        # Create controller
        controller = RecordingController()

        # Open visual editor
        controller.open_visual_editor(self.test_macro)

        # Verify visual editor was created and configured
        mock_visual_editor_class.assert_called_once()
        mock_editor.load_macro.assert_called_once_with(self.test_macro)
        mock_editor.show.assert_called_once()

        # Verify controller stores the editor
        assert controller.visual_editor == mock_editor

    @patch('ui.recording_controller.VisualEditor')
    def test_reuse_existing_visual_editor(self, mock_visual_editor_class):
        """Test reusing existing visual editor instance."""
        # Setup mocks
        mock_editor = Mock()
        mock_visual_editor_class.return_value = mock_editor

        # Create controller and open editor twice
        controller = RecordingController()
        controller.open_visual_editor(self.test_macro)
        controller.open_visual_editor(self.test_macro)

        # Verify visual editor was created only once
        mock_visual_editor_class.assert_called_once()
        # But load_macro and show should be called twice
        assert mock_editor.load_macro.call_count == 2
        assert mock_editor.show.call_count == 2

    @patch('ui.recording_controller.VisualEditor')
    def test_close_visual_editor(self, mock_visual_editor_class):
        """Test closing visual editor."""
        # Setup mocks
        mock_editor = Mock()
        mock_visual_editor_class.return_value = mock_editor

        # Create controller and open editor
        controller = RecordingController()
        controller.open_visual_editor(self.test_macro)

        # Close editor
        controller.close_visual_editor()

        # Verify hide was called
        mock_editor.hide.assert_called_once()

    def test_close_visual_editor_when_none(self):
        """Test closing visual editor when none exists."""
        controller = RecordingController()

        # Should not raise error
        controller.close_visual_editor()

        # Should still be None
        assert controller.visual_editor is None

    @patch('ui.recording_controller.VisualEditor')
    def test_handle_visual_editor_error(self, mock_visual_editor_class):
        """Test handling errors when opening visual editor."""
        # Setup mock to raise exception
        mock_visual_editor_class.side_effect = Exception('Test error')

        # Create controller
        controller = RecordingController()

        # Should not raise exception
        controller.open_visual_editor(self.test_macro)

        # Visual editor should remain None
        assert controller.visual_editor is None

    @patch('ui.recording_controller.VisualEditor')
    @patch.object(RecordingController, 'open_visual_editor')
    def test_auto_open_after_recording_completion(
        self, mock_open_editor, mock_visual_editor_class
    ):
        """Test automatic opening of visual editor after recording completion."""
        # Create controller with mocked dependencies
        with (
            patch('ui.recording_controller.InputCaptureManager'),
            patch('ui.recording_controller.ScreenCaptureManager'),
        ):
            controller = RecordingController()

            # Simulate completing a recording with operations
            controller.current_recording = self.test_macro
            controller.is_recording = True

            # Mock the input capture to return that recording is stopped
            controller.input_capture.stop_recording = Mock()

            # Call stop_recording
            result = controller.stop_recording()

            # Verify visual editor was opened
            mock_open_editor.assert_called_once_with(self.test_macro)
            assert result == self.test_macro

    @patch('ui.recording_controller.VisualEditor')
    @patch.object(RecordingController, 'open_visual_editor')
    def test_no_auto_open_for_empty_recording(
        self, mock_open_editor, mock_visual_editor_class
    ):
        """Test that visual editor doesn't auto-open for empty recordings."""
        # Create empty macro
        empty_macro = MacroRecording(
            name='Empty Recording',
            created_at=time.time(),
            operations=[],  # No operations
            metadata={},
        )

        # Create controller with mocked dependencies
        with (
            patch('ui.recording_controller.InputCaptureManager'),
            patch('ui.recording_controller.ScreenCaptureManager'),
        ):
            controller = RecordingController()
            controller.current_recording = empty_macro
            controller.is_recording = True

            # Mock the input capture
            controller.input_capture.stop_recording = Mock()

            # Call stop_recording
            result = controller.stop_recording()

            # Verify visual editor was NOT opened
            mock_open_editor.assert_not_called()
            assert result == empty_macro


def run_tests():
    """Run all tests manually without pytest runner."""
    print('Running Recording Controller Integration Tests...')

    test_class = TestRecordingControllerVisualEditorIntegration()

    tests = [
        'test_open_visual_editor',
        'test_reuse_existing_visual_editor',
        'test_close_visual_editor',
        'test_close_visual_editor_when_none',
        'test_handle_visual_editor_error',
        'test_auto_open_after_recording_completion',
        'test_no_auto_open_for_empty_recording',
    ]

    passed = 0
    failed = 0

    for test_name in tests:
        try:
            print(f'\n• Testing {test_name}...')
            test_class.setup_method()
            test_method = getattr(test_class, test_name)
            test_method()
            test_class.teardown_method()
            print(f'  ✓ {test_name} passed')
            passed += 1
        except Exception as e:
            print(f'  ✗ {test_name} failed: {e}')
            failed += 1

    print(f'\nTest Results: {passed} passed, {failed} failed')
    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
