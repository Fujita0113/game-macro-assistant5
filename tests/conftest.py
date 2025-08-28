"""
Global pytest configuration and fixtures.

This module provides shared test fixtures for the entire test suite,
including simplified Tkinter environment management.
"""

import os
import sys
import pytest
import tkinter as tk


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

# Global display availability check (for backward compatibility)
HAS_DISPLAY = _has_display


@pytest.fixture
def tk_root():
    """
    Provide a clean Tk environment for each test using unified session management.

    This fixture uses a global Tkinter session to avoid initialization conflicts,
    ensuring test isolation and proper cleanup.
    """
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


@pytest.fixture
def skip_if_no_display():
    """
    Fixture to skip tests if no display is available.

    Use this fixture for tests that require GUI but don't need a root window.
    """
    if not HAS_DISPLAY:
        pytest.skip('No display available')


# Mark to skip GUI tests when no display is available
pytestmark = pytest.mark.skipif(not HAS_DISPLAY, reason='No display available')
