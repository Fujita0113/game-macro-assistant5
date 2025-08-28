#!/usr/bin/env python3
"""
Test script for multiple recording cycles to verify visual editor reuse fix.
"""

import time
import sys
import os
import tkinter as tk

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.recording_controller import RecordingController
from core.macro_data import (
    MacroRecording,
    create_mouse_click_operation,
    create_key_operation,
)
from core.macro_data import MouseButton, Position


def create_test_recording(name: str, operation_count: int = 3) -> MacroRecording:
    """Create a test recording with dummy operations."""
    recording = MacroRecording(
        name=name,
        created_at=time.time(),
        operations=[],
        metadata={'created_by': 'TestScript'},
    )

    # Add dummy operations
    for i in range(operation_count):
        # Add mouse click
        mouse_op = create_mouse_click_operation(
            MouseButton.LEFT,
            Position(x=100 + i * 50, y=200 + i * 30),
            time.time() + i * 0.1,
        )
        recording.add_operation(mouse_op)

        # Add key press
        key_op = create_key_operation(
            f'key_{i}', 'press', [], time.time() + i * 0.1 + 0.05
        )
        recording.add_operation(key_op)

    return recording


def test_multiple_visual_editor_cycles():
    """Test opening visual editor multiple times to verify no widget reuse issues."""
    print('=== Testing Multiple Visual Editor Cycles ===')

    # Create Tkinter root for the test
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    try:
        controller = RecordingController()

        # Test multiple cycles
        for cycle in range(3):
            print(f'\n--- Cycle {cycle + 1} ---')

            # Create test recording
            test_recording = create_test_recording(f'TestRecording_{cycle + 1}')

            print(
                f'Opening visual editor with {test_recording.operation_count} operations...'
            )

            try:
                # Open visual editor
                controller.open_visual_editor(test_recording)
                print('[OK] Visual editor opened successfully')

                # Wait a moment
                time.sleep(0.5)

                # Close visual editor
                controller.close_visual_editor()
                print('[OK] Visual editor closed successfully')

                # Wait a moment before next cycle
                time.sleep(0.2)

            except Exception as e:
                print(f'[FAIL] Error in cycle {cycle + 1}: {e}')
                return False

        print('\n=== All cycles completed successfully! ===')
        return True

    except Exception as e:
        print(f'[FAIL] Test failed: {e}')
        return False

    finally:
        try:
            root.destroy()
        except Exception:
            pass


def test_recording_completion_cycles():
    """Test recording completion handler multiple times."""
    print('\n=== Testing Recording Completion Cycles ===')

    root = tk.Tk()
    root.withdraw()

    try:
        controller = RecordingController()

        # Test multiple completion cycles
        for cycle in range(3):
            print(f'\n--- Completion Cycle {cycle + 1} ---')

            test_recording = create_test_recording(f'CompletionTest_{cycle + 1}')

            try:
                # Simulate recording completion
                controller._handle_recording_completion(test_recording)
                print('[OK] Recording completion handled successfully')

                # Wait and cleanup
                time.sleep(0.5)
                if controller.visual_editor:
                    controller.close_visual_editor()

                time.sleep(0.2)

            except Exception as e:
                print(f'[FAIL] Error in completion cycle {cycle + 1}: {e}')
                return False

        print('\n=== All completion cycles successful! ===')
        return True

    except Exception as e:
        print(f'[FAIL] Completion test failed: {e}')
        return False

    finally:
        try:
            root.destroy()
        except Exception:
            pass


if __name__ == '__main__':
    print('Testing Visual Editor Multiple Cycles...')

    # Test 1: Direct visual editor cycles
    success1 = test_multiple_visual_editor_cycles()

    # Test 2: Recording completion cycles
    success2 = test_recording_completion_cycles()

    if success1 and success2:
        print(
            '\n[SUCCESS] ALL TESTS PASSED! Visual editor multiple cycles working correctly.'
        )
        sys.exit(0)
    else:
        print('\n[FAIL] SOME TESTS FAILED! Check the output above.')
        sys.exit(1)
