"""
Display setup utilities for headless testing environments.

This module provides utilities to set up virtual displays and detect
available display backends for running GUI tests in CI/CD environments.
"""

import os
import sys
import tkinter as tk
from typing import Optional, Tuple


def get_display_backend() -> str:
    """
    Detect available display backend.

    Returns:
        str: The detected display backend ('x11', 'windows', 'headless', 'unavailable')
    """
    # Check if we're on Windows
    if sys.platform.startswith('win'):
        return 'windows'

    # Check if DISPLAY is set (Linux/macOS with X11)
    if 'DISPLAY' in os.environ:
        return 'x11'

    # Check for common headless indicators
    if any(
        var in os.environ for var in ['CI', 'GITHUB_ACTIONS', 'JENKINS_URL', 'TRAVIS']
    ):
        return 'headless'

    # Try to create a test Tk instance to see if display works
    try:
        root = tk.Tk()
        root.withdraw()
        root.destroy()
        return 'x11'  # Fallback working display
    except tk.TclError:
        return 'unavailable'


def setup_headless_display() -> Tuple[bool, str]:
    """
    Set up headless display for CI environments.

    Returns:
        Tuple[bool, str]: (success, message)
    """
    backend = get_display_backend()

    if backend == 'windows':
        # Windows doesn't need special headless setup
        return True, 'Windows display backend detected'

    if backend == 'x11':
        # Already have working display
        return True, 'X11 display backend available'

    if backend == 'headless':
        # Try to set up Xvfb if available
        try:
            # Check if Xvfb is available
            import subprocess

            result = subprocess.run(['which', 'Xvfb'], capture_output=True, text=True)
            if result.returncode == 0:
                # Xvfb is available, set a virtual display
                os.environ['DISPLAY'] = ':99'
                return True, 'Virtual display :99 configured for headless environment'
            else:
                return False, 'Headless environment detected but Xvfb not available'
        except Exception as e:
            return False, f'Failed to set up headless display: {e}'

    return False, 'No suitable display backend available'


def ensure_display_available() -> bool:
    """
    Ensure a display is available for GUI tests.

    Returns:
        bool: True if display is available, False otherwise
    """
    try:
        # Try to create a simple Tk window
        root = tk.Tk()
        root.withdraw()  # Hide the window
        root.destroy()
        return True
    except tk.TclError:
        # Try headless setup
        success, message = setup_headless_display()
        if success:
            # Test again after headless setup
            try:
                root = tk.Tk()
                root.withdraw()
                root.destroy()
                return True
            except tk.TclError:
                pass
        return False


def create_test_root_with_retry(max_attempts: int = 3) -> Optional[tk.Tk]:
    """
    Create a Tk root window with retry logic for resource contention.

    Args:
        max_attempts: Maximum number of attempts to create the window

    Returns:
        Optional[tk.Tk]: The created root window, or None if failed
    """
    import time

    for attempt in range(max_attempts):
        try:
            root = tk.Tk()
            root.withdraw()  # Hide window during tests
            return root
        except tk.TclError as e:
            if attempt < max_attempts - 1:
                # Wait a bit before retrying
                time.sleep(0.1 * (attempt + 1))
                continue
            else:
                # Last attempt failed
                print(f'Failed to create Tk root after {max_attempts} attempts: {e}')
                return None

    return None


def cleanup_tk_resources():
    """
    Clean up any lingering Tk resources.

    This helps prevent resource leaks between tests.
    """
    try:
        # Force garbage collection
        import gc

        gc.collect()

        # Try to clean up any remaining Tk state
        if hasattr(tk, '_default_root') and tk._default_root:
            try:
                tk._default_root.destroy()
            except Exception:
                pass
            tk._default_root = None
    except Exception:
        # Ignore cleanup errors
        pass
