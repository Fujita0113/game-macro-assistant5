"""
Tests for the image editor functionality.

This module tests the image editing window that allows users to select
rectangular areas from screenshots for macro condition checking.
"""

import os
import sys
import pytest
import tkinter as tk
from unittest.mock import patch
from PIL import Image

# Fix TCL environment for Windows (both Python 3.10 and 3.13)
if sys.platform == 'win32':
    python_root = os.path.dirname(sys.executable)
    tcl_path = os.path.join(python_root, 'tcl')
    if os.path.exists(tcl_path):
        os.environ['TCL_LIBRARY'] = os.path.join(tcl_path, 'tcl8.6')
        os.environ['TK_LIBRARY'] = os.path.join(tcl_path, 'tk8.6')

# Global Tkinter session management
_tk_session = None
_has_display = None


def _check_display():
    """Check if display is available for Tkinter."""
    global _has_display, _tk_session
    if _has_display is not None:
        return _has_display

    try:
        _tk_session = tk.Tk()
        _tk_session.withdraw()
        _has_display = True
        return True
    except tk.TclError:
        _has_display = False
        return False


def _cleanup_tk_session():
    """Clean up the global Tkinter session."""
    global _tk_session
    if _tk_session:
        try:
            _tk_session.destroy()
        except tk.TclError:
            pass
        _tk_session = None


# Initialize display check
_check_display()

# Register cleanup function
import atexit

atexit.register(_cleanup_tk_session)


# pytest fixture to provide fresh Tk environment for each test
@pytest.fixture
def tk_root():
    """Provide a clean Tk environment for each test."""
    global _tk_session

    if not _has_display:
        pytest.skip('No display available')

    # Ensure we have a valid session
    if not _tk_session or not _tk_session.winfo_exists():
        _tk_session = tk.Tk()
        _tk_session.withdraw()

    # Clean up any existing child widgets
    for child in _tk_session.winfo_children():
        try:
            child.destroy()
        except tk.TclError:
            pass

    # Set as default root for this test
    tk._default_root = _tk_session

    yield _tk_session

    # Post-test cleanup
    for child in _tk_session.winfo_children():
        try:
            child.destroy()
        except tk.TclError:
            pass


pytestmark = pytest.mark.skipif(not _has_display, reason='No display available')


def test_image_editor_window_initialization(tk_root):
    """Test that ImageEditor window initializes correctly."""
    # This test will fail until we implement the ImageEditor class
    from src.ui.image_editor import ImageEditor

    test_image = Image.new('RGB', (100, 100), color='red')

    editor = ImageEditor(tk_root, test_image)

    # Should have a title
    assert editor.title() == '画像編集'

    # Should be properly initialized
    assert editor is not None


def test_rectangle_selection_functionality(tk_root):
    """Test that mouse drag creates a rectangle selection."""
    from src.ui.image_editor import ImageEditor

    test_image = Image.new('RGB', (100, 100), color='red')

    editor = ImageEditor(tk_root, test_image)

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
    assert editor.selection_coords == (10, 10, 50, 50), (
        f'Expected (10, 10, 50, 50), got: {editor.selection_coords}'
    )


def test_selection_area_highlight_display(tk_root):
    """Test that selection area is properly highlighted."""
    from src.ui.image_editor import ImageEditor

    test_image = Image.new('RGB', (100, 100), color='red')

    editor = ImageEditor(tk_root, test_image)
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

    # Check if rectangle is properly created on canvas
    rect_coords = editor.canvas.coords(editor.selection_rect)
    assert rect_coords == [10, 10, 50, 50]


def test_minimum_selection_size_error(tk_root):
    """Test that selections smaller than 5x5 pixels show error message."""
    from src.ui.image_editor import ImageEditor

    test_image = Image.new('RGB', (100, 100), color='red')

    editor = ImageEditor(tk_root, test_image)
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

        # Should have shown error message
        mock_error.assert_called_once()
        assert '5x5ピクセル以上' in str(mock_error.call_args)


def test_no_error_for_valid_selection_size(tk_root):
    """Test that selections 5x5 pixels or larger do not show error."""
    from src.ui.image_editor import ImageEditor

    test_image = Image.new('RGB', (100, 100), color='red')

    editor = ImageEditor(tk_root, test_image)
    tk_root.update()

    # Mock the messagebox to ensure no error is shown
    with patch('tkinter.messagebox.showerror') as mock_error:
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


if __name__ == '__main__':
    pytest.main([__file__])
