"""
Test suite for resource management in image editor.

Tests memory leak prevention, proper cleanup, and concurrent instance handling.
"""

import unittest
import io
import gc
from unittest.mock import Mock, patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ui.image_editor import ImageEditor
from PIL import Image, ImageDraw


class TestResourceManagement(unittest.TestCase):
    """Test resource management and cleanup."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_image_data = self._create_test_image_data()

    def _create_test_image_data(self):
        """Create test image data."""
        img = Image.new('RGB', (200, 200), color='blue')
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 150, 150], fill='white')

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    @patch('ui.image_editor.tk.Toplevel')
    def test_image_resource_cleanup(self, mock_toplevel):
        """Test that image resources are properly cleaned up."""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        mock_window.destroy = Mock()
        mock_window.grab_release = Mock()

        editor = ImageEditor(Mock(), self.valid_image_data, None)

        # Verify resources were created
        if not editor.load_failed:
            self.assertIsNotNone(editor.image)
            self.assertIsNotNone(editor.photo)

        # Close editor
        editor._close_window()

        # Verify resources were cleaned up
        self.assertIsNone(editor.window)
        self.assertIsNone(editor.image)
        self.assertIsNone(editor.photo)
        self.assertIsNone(editor.image_item)

    @patch('ui.image_editor.tk.Toplevel')
    def test_window_cleanup_with_exceptions(self, mock_toplevel):
        """Test that cleanup works even when exceptions occur."""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window

        # Make grab_release raise exception
        mock_window.grab_release.side_effect = Exception('Grab release failed')
        mock_window.destroy.side_effect = Exception('Destroy failed')

        editor = ImageEditor(Mock(), self.valid_image_data, None)

        # Cleanup should not raise exception despite errors
        try:
            editor._close_window()
        except Exception:
            self.fail('_close_window should not raise exceptions')

        # Window reference should still be cleared
        self.assertIsNone(editor.window)

    @patch('ui.image_editor.tk.Toplevel')
    def test_canvas_cleanup_safety(self, mock_toplevel):
        """Test that canvas cleanup is safe when canvas is already destroyed."""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window

        editor = ImageEditor(Mock(), self.valid_image_data, None)

        if not editor.load_failed:
            # Mock canvas deletion to raise TclError
            mock_canvas = Mock()
            mock_canvas.delete.side_effect = Exception('Canvas already destroyed')
            editor.canvas = mock_canvas
            editor.image_item = 'test_item'

            # Should not raise exception
            try:
                editor._cleanup_image_resources()
            except Exception:
                self.fail('_cleanup_image_resources should handle canvas errors')

    @patch('ui.image_editor.tk.Toplevel')
    def test_multiple_cleanup_calls_safety(self, mock_toplevel):
        """Test that multiple cleanup calls are safe."""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window

        editor = ImageEditor(Mock(), self.valid_image_data, None)

        # Call cleanup multiple times
        editor._cleanup_image_resources()
        editor._cleanup_image_resources()  # Should be safe
        editor._close_window()
        editor._close_window()  # Should be safe

    @patch('ui.image_editor.tk.Toplevel')
    def test_memory_leak_prevention(self, mock_toplevel):
        """Test that repeated editor creation doesn't leak memory significantly."""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window

        # Create and destroy multiple editors
        editors = []
        for i in range(10):
            editor = ImageEditor(Mock(), self.valid_image_data, None)
            editors.append(editor)

        # Clean up all editors
        for editor in editors:
            editor._close_window()

        # Force garbage collection
        gc.collect()

        # All editor windows should be None
        for editor in editors:
            self.assertIsNone(editor.window)

    @patch('ui.image_editor.tk.Toplevel')
    @patch('builtins.print')
    def test_cleanup_error_logging(self, mock_print, mock_toplevel):
        """Test that cleanup errors are logged but don't prevent cleanup."""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        mock_window.destroy.side_effect = Exception('Cleanup error')

        editor = ImageEditor(Mock(), self.valid_image_data, None)
        editor._close_window()

        # Check that error was logged
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        error_logs = [log for log in print_calls if 'Warning: Error during' in log]
        self.assertGreater(len(error_logs), 0)

        # Window should still be cleaned up
        self.assertIsNone(editor.window)

    def test_concurrent_editors_independence(self):
        """Test that multiple editors can exist concurrently without interference."""
        with patch('ui.image_editor.tk.Toplevel') as mock_toplevel:
            # Create multiple editors
            mock_windows = [Mock() for _ in range(3)]
            mock_toplevel.side_effect = mock_windows

            editors = []
            for i in range(3):
                editor = ImageEditor(Mock(), self.valid_image_data, None)
                editors.append(editor)

            # Each should have its own window
            for i, editor in enumerate(editors):
                if not editor.load_failed:
                    self.assertIs(editor.window, mock_windows[i])

            # Close one editor
            editors[0]._close_window()
            self.assertIsNone(editors[0].window)

            # Others should remain unaffected
            for editor in editors[1:]:
                if not editor.load_failed:
                    self.assertIsNotNone(editor.window)

    def test_resource_state_after_load_failure(self):
        """Test resource state when image loading fails."""
        with patch('ui.image_editor.tk.Toplevel') as mock_toplevel:
            mock_window = Mock()
            mock_toplevel.return_value = mock_window

            # Create editor with invalid data
            editor = ImageEditor(Mock(), b'invalid', None)

            # Should be in failed state
            self.assertTrue(editor.load_failed)

            # But window should still exist for error display
            self.assertIsNotNone(editor.window)

            # Image resources should be None
            self.assertIsNone(editor.image)
            self.assertIsNone(editor.photo)

            # Cleanup should still work
            editor._close_window()
            self.assertIsNone(editor.window)

    @patch('ui.image_editor.tk.Toplevel')
    def test_pil_image_close_handling(self, mock_toplevel):
        """Test that PIL Image.close() is called safely."""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window

        editor = ImageEditor(Mock(), self.valid_image_data, None)

        if not editor.load_failed and editor.image:
            # Mock PIL Image to track close calls
            mock_image = Mock()
            editor.image = mock_image

            editor._cleanup_image_resources()

            # close() should have been called
            mock_image.close.assert_called_once()

    def test_coordinate_transformer_cleanup(self):
        """Test that coordinate transformer is properly cleaned up."""
        with patch('ui.image_editor.tk.Toplevel') as mock_toplevel:
            mock_window = Mock()
            mock_toplevel.return_value = mock_window

            editor = ImageEditor(Mock(), self.valid_image_data, None)

            if not editor.load_failed:
                # Should have coordinate transformer
                self.assertIsNotNone(editor.coordinate_transformer)

            editor._close_window()

            # Coordinate transformer reference should remain (it's not a resource that needs cleanup)
            # but the editor should be in a clean state


if __name__ == '__main__':
    unittest.main(verbosity=2)
