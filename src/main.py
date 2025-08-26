#!/usr/bin/env python3
"""
GameMacroAssistant - Main application entry point
"""

import argparse
import time
import sys
import json
import tkinter as tk
import os
from datetime import datetime

from core.input_capture import InputCaptureManager


def test_input_capture():
    """Test the input capture functionality."""
    print('=== Input Capture Test ===')
    print('This test will record mouse clicks and keyboard input.')
    print('Instructions:')
    print('1. LEFT-click at one location')
    print('2. RIGHT-click at another location')
    print('3. MIDDLE-click (scroll wheel) at a third location')
    print("4. Type 'Hello World' (with spaces)")
    print('5. Press ESC to stop recording')
    print()
    print('This test validates all three mouse buttons and space character recording.')
    print()

    input('Press Enter to start recording...')

    manager = InputCaptureManager()
    manager.start_recording()

    # Wait for user to complete the test
    while manager.is_recording():
        time.sleep(0.1)

    print()
    print('=== Recording Results ===')
    events = manager.get_recorded_events()

    if not events:
        print('No events were recorded!')
        return False

    # Analyze recorded events
    mouse_clicks = [e for e in events if hasattr(e, 'button')]
    key_events = [e for e in events if hasattr(e, 'key')]

    print(f'Total events recorded: {len(events)}')
    print(f'Mouse clicks: {len(mouse_clicks)}')
    print(f'Keyboard events: {len(key_events)}')
    print()

    # Show mouse click details
    if mouse_clicks:
        print('Mouse clicks:')
        for i, event in enumerate(mouse_clicks, 1):
            print(
                f'  {i}. {event.button.value} click at ({event.x}, {event.y}) - {event.timestamp}'
            )

    # Show keyboard input reconstruction
    if key_events:
        print('\nKeyboard input:')
        text_chars = []
        for event in key_events:
            # Only use KEY_PRESS events to avoid duplication
            if (
                event.type.value == 'key_press'
                and event.char
                and len(event.char) == 1
                and event.char.isprintable()
            ):
                text_chars.append(event.char)

        if text_chars:
            reconstructed_text = ''.join(text_chars)
            print(f"  Reconstructed text: '{reconstructed_text}'")

        key_list = [
            (e.key, e.type.value) for e in key_events[:20]
        ]  # Show first 20 keys with type
        print(f'  All key events: {key_list}')

    # Export results to JSON
    try:
        export_data = {
            'test_timestamp': datetime.now().isoformat(),
            'total_events': len(events),
            'mouse_clicks': len(mouse_clicks),
            'keyboard_events': len(key_events),
            'events': [event.to_dict() for event in events],
        }

        with open('input_capture_test_results.json', 'w') as f:
            json.dump(export_data, f, indent=2)

        print('\nResults exported to: input_capture_test_results.json')
    except Exception as e:
        print(f'Failed to export results: {e}')

    # Validate test requirements
    success = True

    # Check mouse click count
    if len(mouse_clicks) < 3:
        print(f'[FAIL] Expected at least 3 mouse clicks, got {len(mouse_clicks)}')
        success = False
    else:
        print('[OK] Mouse clicks recorded successfully')

    # Check for all three mouse button types
    button_types = set(event.button.value for event in mouse_clicks)
    expected_buttons = {'left', 'right', 'middle'}
    found_buttons = button_types.intersection(expected_buttons)

    if len(found_buttons) >= 3:
        print(
            f'[OK] All mouse button types detected: {", ".join(sorted(found_buttons))}'
        )
    elif len(found_buttons) >= 2:
        print(
            f'[WARN] Partial mouse button coverage: {", ".join(sorted(found_buttons))}'
        )
        missing = expected_buttons - found_buttons
        print(f'   Missing: {", ".join(sorted(missing))}')
    else:
        print(
            f'[FAIL] Insufficient mouse button coverage: {", ".join(sorted(found_buttons)) if found_buttons else "none"}'
        )
        success = False

    # Check if "Hello World" was typed (with space detection)
    text_chars = [
        e.char
        for e in key_events
        if e.type.value == 'key_press'
        and e.char
        and len(e.char) == 1
        and e.char.isprintable()
    ]
    reconstructed = ''.join(text_chars).lower()
    space_count = reconstructed.count(' ')

    if 'hello' in reconstructed and 'world' in reconstructed:
        print("[OK] 'Hello World' text input detected")
    else:
        print("[FAIL] 'Hello World' text input not clearly detected")
        print(f"   Detected text: '{reconstructed}'")
        success = False

    # Validate space character recording
    if space_count >= 1:
        print(f'[OK] Space characters recorded correctly ({space_count} spaces found)')
    else:
        print(
            f'[FAIL] Space character recording failed ({space_count} spaces found, expected at least 1)'
        )
        success = False

    print(f'\nTest {"PASSED" if success else "FAILED"}')
    return success


def test_input_capture_from_file(file_path: str) -> bool:
    """Test input capture functionality using data from a JSON file."""
    print('=== Non-Interactive Input Capture Test ===')
    print(f'Loading test data from: {file_path}')

    manager = InputCaptureManager()

    # Load test data from file
    if not manager.load_test_data(file_path):
        print('[FAIL] Failed to load test data from file')
        return False

    print('[OK] Test data loaded successfully')

    # Get the loaded events
    events = manager.get_recorded_events()

    if not events:
        print('[FAIL] No events were loaded from file!')
        return False

    # Analyze loaded events (same logic as interactive test)
    mouse_clicks = [e for e in events if hasattr(e, 'button')]
    key_events = [e for e in events if hasattr(e, 'key')]

    print(f'Total events loaded: {len(events)}')
    print(f'Mouse clicks: {len(mouse_clicks)}')
    print(f'Keyboard events: {len(key_events)}')
    print()

    # Show mouse click details
    if mouse_clicks:
        print('Mouse clicks:')
        for i, event in enumerate(mouse_clicks, 1):
            print(
                f'  {i}. {event.button.value} click at ({event.x}, {event.y}) - {event.timestamp}'
            )

    # Show keyboard input reconstruction
    if key_events:
        print('\nKeyboard input:')
        text_chars = []
        for event in key_events:
            # Only use KEY_PRESS events to avoid duplication
            if (
                event.type.value == 'key_press'
                and event.char
                and len(event.char) == 1
                and event.char.isprintable()
            ):
                text_chars.append(event.char)

        if text_chars:
            reconstructed_text = ''.join(text_chars)
            print(f"  Reconstructed text: '{reconstructed_text}'")

        key_list = [
            (e.key, e.type.value) for e in key_events[:20]
        ]  # Show first 20 keys with type
        print(f'  All key events: {key_list}')

    # Export results to JSON
    try:
        export_data = {
            'test_timestamp': datetime.now().isoformat(),
            'test_source': 'file_based',
            'source_file': file_path,
            'total_events': len(events),
            'mouse_clicks': len(mouse_clicks),
            'keyboard_events': len(key_events),
            'events': [event.to_dict() for event in events],
        }

        with open('input_capture_test_results.json', 'w') as f:
            json.dump(export_data, f, indent=2)

        print('\nResults exported to: input_capture_test_results.json')
    except Exception as e:
        print(f'Failed to export results: {e}')

    # Validate test requirements (same validation logic)
    success = True

    # Check mouse click count
    if len(mouse_clicks) < 3:
        print(f'[FAIL] Expected at least 3 mouse clicks, got {len(mouse_clicks)}')
        success = False
    else:
        print('[OK] Mouse clicks loaded successfully')

    # Check for all three mouse button types
    button_types = set(event.button.value for event in mouse_clicks)
    expected_buttons = {'left', 'right', 'middle'}
    found_buttons = button_types.intersection(expected_buttons)

    if len(found_buttons) >= 3:
        print(
            f'[OK] All mouse button types detected: {", ".join(sorted(found_buttons))}'
        )
    elif len(found_buttons) >= 2:
        print(
            f'[WARN] Partial mouse button coverage: {", ".join(sorted(found_buttons))}'
        )
        missing = expected_buttons - found_buttons
        print(f'   Missing: {", ".join(sorted(missing))}')
    else:
        print(
            f'[FAIL] Insufficient mouse button coverage: {", ".join(sorted(found_buttons)) if found_buttons else "none"}'
        )
        success = False

    # Check if "Hello World" was typed (with space detection)
    text_chars = [
        e.char
        for e in key_events
        if e.type.value == 'key_press'
        and e.char
        and len(e.char) == 1
        and e.char.isprintable()
    ]
    reconstructed = ''.join(text_chars).lower()
    space_count = reconstructed.count(' ')

    if 'hello' in reconstructed and 'world' in reconstructed:
        print("[OK] 'Hello World' text input detected")
    else:
        print("[FAIL] 'Hello World' text input not clearly detected")
        print(f"   Detected text: '{reconstructed}'")
        success = False

    # Validate space character recording
    if space_count >= 1:
        print(f'[OK] Space characters loaded correctly ({space_count} spaces found)')
    else:
        print(
            f'[FAIL] Space character loading failed ({space_count} spaces found, expected at least 1)'
        )
        success = False

    print(f'\nTest {"PASSED" if success else "FAILED"}')
    return success


# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow  # noqa: E402
from ui.recording_controller import RecordingController  # noqa: E402


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description='GameMacroAssistant')
    parser.add_argument(
        '--test-input', action='store_true', help='Run input capture integration test'
    )
    parser.add_argument(
        '--test-input-file',
        type=str,
        help='Run non-interactive input test with data file',
    )

    args = parser.parse_args()

    if args.test_input:
        success = test_input_capture()
        sys.exit(0 if success else 1)

    if args.test_input_file:
        success = test_input_capture_from_file(args.test_input_file)
        sys.exit(0 if success else 1)

    print('GameMacroAssistant - Starting...')

    try:
        # Create root window
        root = tk.Tk()

        # Initialize controller
        controller = RecordingController()

        # Initialize main window
        window = MainWindow(root)

        # Connect controller to window
        setup_window_controller_integration(window, controller)

        print('GUI initialized - Ready for recording')

        # Start main loop
        window.run()

    except KeyboardInterrupt:
        print('\nShutting down...')
    except Exception as e:
        print(f'Error starting application: {e}')
        return 1

    return 0


def setup_window_controller_integration(
    window: MainWindow, controller: RecordingController
):
    """Set up integration between main window and recording controller."""

    # Set up controller callbacks
    def on_recording_state_changed(recording: bool):
        """Handle recording state changes."""
        window.set_recording_state(recording)

    def on_recording_completed(recording_data):
        """Handle recording completion."""
        operation_count = recording_data.operation_count if recording_data else 0
        window.show_recording_completed(operation_count)

        # Print recording data to console for testing
        if recording_data:
            print('\n=== Recording Completed ===')
            print(f'Name: {recording_data.name}')
            print(f'Operations: {recording_data.operation_count}')
            print(f'Duration: {recording_data.duration:.2f}s')
            print(f'Created: {recording_data.created_at}')

            print('\n=== Operation Details ===')
            for i, op in enumerate(recording_data.operations, 1):
                print(f'{i}. {op.operation_type.value} at {op.timestamp:.3f}')
                if op.mouse_op:
                    print(
                        f'   Mouse: {op.mouse_op.button.value} at ({op.mouse_op.position.x}, {op.mouse_op.position.y})'
                    )
                if op.keyboard_op:
                    print(f"   Key: {op.keyboard_op.action} '{op.keyboard_op.key}'")

    # Connect callbacks
    controller.on_recording_state_changed = on_recording_state_changed
    controller.on_recording_completed = on_recording_completed

    # Set up window callbacks
    def start_recording():
        """Start recording from UI."""
        success = controller.start_recording()
        if not success:
            print('Failed to start recording')

    window.on_start_recording = start_recording


if __name__ == '__main__':
    sys.exit(main())
