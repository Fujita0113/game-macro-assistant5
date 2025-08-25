"""
Recording controller that integrates UI with capture systems.

This module coordinates between the main window UI and the input/screen
capture managers to provide unified recording control.
"""

import time
import uuid
import threading
from typing import Optional, Callable
import keyboard
import mouse

from core.macro_data import (
    MacroRecording, OperationBlock, MouseButton, Position,
    create_mouse_click_operation, create_key_operation
)


class MockInputCaptureManager:
    """
    Placeholder implementation for InputCaptureManager.
    
    This will be replaced with the actual implementation from Issue #1.
    """
    
    def __init__(self):
        self.is_capturing = False
        self.on_mouse_event: Optional[Callable] = None
        self.on_key_event: Optional[Callable] = None
        self._hooks = []
    
    def start_capture(self):
        """Start capturing input events."""
        if self.is_capturing:
            return
        
        self.is_capturing = True
        
        # Hook mouse events
        mouse.on_click(self._on_mouse_click)
        
        # Hook keyboard events (excluding ESC)
        keyboard.on_press(self._on_key_press)
        
        print("Input capture started (Mock implementation)")
    
    def stop_capture(self):
        """Stop capturing input events."""
        if not self.is_capturing:
            return
        
        self.is_capturing = False
        
        # Unhook all events
        try:
            mouse.unhook_all()
            keyboard.unhook_all()
        except:
            pass
        
        print("Input capture stopped")
    
    def _on_mouse_click(self):
        """Handle mouse click events."""
        if not self.is_capturing or not self.on_mouse_event:
            return
        
        try:
            pos = mouse.get_position()
            button = MouseButton.LEFT  # Simplified for mock
            position = Position(x=pos[0], y=pos[1])
            self.on_mouse_event(button, position)
        except Exception as e:
            print(f"Error handling mouse click: {e}")
    
    def _on_key_press(self, event):
        """Handle key press events."""
        if not self.is_capturing or not self.on_key_event:
            return
        
        # Skip ESC key as it's used for stopping recording
        if event.name == 'esc':
            return
        
        try:
            self.on_key_event(event.name, "press")
        except Exception as e:
            print(f"Error handling key press: {e}")


class MockScreenCaptureManager:
    """
    Placeholder implementation for ScreenCaptureManager.
    
    This will be replaced with the actual implementation from Issue #2.
    """
    
    def __init__(self):
        self.is_capturing = False
    
    def start_capture(self):
        """Start screen capture."""
        self.is_capturing = True
        print("Screen capture started (Mock implementation)")
    
    def stop_capture(self):
        """Stop screen capture."""
        self.is_capturing = False
        print("Screen capture stopped")
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> bytes:
        """Capture a screen region."""
        # Return mock image data
        return b"mock_screenshot_data"


class RecordingController:
    """Controls the recording process and coordinates between UI and capture systems."""
    
    def __init__(self):
        """Initialize the recording controller."""
        self.input_capture = MockInputCaptureManager()
        self.screen_capture = MockScreenCaptureManager()
        
        self.current_recording: Optional[MacroRecording] = None
        self.is_recording = False
        self._recording_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Set up event handlers
        self.input_capture.on_mouse_event = self._on_mouse_event
        self.input_capture.on_key_event = self._on_key_event
        
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
            print("Recording already in progress")
            return False
        
        try:
            # Create new recording
            if recording_name is None:
                recording_name = f"Recording_{int(time.time())}"
            
            self.current_recording = MacroRecording(
                name=recording_name,
                created_at=time.time(),
                operations=[],
                metadata={"created_by": "GameMacroAssistant"}
            )
            
            # Start capture systems
            self.input_capture.start_capture()
            self.screen_capture.start_capture()
            
            # Set recording state
            self.is_recording = True
            self._stop_event.clear()
            
            # Start monitoring thread for ESC key
            self._recording_thread = threading.Thread(target=self._monitor_recording)
            self._recording_thread.daemon = True
            self._recording_thread.start()
            
            # Notify UI
            if self.on_recording_state_changed:
                self.on_recording_state_changed(True)
            
            print(f"Recording started: {recording_name}")
            return True
            
        except Exception as e:
            print(f"Error starting recording: {e}")
            self._cleanup_recording()
            return False
    
    def stop_recording(self) -> Optional[MacroRecording]:
        """
        Stop the current recording session.
        
        Returns:
            The completed MacroRecording if successful, None otherwise
        """
        if not self.is_recording:
            print("No recording in progress")
            return None
        
        try:
            # Stop recording
            self.is_recording = False
            self._stop_event.set()
            
            # Stop capture systems
            self.input_capture.stop_capture()
            self.screen_capture.stop_capture()
            
            # Wait for monitoring thread to finish
            if self._recording_thread and self._recording_thread.is_alive():
                self._recording_thread.join(timeout=1.0)
            
            # Get completed recording
            completed_recording = self.current_recording
            
            # Cleanup
            self._cleanup_recording()
            
            # Notify UI
            if self.on_recording_state_changed:
                self.on_recording_state_changed(False)
            
            if completed_recording and self.on_recording_completed:
                self.on_recording_completed(completed_recording)
            
            print(f"Recording stopped. Operations recorded: {completed_recording.operation_count if completed_recording else 0}")
            return completed_recording
            
        except Exception as e:
            print(f"Error stopping recording: {e}")
            self._cleanup_recording()
            return None
    
    def _monitor_recording(self):
        """Monitor for ESC key to stop recording."""
        try:
            # Set up ESC key hook
            keyboard.add_hotkey('esc', self._on_esc_pressed, suppress=False)
            
            # Keep thread alive until recording stops
            while not self._stop_event.wait(0.1):
                if not self.is_recording:
                    break
            
        except Exception as e:
            print(f"Error in recording monitor: {e}")
        finally:
            try:
                keyboard.remove_hotkey('esc')
            except:
                pass
    
    def _on_esc_pressed(self):
        """Handle ESC key press to stop recording."""
        if self.is_recording:
            print("ESC pressed - stopping recording")
            self.stop_recording()
    
    def _on_mouse_event(self, button: MouseButton, position: Position):
        """Handle mouse events during recording."""
        if not self.is_recording or not self.current_recording:
            return
        
        try:
            operation = create_mouse_click_operation(button, position)
            self.current_recording.add_operation(operation)
            print(f"Recorded mouse click: {button.value} at ({position.x}, {position.y})")
        except Exception as e:
            print(f"Error recording mouse event: {e}")
    
    def _on_key_event(self, key: str, action: str):
        """Handle keyboard events during recording."""
        if not self.is_recording or not self.current_recording:
            return
        
        try:
            operation = create_key_operation(key, action)
            self.current_recording.add_operation(operation)
            print(f"Recorded key {action}: {key}")
        except Exception as e:
            print(f"Error recording key event: {e}")
    
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
            return {"active": False}
        
        return {
            "active": self.is_recording,
            "name": self.current_recording.name,
            "operation_count": self.current_recording.operation_count,
            "duration": self.current_recording.duration,
            "created_at": self.current_recording.created_at
        }