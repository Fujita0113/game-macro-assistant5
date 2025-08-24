import threading
from datetime import datetime
from typing import List, Optional
import pynput
from pynput import mouse, keyboard

from .events import MouseEvent, KeyboardEvent, EventType, MouseButton, InputEvent


class InputCaptureManager:
    def __init__(self):
        self._recording = False
        self._recorded_events: List[InputEvent] = []
        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._recording_lock = threading.Lock()
    
    def start_recording(self) -> None:
        """Start recording mouse and keyboard events"""
        with self._recording_lock:
            if self._recording:
                return
            
            self._recording = True
            self._recorded_events.clear()
            
            print("Recording... Press ESC to stop")
            
            # Start mouse listener
            self._mouse_listener = mouse.Listener(
                on_click=self._on_mouse_click
            )
            self._mouse_listener.start()
            
            # Start keyboard listener
            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self._keyboard_listener.start()
    
    def stop_recording(self) -> None:
        """Stop recording events"""
        with self._recording_lock:
            if not self._recording:
                return
            
            self._recording = False
            
            if self._mouse_listener:
                self._mouse_listener.stop()
                self._mouse_listener = None
            
            if self._keyboard_listener:
                self._keyboard_listener.stop()
                self._keyboard_listener = None
            
            print("Recording stopped")
    
    def get_recorded_events(self) -> List[InputEvent]:
        """Get the list of recorded events"""
        with self._recording_lock:
            return self._recorded_events.copy()
    
    def is_recording(self) -> bool:
        """Check if currently recording"""
        with self._recording_lock:
            return self._recording
    
    def _on_mouse_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        """Handle mouse click events"""
        if not self._recording or not pressed:
            return
        
        mouse_button = self._convert_mouse_button(button)
        if mouse_button:
            event = MouseEvent(
                type=EventType.MOUSE_CLICK,
                x=x,
                y=y,
                button=mouse_button,
                timestamp=datetime.now()
            )
            
            with self._recording_lock:
                self._recorded_events.append(event)
                print(f"Mouse click recorded: {button.name} at ({x}, {y})")
    
    def _on_key_press(self, key) -> None:
        """Handle key press events"""
        if not self._recording:
            return
        
        # Check for ESC key to stop recording
        try:
            if key == keyboard.Key.esc:
                self.stop_recording()
                return
        except AttributeError:
            pass
        
        key_str = self._key_to_string(key)
        char = None
        
        # Get character representation if it's a printable key
        try:
            if hasattr(key, 'char') and key.char is not None:
                char = key.char
        except AttributeError:
            pass
        
        event = KeyboardEvent(
            type=EventType.KEY_PRESS,
            key=key_str,
            timestamp=datetime.now(),
            char=char
        )
        
        with self._recording_lock:
            self._recorded_events.append(event)
            print(f"Key press recorded: {key_str}")
    
    def _on_key_release(self, key) -> None:
        """Handle key release events"""
        if not self._recording:
            return
        
        key_str = self._key_to_string(key)
        char = None
        
        # Get character representation if it's a printable key
        try:
            if hasattr(key, 'char') and key.char is not None:
                char = key.char
        except AttributeError:
            pass
        
        event = KeyboardEvent(
            type=EventType.KEY_RELEASE,
            key=key_str,
            timestamp=datetime.now(),
            char=char
        )
        
        with self._recording_lock:
            self._recorded_events.append(event)
    
    def _convert_mouse_button(self, button: mouse.Button) -> Optional[MouseButton]:
        """Convert pynput mouse button to our MouseButton enum"""
        button_map = {
            mouse.Button.left: MouseButton.LEFT,
            mouse.Button.right: MouseButton.RIGHT,
            mouse.Button.middle: MouseButton.MIDDLE
        }
        return button_map.get(button)
    
    def _key_to_string(self, key) -> str:
        """Convert pynput key to string representation"""
        try:
            # Handle special keys
            if hasattr(key, 'name'):
                return key.name
            elif hasattr(key, 'char') and key.char is not None:
                return key.char
            else:
                return str(key)
        except AttributeError:
            return str(key)