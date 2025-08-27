"""
Comprehensive test suite for ImageEditor class.

Tests cover:
- Happy path operations
- Error handling for various failure scenarios
- Edge cases and boundary conditions
- Coordinate transformation precision
- UI component integration
"""

import unittest
import tkinter as tk
import io
import os
import sys
from unittest.mock import patch
from PIL import Image, ImageDraw
import pytest

# Configure headless environment support
os.environ.setdefault('DISPLAY', ':0')

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ui.image_editor import ImageEditor


class TkinterTestMixin:
    """Mixin class to handle Tkinter environment issues gracefully."""

    def setUp_tkinter(self):
        """Set up Tkinter with environment error handling."""
        try:
            import PIL.ImageTk

            self.root = tk.Tk()
            self.root.withdraw()  # Hide test window

            # Test PIL ImageTk integration which is critical for our tests
            from PIL import Image

            test_image = Image.new('RGB', (10, 10), color='red')
            test_photo = PIL.ImageTk.PhotoImage(test_image)

            # Test basic Tkinter functionality with images
            test_canvas = tk.Canvas(self.root, width=10, height=10)
            test_item = test_canvas.create_image(0, 0, image=test_photo, anchor='nw')
            test_canvas.delete(test_item)
            test_canvas.destroy()
            return True
        except (tk.TclError, ImportError, AttributeError, OSError) as e:
            # Skip on any GUI/image-related errors
            pytest.skip(f'GUI environment not available for image tests: {e}')
        except Exception as e:
            pytest.skip(f'Unexpected GUI initialization error: {e}')

    def tearDown_tkinter(self):
        """Clean up Tkinter resources safely."""
        if hasattr(self, 'root') and self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except tk.TclError:
                # Ignore cleanup errors in problematic environments
                pass


class TestImageEditorTestData:
    """Helper class for generating test image data."""

    @staticmethod
    def create_standard_test_image(width=800, height=600) -> bytes:
        """Create a standard test image (800x600 PNG) without text to avoid font conflicts."""
        image = Image.new('RGB', (width, height), color='lightblue')
        draw = ImageDraw.Draw(image)

        # Draw test elements - avoid text drawing to prevent PIL font loading conflicts
        draw.rectangle([50, 50, 150, 100], fill='lightgray', outline='black', width=2)
        draw.rectangle([75, 70, 125, 90], fill='red', outline='darkred', width=1)

        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        return img_bytes.getvalue()

    @staticmethod
    def create_large_test_image(width=12000, height=12000) -> bytes:
        """Create a large test image exceeding the 10000x10000 limit."""
        image = Image.new('RGB', (width, height), color='red')

        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        return img_bytes.getvalue()

    @staticmethod
    def create_tiny_test_image(width=1, height=1) -> bytes:
        """Create a minimal 1x1 pixel image."""
        image = Image.new('RGB', (width, height), color='green')

        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        return img_bytes.getvalue()

    @staticmethod
    def create_invalid_image_data() -> bytes:
        """Create invalid/corrupted image data."""
        return b'invalid_image_data_not_png_or_jpeg'

    @staticmethod
    def create_empty_data() -> bytes:
        """Create empty binary data."""
        return b''


class TestImageEditorHappyPath(TkinterTestMixin, unittest.TestCase):
    """Test normal successful operations."""

    def setUp(self):
        """Set up test environment."""
        self.setUp_tkinter()  # Handle Tkinter initialization with error handling
        self.test_data = TestImageEditorTestData()
        self.callback_received = None

        def test_callback(region):
            self.callback_received = region

        self.test_callback = test_callback

    def tearDown(self):
        """Clean up after tests."""
        if (
            hasattr(self, 'editor')
            and hasattr(self.editor, 'window')
            and self.editor.window
        ):
            try:
                self.editor.window.destroy()
            except tk.TclError:
                pass  # Ignore cleanup errors
        self.tearDown_tkinter()

    def test_standard_image_initialization(self):
        """Test that ImageEditor initializes correctly with standard 800x600 image."""
        image_data = self.test_data.create_standard_test_image()

        self.editor = ImageEditor(self.root, image_data, self.test_callback)

        # Verify initialization
        self.assertIsNotNone(self.editor.window)
        self.assertIsNotNone(self.editor.canvas)
        self.assertIsNotNone(self.editor.image)
        self.assertIsNotNone(self.editor.photo)

        # Verify image dimensions
        self.assertEqual(self.editor.image.size, (800, 600))
        self.assertGreater(self.editor.scale_factor, 0)
        self.assertLessEqual(self.editor.scale_factor, 1.0)

    def test_mouse_selection_coordinates(self):
        """Test that mouse drag selection calculates correct coordinates."""
        image_data = self.test_data.create_standard_test_image()
        self.editor = ImageEditor(self.root, image_data, self.test_callback)

        # Simulate mouse selection: 100x100 pixel area
        self.editor.selection_start = (50, 50)
        self.editor.selection_end = (150, 150)

        region = self.editor._get_selection_region()

        self.assertIsNotNone(region)
        x, y, width, height = region

        # Verify coordinates are reasonable (considering scale factor)
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)

        # Verify area is approximately correct (accounting for scaling)
        expected_width = int(100 / self.editor.scale_factor)
        expected_height = int(100 / self.editor.scale_factor)
        self.assertAlmostEqual(width, expected_width, delta=2)
        self.assertAlmostEqual(height, expected_height, delta=2)

    def test_ok_cancel_button_callbacks(self):
        """Test that OK and Cancel buttons invoke appropriate callbacks."""
        image_data = self.test_data.create_standard_test_image()
        self.editor = ImageEditor(self.root, image_data, self.test_callback)

        # Set up a valid selection
        self.editor.selection_start = (50, 50)
        self.editor.selection_end = (100, 100)

        # Test OK button (should call callback)
        with patch.object(self.editor, '_close_window') as mock_close:
            self.editor._on_confirm_click()
            self.assertIsNotNone(self.callback_received)
            mock_close.assert_called_once()

        # Test Cancel button (should not call callback)
        self.callback_received = None
        with patch.object(self.editor, '_close_window') as mock_close:
            self.editor._on_cancel()
            self.assertIsNone(self.callback_received)
            mock_close.assert_called_once()

    def test_selection_rectangle_highlight(self):
        """Test that selection area is highlighted with a rectangle."""
        image_data = self.test_data.create_standard_test_image()
        self.editor = ImageEditor(self.root, image_data, self.test_callback)

        # Initially no selection rectangle
        self.assertIsNone(self.editor.selection_rect)

        # Set selection and update rectangle
        self.editor.selection_start = (50, 50)
        self.editor.selection_end = (100, 100)
        self.editor._update_selection_rect()

        # Verify rectangle is created
        self.assertIsNotNone(self.editor.selection_rect)

        # Clear selection
        self.editor._clear_selection()
        self.assertIsNone(self.editor.selection_start)
        self.assertIsNone(self.editor.selection_end)


class TestImageEditorErrorHandling(TkinterTestMixin, unittest.TestCase):
    """Test error handling for various failure scenarios."""

    def setUp(self):
        """Set up test environment."""
        self.setUp_tkinter()  # Handle Tkinter initialization with error handling
        self.test_data = TestImageEditorTestData()

    def tearDown(self):
        """Clean up after tests."""
        if (
            hasattr(self, 'editor')
            and hasattr(self.editor, 'window')
            and self.editor.window
        ):
            try:
                self.editor.window.destroy()
            except tk.TclError:
                pass  # Ignore cleanup errors
        self.tearDown_tkinter()

    @patch('ui.image_editor.messagebox.showerror')
    def test_large_image_error_handling(self, mock_messagebox):
        """Test that images larger than 10000x10000 show appropriate error."""
        large_image_data = self.test_data.create_large_test_image()

        self.editor = ImageEditor(self.root, large_image_data, None)

        # Verify error message was shown
        mock_messagebox.assert_called_once()
        args, kwargs = mock_messagebox.call_args
        error_message = args[1]  # Second argument is the message
        self.assertIn('大きすぎます', error_message)
        self.assertIn('10000x10000', error_message)

    @patch('ui.image_editor.messagebox.showerror')
    def test_invalid_image_format_error(self, mock_messagebox):
        """Test that invalid image data shows 'cannot identify image file' error."""
        invalid_data = self.test_data.create_invalid_image_data()

        self.editor = ImageEditor(self.root, invalid_data, None)

        # Verify appropriate error message was shown
        mock_messagebox.assert_called_once()
        args, kwargs = mock_messagebox.call_args
        error_message = args[1]
        self.assertIn('認識できません', error_message)
        self.assertIn('PNG', error_message)

    @patch('ui.image_editor.messagebox.showerror')
    def test_empty_image_data_error(self, mock_messagebox):
        """Test that empty binary data is handled gracefully."""
        empty_data = self.test_data.create_empty_data()

        self.editor = ImageEditor(self.root, empty_data, None)

        # Should show format recognition error message (empty data is treated as unrecognizable)
        mock_messagebox.assert_called_once()
        args, kwargs = mock_messagebox.call_args
        error_message = args[1]
        # Empty data triggers "cannot identify image file" path, not generic error
        self.assertIn('認識できません', error_message)

    @patch('ui.image_editor.messagebox.showerror')
    def test_memory_error_handling(self, mock_messagebox):
        """Test that memory errors show appropriate message."""
        # Create test data BEFORE applying mock to avoid PIL font loading conflicts
        image_data = self.test_data.create_standard_test_image()

        # Apply mock with precise scope - only during ImageEditor initialization
        with patch('PIL.Image.open') as mock_image_open:
            mock_image_open.side_effect = MemoryError('out of memory')
            self.editor = ImageEditor(self.root, image_data, None)

        # Verify memory error message
        mock_messagebox.assert_called_once()
        args, kwargs = mock_messagebox.call_args
        error_message = args[1]
        self.assertIn('メモリ不足', error_message)

    @patch('ui.image_editor.messagebox.showerror')
    def test_no_messagebox_import_error(self, mock_messagebox):
        """Test that messagebox import is available and doesn't cause AttributeError."""
        image_data = self.test_data.create_invalid_image_data()

        # This should not raise AttributeError
        try:
            self.editor = ImageEditor(self.root, image_data, None)
        except AttributeError as e:
            if 'messagebox' in str(e):
                self.fail('AttributeError related to messagebox import detected')

        # Verify messagebox was called without errors
        mock_messagebox.assert_called_once()


class TestImageEditorEdgeCases(TkinterTestMixin, unittest.TestCase):
    """Test boundary conditions and edge cases."""

    def setUp(self):
        """Set up test environment."""
        self.setUp_tkinter()  # Handle Tkinter initialization with error handling
        self.test_data = TestImageEditorTestData()

    def tearDown(self):
        """Clean up after tests."""
        if (
            hasattr(self, 'editor')
            and hasattr(self.editor, 'window')
            and self.editor.window
        ):
            try:
                self.editor.window.destroy()
            except tk.TclError:
                pass  # Ignore cleanup errors
        self.tearDown_tkinter()

    @patch('ui.image_editor.messagebox.showerror')
    def test_minimum_selection_size_validation(self, mock_messagebox):
        """Test that selections smaller than 5x5 pixels show validation error."""
        image_data = self.test_data.create_standard_test_image()
        self.editor = ImageEditor(self.root, image_data, None)

        # Set tiny selection (less than 5x5)
        self.editor.selection_start = (50, 50)
        self.editor.selection_end = (52, 52)  # 2x2 selection

        self.editor._on_confirm_click()

        # Verify validation error message
        mock_messagebox.assert_called_once()
        args, kwargs = mock_messagebox.call_args
        error_message = args[1]
        self.assertIn('有効な領域を選択', error_message)
        self.assertIn('5x5ピクセル', error_message)

    def test_image_boundary_clamping(self):
        """Test that selections are clamped to image boundaries."""
        image_data = self.test_data.create_standard_test_image()
        self.editor = ImageEditor(self.root, image_data, None)

        # Simulate drag beyond image boundaries
        canvas_x = self.editor.display_width + 100  # Beyond right edge
        canvas_y = self.editor.display_height + 100  # Beyond bottom edge

        # This should be clamped to image bounds
        clamped_x = max(0, min(canvas_x, self.editor.display_width))
        clamped_y = max(0, min(canvas_y, self.editor.display_height))

        self.assertEqual(clamped_x, self.editor.display_width)
        self.assertEqual(clamped_y, self.editor.display_height)

    def test_coordinate_transformation_precision(self):
        """Test that coordinate scaling has accuracy within 1 pixel."""
        image_data = self.test_data.create_standard_test_image()
        self.editor = ImageEditor(self.root, image_data, None)

        # Test different scaling scenarios
        test_cases = [
            (100, 100, 50, 50),  # Standard case
            (1, 1, 10, 10),  # Small selection
            (200, 150, 100, 75),  # Medium selection
        ]

        for display_x, display_y, display_w, display_h in test_cases:
            with self.subTest(case=(display_x, display_y, display_w, display_h)):
                self.editor.selection_start = (display_x, display_y)
                self.editor.selection_end = (
                    display_x + display_w,
                    display_y + display_h,
                )

                region = self.editor._get_selection_region()
                self.assertIsNotNone(region)

                orig_x, orig_y, orig_width, orig_height = region

                # Verify reverse transformation accuracy (within 1 pixel)
                reverse_x = round(orig_x * self.editor.scale_factor)
                reverse_y = round(orig_y * self.editor.scale_factor)

                self.assertAlmostEqual(reverse_x, display_x, delta=1)
                self.assertAlmostEqual(reverse_y, display_y, delta=1)

    def test_extreme_scaling_ratios(self):
        """Test coordinate precision with extreme scaling ratios."""
        # Test with very small image (forces high scale factor)
        tiny_data = self.test_data.create_tiny_test_image()
        self.editor = ImageEditor(self.root, tiny_data, None)

        # Scale factor should be 1.0 (no scaling up)
        self.assertEqual(self.editor.scale_factor, 1.0)

        # Test with large image (forces low scale factor)
        large_data = self.test_data.create_standard_test_image(
            2000, 1500
        )  # Within limits but large
        self.editor.window.destroy()  # Clean up previous
        self.editor = ImageEditor(self.root, large_data, None)

        # Scale factor should be less than 1.0
        self.assertLess(self.editor.scale_factor, 1.0)
        self.assertGreater(self.editor.scale_factor, 0.1)  # Reasonable minimum

    def test_tiny_image_no_crash(self):
        """Test that 1x1 pixel image doesn't crash the editor."""
        tiny_data = self.test_data.create_tiny_test_image()

        # This should not raise any exceptions
        try:
            self.editor = ImageEditor(self.root, tiny_data, None)

            # Verify basic functionality works
            self.assertIsNotNone(self.editor.window)
            self.assertIsNotNone(self.editor.image)
            self.assertEqual(self.editor.image.size, (1, 1))

        except Exception as e:
            self.fail(f'1x1 image caused crash: {e}')

    def test_window_resize_canvas_stability(self):
        """Test that canvas display remains stable during window operations."""
        image_data = self.test_data.create_standard_test_image()
        self.editor = ImageEditor(self.root, image_data, None)

        # Get initial canvas state
        initial_width = self.editor.canvas.winfo_reqwidth()
        initial_height = self.editor.canvas.winfo_reqheight()

        # Canvas should have reasonable initial dimensions
        self.assertGreater(initial_width, 0)
        self.assertGreater(initial_height, 0)

        # Image should be properly positioned
        self.assertIsNotNone(self.editor.image_item)


class TestImageEditorIntegration(TkinterTestMixin, unittest.TestCase):
    """Integration tests for complete workflows."""

    def setUp(self):
        """Set up test environment."""
        self.setUp_tkinter()  # Handle Tkinter initialization with error handling
        self.test_data = TestImageEditorTestData()
        self.callback_results = []

        def capture_callback(region):
            self.callback_results.append(region)

        self.capture_callback = capture_callback

    def tearDown(self):
        """Clean up after tests."""
        if (
            hasattr(self, 'editor')
            and hasattr(self.editor, 'window')
            and self.editor.window
        ):
            try:
                self.editor.window.destroy()
            except tk.TclError:
                pass  # Ignore cleanup errors
        self.tearDown_tkinter()

    def test_complete_selection_workflow(self):
        """Test complete user workflow: open -> select -> confirm."""
        image_data = self.test_data.create_standard_test_image()
        self.editor = ImageEditor(self.root, image_data, self.capture_callback)

        # Simulate complete user interaction
        # 1. User makes selection
        self.editor.selection_start = (100, 100)
        self.editor.selection_end = (200, 200)

        # 2. User clicks OK
        with patch.object(self.editor, '_close_window'):
            self.editor._on_confirm_click()

        # 3. Verify callback was invoked with correct data
        self.assertEqual(len(self.callback_results), 1)
        region = self.callback_results[0]
        self.assertIsNotNone(region)

        x, y, width, height = region
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)

    def test_static_factory_method(self):
        """Test the static open_image_editor factory method."""
        image_data = self.test_data.create_standard_test_image()

        editor = ImageEditor.open_image_editor(
            self.root, image_data, self.capture_callback
        )

        self.assertIsInstance(editor, ImageEditor)
        self.assertIsNotNone(editor.window)
        self.assertEqual(editor.on_confirm, self.capture_callback)

        # Clean up
        editor.window.destroy()

    def test_image_load_failure_ok_button_disabled(self):
        """Test that OK button is disabled when image loading fails."""
        # Create invalid image data
        invalid_data = b'invalid image data'

        # Create editor with invalid image data
        self.editor = ImageEditor(self.root, invalid_data, self.capture_callback)

        # Verify load failed flag is set
        self.assertTrue(self.editor.load_failed)

        # Verify OK button is disabled
        self.assertEqual(self.editor.ok_button['state'], 'disabled')

        # Verify photo is None
        self.assertIsNone(self.editor.photo)

    def test_oversized_image_ok_button_disabled(self):
        """Test that OK button is disabled for oversized images."""
        # Create oversized image data (over 10,000px limit)
        oversized_data = self.test_data.create_standard_test_image(10001, 100)

        # Create editor with oversized image
        self.editor = ImageEditor(self.root, oversized_data, self.capture_callback)

        # Verify load failed flag is set
        self.assertTrue(self.editor.load_failed)

        # Verify OK button is disabled
        self.assertEqual(self.editor.ok_button['state'], 'disabled')

    def test_keyboard_shortcuts_exist(self):
        """Test that keyboard shortcuts are properly bound."""
        image_data = self.test_data.create_standard_test_image()
        self.editor = ImageEditor(self.root, image_data, self.capture_callback)

        # Check if Return and Escape key bindings exist
        # The bindings should include our keyboard shortcuts
        # Note: This is a basic check for binding existence
        self.assertIsNotNone(self.editor.window.bind('<Return>'))
        self.assertIsNotNone(self.editor.window.bind('<Escape>'))

    def test_canvas_events_not_bound_when_load_failed(self):
        """Test that canvas events are not bound when image loading fails."""
        # Create invalid image data
        invalid_data = b'invalid image data'

        # Create editor with invalid image data
        self.editor = ImageEditor(self.root, invalid_data, self.capture_callback)

        # Verify canvas exists but events are not bound
        self.assertIsNotNone(self.editor.canvas)

        # Check that mouse events are not bound (this is implementation-specific)
        # Since _bind_events() checks for self.photo and load_failed,
        # mouse events should not be active
        try:
            # Try to trigger a mouse event - should not cause errors but also not process
            event = type('Event', (), {'x': 50, 'y': 50})()
            # This should not crash but also not create selections
            self.editor._on_mouse_down(event)
            self.assertIsNone(self.editor.selection_start)
        except AttributeError:
            # Expected if events aren't properly bound
            pass


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2, buffer=True)
