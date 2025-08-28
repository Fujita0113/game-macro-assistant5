"""
Recording controller that integrates UI with capture systems.

This module coordinates between the main window UI and the input/screen
capture managers to provide unified recording control.
"""

import time
import threading
import traceback
from typing import Optional, Callable

from core.macro_data import (
    MacroRecording,
    OperationBlock,
    MouseButton,
    Position,
    create_mouse_click_operation,
    create_key_operation,
)
from core.input_capture import InputCaptureManager
from core.screen_capture import ScreenCaptureManager
from core.events import MouseEvent, KeyboardEvent, EventType


class RecordingController:
    """Controls the recording process and coordinates between UI and capture systems."""

    def __init__(self):
        """Initialize the recording controller."""
        self.input_capture = InputCaptureManager()
        self.screen_capture = ScreenCaptureManager()

        self.current_recording: Optional[MacroRecording] = None
        self.is_recording = False
        self._recording_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # UI callback
        self.on_recording_state_changed: Optional[Callable[[bool], None]] = None
        self.on_recording_completed: Optional[Callable[[MacroRecording], None]] = None

    def start_recording(self, recording_name: Optional[str] = None) -> bool:
        """
        Start a new recording session.

        Args:
            recording_name: Name for the recording (auto-generated if None)

        Returns:
            True if recording started successfully, False otherwise
        """
        if self.is_recording:
            print('Recording already in progress')
            return False

        try:
            # DEBUG: Log thread context
            current_thread = threading.current_thread()
            print(f'DEBUG: start_recording() called from thread: {current_thread.name} (ID: {current_thread.ident})')
            
            # Create new recording
            if recording_name is None:
                recording_name = f'Recording_{int(time.time())}'

            self.current_recording = MacroRecording(
                name=recording_name,
                created_at=time.time(),
                operations=[],
                metadata={'created_by': 'GameMacroAssistant'},
            )

            # Start capture systems
            self.input_capture.start_recording()  # InputCaptureManager uses start_recording()

            # Set recording state
            self.is_recording = True
            self._stop_event.clear()

            # Start monitoring thread for recording events
            self._recording_thread = threading.Thread(target=self._monitor_recording)
            self._recording_thread.daemon = True
            self._recording_thread.start()
            print(f'DEBUG: Monitoring thread started: {self._recording_thread.name} (ID: {self._recording_thread.ident})')

            # Notify UI
            if self.on_recording_state_changed:
                self.on_recording_state_changed(True)

            print(f'Recording started: {recording_name}')
            return True

        except Exception as e:
            print(f'Error starting recording: {e}')
            self._cleanup_recording()
            return False

    def stop_recording(self) -> Optional[MacroRecording]:
        """
        Stop the current recording session.

        Returns:
            The completed MacroRecording if successful, None otherwise
        """
        if not self.is_recording:
            print('No recording in progress')
            return None

        try:
            # DEBUG: Log thread context
            current_thread = threading.current_thread()
            print(f'DEBUG: stop_recording() called from thread: {current_thread.name} (ID: {current_thread.ident})')
            print(f'DEBUG: Recording thread is: {self._recording_thread.name if self._recording_thread else "None"} (ID: {self._recording_thread.ident if self._recording_thread else "None"})')
            # Stop recording
            self.is_recording = False
            self._stop_event.set()

            # Stop capture systems
            self.input_capture.stop_recording()  # InputCaptureManager uses stop_recording()

            # Wait for monitoring thread to finish
            if self._recording_thread and self._recording_thread.is_alive():
                print(f'DEBUG: About to join recording thread from thread: {threading.current_thread().name}')
                is_same_thread = threading.current_thread() == self._recording_thread
                print(f'DEBUG: Is current thread same as recording thread? {is_same_thread}')
                
                if not is_same_thread:
                    # Only join if we're not in the same thread (avoid "cannot join current thread" error)
                    self._recording_thread.join(timeout=1.0)
                    print(f'DEBUG: Thread join completed')
                else:
                    print(f'DEBUG: Skipping join - called from monitoring thread itself')

            # Get completed recording
            completed_recording = self.current_recording

            # Cleanup
            self._cleanup_recording()

            # Notify UI
            if self.on_recording_state_changed:
                self.on_recording_state_changed(False)

            if completed_recording and self.on_recording_completed:
                self.on_recording_completed(completed_recording)

            print(
                f'Recording stopped. Operations recorded: {completed_recording.operation_count if completed_recording else 0}'
            )
            return completed_recording

        except Exception as e:
            print(f'Error stopping recording: {e}')
            print(f'DEBUG: Exception details:')
            traceback.print_exc()
            self._cleanup_recording()
            return None

    def _monitor_recording(self):
        """Monitor for recording completion and convert events."""
        try:
            # DEBUG: Log monitoring thread context
            current_thread = threading.current_thread()
            print(f'DEBUG: _monitor_recording() running in thread: {current_thread.name} (ID: {current_thread.ident})')
            # Keep thread alive until recording stops
            while not self._stop_event.wait(0.1):
                if not self.is_recording:
                    break

                # Check if InputCaptureManager has stopped (ESC pressed)
                if not self.input_capture.is_recording():
                    print('Recording stopped by ESC key')
                    print(f'DEBUG: ESC detected in thread: {threading.current_thread().name} (ID: {threading.current_thread().ident})')
                    self.stop_recording()
                    break

                # Process new events from InputCaptureManager
                self._process_captured_events()

        except Exception as e:
            print(f'Error in recording monitor: {e}')

    def _process_captured_events(self):
        """Process events captured by InputCaptureManager and convert to macro format."""
        if not self.current_recording:
            return

        try:
            events = self.input_capture.get_recorded_events()

            # Process new events (skip already processed ones)
            current_count = len(self.current_recording.operations)
            new_events = events[current_count:]

            for event in new_events:
                operation = self._convert_event_to_operation(event)
                if operation:
                    self.current_recording.add_operation(operation)

        except Exception as e:
            print(f'Error processing captured events: {e}')

    def _convert_event_to_operation(self, event) -> Optional[OperationBlock]:
        """Convert InputCaptureManager event to OperationBlock."""
        try:
            # Convert datetime timestamp to float
            timestamp = event.timestamp.timestamp() if hasattr(event.timestamp, 'timestamp') else event.timestamp
            
            if isinstance(event, MouseEvent):
                # Convert MouseEvent to our format
                button_mapping = {
                    'left': MouseButton.LEFT,
                    'right': MouseButton.RIGHT,
                    'middle': MouseButton.MIDDLE,
                }

                button = button_mapping.get(
                    event.button.value.lower(), MouseButton.LEFT
                )
                position = Position(x=int(event.x), y=int(event.y))
                return create_mouse_click_operation(button, position, timestamp)

            elif isinstance(event, KeyboardEvent):
                # Convert KeyboardEvent to our format
                action = 'press' if event.type == EventType.KEY_PRESS else 'release'
                key = (
                    event.key
                    if hasattr(event, 'key')
                    else str(event.char)
                    if hasattr(event, 'char')
                    else 'unknown'
                )
                return create_key_operation(key, action, [], timestamp)

        except Exception as e:
            print(f'Error converting event to operation: {e}')

        return None

    def _cleanup_recording(self):
        """Clean up recording resources."""
        self.current_recording = None
        self.is_recording = False
        self._recording_thread = None
        self._stop_event.clear()

    def get_current_recording_info(self) -> dict:
        """
        Get information about the current recording.

        Returns:
            Dictionary with recording information
        """
        if not self.current_recording:
            return {'active': False}

        return {
            'active': self.is_recording,
            'name': self.current_recording.name,
            'operation_count': self.current_recording.operation_count,
            'duration': self.current_recording.duration,
            'created_at': self.current_recording.created_at,
        }
