"""
Simplified tests for the image editor functionality.

This module tests the image editing window that allows users to select
rectangular areas from screenshots for macro condition checking.
"""

import pytest
from unittest.mock import patch
from PIL import Image


class TestImageEditor:
    """Test cases for ImageEditor with simplified Tkinter management."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_image = Image.new('RGB', (100, 100), color='red')

    def test_image_editor_window_initialization(self, tk_root):
        """Test that ImageEditor window initializes correctly."""
        from src.ui.image_editor import ImageEditor

        editor = ImageEditor(tk_root, self.test_image)

        # Should have a title
        assert editor.title() == '画像編集'

        # Should be properly initialized
        assert editor is not None

    def test_rectangle_selection_functionality(self, tk_root):
        """Test that mouse drag creates a rectangle selection."""
        from src.ui.image_editor import ImageEditor

        editor = ImageEditor(tk_root, self.test_image)

        # Update the window to ensure proper initialization
        tk_root.update()
        editor.update()

        # Create mock event objects with x, y coordinates
        class MockEvent:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        # Simulate mouse press at (10, 10)
        press_event = MockEvent(10, 10)
        editor._on_mouse_press(press_event)

        # Simulate mouse drag to (50, 50)
        drag_event = MockEvent(50, 50)
        editor._on_mouse_drag(drag_event)

        # Simulate mouse release at (50, 50)
        release_event = MockEvent(50, 50)
        editor._on_mouse_release(release_event)

        # Should have created a selection rectangle
        assert editor.selection_coords is not None, (
            f'Expected selection_coords, got: {editor.selection_coords}'
        )
        assert editor.selection_coords == (
            10,
            10,
            50,
            50,
        ), f'Expected (10, 10, 50, 50), got: {editor.selection_coords}'

    def test_selection_area_highlight_display(self, tk_root):
        """Test that selection area is properly highlighted."""
        from src.ui.image_editor import ImageEditor

        editor = ImageEditor(tk_root, self.test_image)
        tk_root.update()

        # Create mock event objects
        class MockEvent:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        # Start selection at (10, 10)
        press_event = MockEvent(10, 10)
        editor._on_mouse_press(press_event)

        # Should not have selection rectangle yet
        assert editor.selection_rect is None

        # Drag to (50, 50) to create selection
        drag_event = MockEvent(50, 50)
        editor._on_mouse_drag(drag_event)

        # Should now have selection rectangle visible
        assert editor.selection_rect is not None

        # Check rectangle coordinates
        rect_coords = editor.canvas.coords(editor.selection_rect)
        assert rect_coords == [10, 10, 50, 50]

    def test_minimum_selection_size_error(self, tk_root):
        """Test that selections smaller than 5x5 pixels show error message."""
        from src.ui.image_editor import ImageEditor

        editor = ImageEditor(tk_root, self.test_image)
        tk_root.update()

        # Mock the messagebox to capture error messages
        with patch('tkinter.messagebox.showerror') as mock_error:
            # Create mock event objects
            class MockEvent:
                def __init__(self, x, y):
                    self.x = x
                    self.y = y

            # Create a selection smaller than 5x5 pixels
            press_event = MockEvent(10, 10)
            editor._on_mouse_press(press_event)

            drag_event = MockEvent(12, 12)  # Only 2x2 pixels
            editor._on_mouse_drag(drag_event)

            release_event = MockEvent(12, 12)
            editor._on_mouse_release(release_event)

            # Try to click OK button
            editor._on_ok()

            # Should show error message
            mock_error.assert_called_once()
            assert '5x5ピクセル以上' in str(mock_error.call_args)

    def test_no_error_for_valid_selection_size(self, tk_root):
        """Test that selections 5x5 pixels or larger do not show error."""
        from src.ui.image_editor import ImageEditor

        editor = ImageEditor(tk_root, self.test_image)
        tk_root.update()

        # Mock the messagebox to ensure no error is shown
        with (
            patch('tkinter.messagebox.showerror') as mock_error,
            patch('tkinter.messagebox.showinfo'),
        ):
            # Create mock event objects
            class MockEvent:
                def __init__(self, x, y):
                    self.x = x
                    self.y = y

            # Create a selection exactly 5x5 pixels
            press_event = MockEvent(10, 10)
            editor._on_mouse_press(press_event)

            drag_event = MockEvent(15, 15)  # 5x5 pixels
            editor._on_mouse_drag(drag_event)

            release_event = MockEvent(15, 15)
            editor._on_mouse_release(release_event)

            # Try to click OK button
            editor._on_ok()

            # Should not have shown error message
            mock_error.assert_not_called()

    def test_ok_without_selection_shows_error(self, tk_root):
        """Test that clicking OK without any selection shows error message."""
        from src.ui.image_editor import ImageEditor

        editor = ImageEditor(tk_root, self.test_image)
        tk_root.update()

        # Mock the messagebox to capture error messages
        with patch('tkinter.messagebox.showerror') as mock_error:
            # Try to click OK button without making any selection
            editor._on_ok()

            # Should show error message for no selection
            mock_error.assert_called_once()
            args = mock_error.call_args
            assert '選択' in str(args)

    def test_ok_with_selection_shows_status_message(self, tk_root):
        """Test that clicking OK with valid selection shows status message."""
        from src.ui.image_editor import ImageEditor

        editor = ImageEditor(tk_root, self.test_image)
        tk_root.update()

        # Mock the messagebox to capture status messages
        with patch('tkinter.messagebox.showinfo') as mock_info:
            # Create mock event objects
            class MockEvent:
                def __init__(self, x, y):
                    self.x = x
                    self.y = y

            # Create a valid selection (5x5 pixels)
            press_event = MockEvent(10, 10)
            editor._on_mouse_press(press_event)

            drag_event = MockEvent(15, 15)
            editor._on_mouse_drag(drag_event)

            release_event = MockEvent(15, 15)
            editor._on_mouse_release(release_event)

            # Click OK button
            editor._on_ok()

            # Should show status message
            mock_info.assert_called_once()
            args = mock_info.call_args
            assert '選択領域を保存しました' in str(args)


if __name__ == '__main__':
    pytest.main([__file__])
