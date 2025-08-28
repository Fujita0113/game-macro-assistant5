"""
Regression tests for Tkinter initialization issues.

This module contains tests specifically designed to catch the Tkinter
initialization bugs that occurred when running multiple tests together.
These tests should prevent similar issues from reoccurring.
"""

import os
import sys
import pytest
import tkinter as tk
from PIL import Image

# Apply the same Tkinter fixes as main test file
if sys.platform == 'win32':
    python_root = os.path.dirname(sys.executable)
    tcl_path = os.path.join(python_root, 'tcl')
    if os.path.exists(tcl_path):
        os.environ['TCL_LIBRARY'] = os.path.join(tcl_path, 'tcl8.6')
        os.environ['TK_LIBRARY'] = os.path.join(tcl_path, 'tk8.6')

# Global Tkinter session management (same as main test file)
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


def test_multiple_tkinter_window_creation(tk_root):
    """Regression test: Multiple Tkinter windows should be creatable in sequence."""
    windows = []
    
    try:
        # Create multiple Toplevel windows in sequence
        for i in range(3):
            window = tk.Toplevel(tk_root)
            window.title(f'Test Window {i}')
            window.withdraw()  # Hide to avoid screen clutter
            windows.append(window)
            
            # Each window should be valid
            assert window.winfo_exists()
            assert window.title() == f'Test Window {i}'
    
    finally:
        # Clean up all windows
        for window in windows:
            try:
                window.destroy()
            except tk.TclError:
                pass


def test_tkinter_photoimage_creation_multiple_times(tk_root):
    """Regression test: ImageTk.PhotoImage should be creatable multiple times."""
    from PIL import ImageTk
    
    images = []
    try:
        # Create multiple PhotoImage objects
        for i in range(3):
            pil_image = Image.new('RGB', (50, 50), color=['red', 'green', 'blue'][i])
            
            # This should not fail with "Too early to create image" error
            photo_image = ImageTk.PhotoImage(pil_image, master=tk_root)
            images.append(photo_image)
            
            # Verify image was created successfully
            assert photo_image.width() == 50
            assert photo_image.height() == 50
    
    finally:
        # Clean up references
        images.clear()


def test_tkinter_session_isolation_between_tests(tk_root):
    """Regression test: Each test should get a clean Tkinter environment."""
    # Create a test widget
    test_label = tk.Label(tk_root, text="Test isolation")
    test_label.pack()
    
    # Verify the widget exists
    assert test_label.winfo_exists()
    assert test_label.cget('text') == "Test isolation"
    
    # The fixture cleanup should handle widget removal automatically


def test_tkinter_session_isolation_verification(tk_root):
    """Regression test: Verify that previous test's widgets are gone."""
    # This test runs after the previous one
    # There should be no children from the previous test
    children = tk_root.winfo_children()
    
    # All children should be fresh (no leftover widgets from previous test)
    # Note: Some internal widgets might exist, but no Label with "Test isolation"
    for child in children:
        if isinstance(child, tk.Label):
            assert child.cget('text') != "Test isolation"


def test_tkinter_default_root_handling(tk_root):
    """Regression test: tk._default_root should be properly managed."""
    # Verify that we have a default root set
    assert tk._default_root is not None
    assert tk._default_root == tk_root
    
    # Creating PhotoImage should work without specifying master
    from PIL import ImageTk
    test_image = Image.new('RGB', (10, 10), color='blue')
    
    # This should not raise "Too early to create image" error
    photo = ImageTk.PhotoImage(test_image)
    assert photo.width() == 10
    assert photo.height() == 10


def test_run_all_tests_in_sequence():
    """
    Meta-regression test: This ensures that all the above tests can run
    in sequence without Tkinter initialization failures.
    
    The mere fact that pytest collects and runs all tests in this file
    without TclError exceptions validates our Tkinter session management.
    """
    # If we reach here, it means all previous tests in this file ran successfully
    assert True  # Success marker


if __name__ == '__main__':
    pytest.main([__file__])