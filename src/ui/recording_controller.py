"""
Recording controller that integrates UI with capture systems.

This module coordinates between the main window UI and the input/screen
capture managers to provide unified recording control.
"""

import time
import threading
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
from .visual_editor import VisualEditor


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

        # Track processed events to prevent duplicates
        self._processed_event_timestamps = set()

        # UI callback
        self.on_recording_state_changed: Optional[Callable[[bool], None]] = None
        self.on_recording_completed: Optional[Callable[[MacroRecording], None]] = None

        # ESC termination flag
        self._esc_terminated = False

        # Visual editor
        self.visual_editor: Optional[VisualEditor] = None

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
            # Create new recording
            if recording_name is None:
                recording_name = f'Recording_{int(time.time())}'

            self.current_recording = MacroRecording(
                name=recording_name,
                created_at=time.time(),
                operations=[],
                metadata={'created_by': 'GameMacroAssistant'},
            )

            # Clear processed events from previous recordings
            self._processed_event_timestamps.clear()

            # Start capture systems
            self.input_capture.start_recording()  # InputCaptureManager uses start_recording()

            # Set recording state
            self.is_recording = True
            self._stop_event.clear()

            # Start monitoring thread for recording events
            self._recording_thread = threading.Thread(target=self._monitor_recording)
            self._recording_thread.daemon = True
            self._recording_thread.start()

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
            # Stop recording
            self.is_recording = False
            self._stop_event.set()

            # Stop capture systems
            self.input_capture.stop_recording()  # InputCaptureManager uses stop_recording()

            # Wait for monitoring thread to finish (but not if we're in the monitor thread)
            if (
                self._recording_thread
                and self._recording_thread.is_alive()
                and threading.current_thread() != self._recording_thread
            ):
                self._recording_thread.join(timeout=1.0)

            # Get completed recording
            completed_recording = self.current_recording

            # Cleanup
            self._cleanup_recording()

            # Use shared completion logic
            if completed_recording:
                self._handle_recording_completion(completed_recording)

            print(
                f'Recording stopped. Operations recorded: {completed_recording.operation_count if completed_recording else 0}'
            )
            return completed_recording

        except Exception as e:
            print(f'Error stopping recording: {e}')
            self._cleanup_recording()
            return None

    def _monitor_recording(self):
        """Monitor for recording completion and convert events."""
        try:
            # Keep thread alive until recording stops
            while not self._stop_event.wait(0.1):
                if not self.is_recording:
                    break

                # Check if InputCaptureManager has stopped (ESC pressed)
                if not self.input_capture.is_recording():
                    print('Recording stopped by ESC key')
                    # Mark as ESC terminated and stop recording flag
                    self._esc_terminated = True
                    self.is_recording = False
                    self._stop_event.set()
                    break

                # Process new events from InputCaptureManager
                self._process_captured_events()

        except Exception as e:
            print(f'Error in recording monitor: {e}')

        # If ESC terminated, handle completion using shared logic
        if self._esc_terminated and self.current_recording:
            try:
                print('ESC termination detected, finalizing recording...')
                # Get completed recording before cleanup
                completed_recording = self.current_recording

                # Use shared completion logic
                self._handle_recording_completion(completed_recording)

            except Exception as e:
                print(f'Error finalizing ESC termination: {e}')

    def _process_captured_events(self):
        """Process events captured by InputCaptureManager and convert to macro format."""
        if not self.current_recording:
            return

        try:
            events = self.input_capture.get_recorded_events()

            # Process only unprocessed events using timestamp-based deduplication
            for event in events:
                # Create unique identifier from timestamp
                event_id = event.timestamp.isoformat()

                # Skip if already processed
                if event_id in self._processed_event_timestamps:
                    continue

                # Mark as processed before attempting conversion
                self._processed_event_timestamps.add(event_id)

                # Convert and add operation
                operation = self._convert_event_to_operation(event)
                if operation:
                    self.current_recording.add_operation(operation)

        except Exception as e:
            print(f'Error processing captured events: {e}')

    def _convert_event_to_operation(self, event) -> Optional[OperationBlock]:
        """Convert InputCaptureManager event to OperationBlock."""
        try:
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

                # Convert datetime timestamp to float
                timestamp_float = (
                    event.timestamp.timestamp() if event.timestamp else time.time()
                )

                return create_mouse_click_operation(button, position, timestamp_float)

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

                # Convert datetime timestamp to float
                timestamp_float = (
                    event.timestamp.timestamp() if event.timestamp else time.time()
                )

                return create_key_operation(key, action, [], timestamp_float)

        except Exception as e:
            print(f'Error converting event to operation: {e}')
            # Fallback with current time if conversion fails
            try:
                if isinstance(event, MouseEvent):
                    button = MouseButton.LEFT
                    position = Position(x=int(event.x), y=int(event.y))
                    return create_mouse_click_operation(button, position, time.time())
                elif isinstance(event, KeyboardEvent):
                    return create_key_operation('unknown', 'press', [], time.time())
            except Exception:
                pass

        return None

    def _handle_recording_completion(self, completed_recording: MacroRecording):
        """Handle recording completion with UI callbacks and visual editor launch."""
        try:
            # Notify UI of state change
            if self.on_recording_state_changed:
                self.on_recording_state_changed(False)

            # Notify of completion
            if self.on_recording_completed:
                self.on_recording_completed(completed_recording)

            # Automatically open visual editor after recording completion
            if completed_recording.operation_count > 0:
                self.open_visual_editor(completed_recording)

        except Exception as e:
            print(f'Error in recording completion handling: {e}')

    def _cleanup_recording(self):
        """Clean up recording resources."""
        self.current_recording = None
        self.is_recording = False
        self._recording_thread = None
        self._stop_event.clear()
        self._processed_event_timestamps.clear()
        self._esc_terminated = False

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

    def open_visual_editor(self, macro_recording: MacroRecording):
        """
        Open the visual editor with the given macro recording.

        Args:
            macro_recording: The macro recording to load in the editor
        """
        try:
            # Close existing visual editor if present
            if self.visual_editor:
                try:
                    self.visual_editor.destroy()
                    # Clean up the reference to prevent widget reuse issues
                    self.visual_editor = None
                except Exception as cleanup_error:
                    print(
                        f'Warning: Error cleaning up previous visual editor: {cleanup_error}'
                    )
                    # Force clear the reference anyway
                    self.visual_editor = None

            # Always create a new visual editor instance to avoid Tkinter widget issues
            self.visual_editor = VisualEditor()

            # Load the macro into the editor
            self.visual_editor.load_macro(macro_recording)

            # Show the editor window
            self.visual_editor.show()

            print(
                f'Visual editor opened with {macro_recording.operation_count} operations'
            )

        except Exception as e:
            print(f'Error opening visual editor: {e}')
            # Reset the reference if creation failed
            self.visual_editor = None

    def close_visual_editor(self):
        """Close the visual editor if it's open."""
        if self.visual_editor:
            try:
                self.visual_editor.destroy()
                # Clean up the reference after closing
                self.visual_editor = None
                print('Visual editor closed')
            except Exception as e:
                print(f'Error closing visual editor: {e}')
                # Clear reference even if closing failed
                self.visual_editor = None
