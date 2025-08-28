"""
Global pytest configuration and fixtures.

This module provides shared test fixtures for the entire test suite,
including simplified Tkinter environment management.
"""

import os
import sys
import pytest
import tkinter as tk


# Fix TCL environment for Windows
if sys.platform == 'win32':
    python_root = os.path.dirname(sys.executable)
    tcl_path = os.path.join(python_root, 'tcl')
    if os.path.exists(tcl_path):
        os.environ['TCL_LIBRARY'] = os.path.join(tcl_path, 'tcl8.6')
        os.environ['TK_LIBRARY'] = os.path.join(tcl_path, 'tk8.6')


def _check_display():
    """Check if display is available for Tkinter."""
    try:
        root = tk.Tk()
        root.withdraw()
        root.destroy()
        return True
    except tk.TclError:
        return False


# Global display availability check
HAS_DISPLAY = _check_display()


@pytest.fixture
def tk_root():
    """
    Provide a clean Tk environment for each test.

    This fixture creates a fresh Tkinter root window for each test,
    ensuring test isolation and proper cleanup.
    """
    if not HAS_DISPLAY:
        pytest.skip('No display available')

    # Create fresh root for this test
    root = tk.Tk()
    root.withdraw()  # Hide the window

    yield root

    # Cleanup
    try:
        root.destroy()
    except tk.TclError:
        pass  # Already destroyed


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
