"""
Tests for the image editor functionality.

This module tests the image editing window that allows users to select
rectangular areas from screenshots for macro condition checking.
"""

import pytest
import tkinter as tk
from unittest.mock import patch
from PIL import Image

# Skip all tests if running in headless environment (like CI)
try:
    root = tk.Tk()
    root.destroy()
    _has_display = True
except tk.TclError:
    _has_display = False

pytestmark = pytest.mark.skipif(not _has_display, reason='No display available')


def test_image_editor_window_initialization():
    """Test that ImageEditor window initializes correctly."""
    # This test will fail until we implement the ImageEditor class
    from src.ui.image_editor import ImageEditor

    root = tk.Tk()
    test_image = Image.new('RGB', (100, 100), color='red')

    editor = ImageEditor(root, test_image)

    # Should have a title
    assert editor.title() == '画像編集'

    # Should be properly initialized
    assert editor is not None

    root.destroy()


def test_rectangle_selection_functionality():
    """Test that mouse drag creates a rectangle selection."""
    from src.ui.image_editor import ImageEditor

    root = tk.Tk()
    test_image = Image.new('RGB', (100, 100), color='red')

    editor = ImageEditor(root, test_image)

    # Simulate mouse drag for rectangle selection
    # Update the window to ensure proper initialization
    root.update()

    # Start drag at (10, 10)
    editor.canvas.event_generate('<Button-1>', x=10, y=10)
    root.update()
    # Drag to (50, 50)
    editor.canvas.event_generate('<B1-Motion>', x=50, y=50)
    root.update()
    # End drag
    editor.canvas.event_generate('<ButtonRelease-1>', x=50, y=50)
    root.update()

    # Should have created a selection rectangle
    assert editor.selection_coords is not None
    assert editor.selection_coords == (10, 10, 50, 50)

    root.destroy()


def test_selection_area_highlight_display():
    """Test that selection area is properly highlighted."""
    from src.ui.image_editor import ImageEditor

    root = tk.Tk()
    test_image = Image.new('RGB', (100, 100), color='red')

    editor = ImageEditor(root, test_image)
    root.update()

    # Start selection
    editor.canvas.event_generate('<Button-1>', x=10, y=10)
    root.update()

    # Should not have selection rectangle yet
    assert editor.selection_rect is None

    # Drag to create selection
    editor.canvas.event_generate('<B1-Motion>', x=50, y=50)
    root.update()

    # Should now have selection rectangle visible
    assert editor.selection_rect is not None

    # Check if rectangle is properly created on canvas
    rect_coords = editor.canvas.coords(editor.selection_rect)
    assert rect_coords == [10, 10, 50, 50]

    root.destroy()


def test_minimum_selection_size_error():
    """Test that selections smaller than 5x5 pixels show error message."""
    from src.ui.image_editor import ImageEditor

    root = tk.Tk()
    test_image = Image.new('RGB', (100, 100), color='red')

    editor = ImageEditor(root, test_image)
    root.update()

    # Mock the messagebox to capture error messages
    with patch('tkinter.messagebox.showerror') as mock_error:
        # Create a selection smaller than 5x5 pixels
        editor.canvas.event_generate('<Button-1>', x=10, y=10)
        root.update()
        editor.canvas.event_generate('<B1-Motion>', x=12, y=12)  # Only 2x2 pixels
        root.update()
        editor.canvas.event_generate('<ButtonRelease-1>', x=12, y=12)
        root.update()

        # Try to click OK button
        editor._on_ok()

        # Should have shown error message
        mock_error.assert_called_once()
        assert '5x5ピクセル以上' in str(mock_error.call_args)

    root.destroy()


def test_no_error_for_valid_selection_size():
    """Test that selections 5x5 pixels or larger do not show error."""
    from src.ui.image_editor import ImageEditor

    root = tk.Tk()
    test_image = Image.new('RGB', (100, 100), color='red')

    editor = ImageEditor(root, test_image)
    root.update()

    # Mock the messagebox to ensure no error is shown
    with patch('tkinter.messagebox.showerror') as mock_error:
        # Create a selection exactly 5x5 pixels
        editor.canvas.event_generate('<Button-1>', x=10, y=10)
        root.update()
        editor.canvas.event_generate('<B1-Motion>', x=15, y=15)  # 5x5 pixels
        root.update()
        editor.canvas.event_generate('<ButtonRelease-1>', x=15, y=15)
        root.update()

        # Try to click OK button
        editor._on_ok()

        # Should not have shown error message
        mock_error.assert_not_called()

    root.destroy()


if __name__ == '__main__':
    pytest.main([__file__])
