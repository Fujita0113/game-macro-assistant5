import threading
import logging
import json
from datetime import datetime
from typing import List, Optional
from pynput import mouse, keyboard

from .events import MouseEvent, KeyboardEvent, EventType, MouseButton, InputEvent


class ErrorCodes:
    """Unified error code definitions for input capture system"""

    CAPTURE_INIT_FAILED = 'Err-CAP-001'
    CAPTURE_RUNTIME_ERROR = 'Err-CAP-002'
    CAPTURE_PERMISSION_DENIED = 'Err-CAP-003'
    CAPTURE_RESOURCE_UNAVAILABLE = 'Err-CAP-004'


# Configure logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InputCaptureManager:
    def __init__(self):
        self._recording = False
        self._recorded_events: List[InputEvent] = []
        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._recording_lock = threading.Lock()
        self._status_thread: Optional[threading.Thread] = None
        self._stop_status_display = threading.Event()

    def start_recording(self) -> None:
        """Start recording mouse and keyboard events"""
        with self._recording_lock:
            if self._recording:
                return

            try:
                self._recording = True
                self._recorded_events.clear()
                self._stop_status_display.clear()

                logger.info('Starting input capture recording session')

                # Start mouse listener
                self._mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
                self._mouse_listener.start()

                # Start keyboard listener
                self._keyboard_listener = keyboard.Listener(
                    on_press=self._on_key_press, on_release=self._on_key_release
                )
                self._keyboard_listener.start()

                # Start status display thread
                self._status_thread = threading.Thread(
                    target=self._display_recording_status, daemon=True
                )
                self._status_thread.start()

            except PermissionError as e:
                error_msg = f'{ErrorCodes.CAPTURE_PERMISSION_DENIED}: Permission denied for input capture - {str(e)}'
                logger.error(error_msg)
                self._recording = False
                self._stop_status_display.set()
                raise RuntimeError(error_msg) from e
            except OSError as e:
                error_msg = f'{ErrorCodes.CAPTURE_RESOURCE_UNAVAILABLE}: System resources unavailable for input capture - {str(e)}'
                logger.error(error_msg)
                self._recording = False
                self._stop_status_display.set()
                raise RuntimeError(error_msg) from e
            except Exception as e:
                error_msg = f'{ErrorCodes.CAPTURE_INIT_FAILED}: Failed to initialize input capture - {str(e)}'
                logger.error(error_msg)
                self._recording = False
                self._stop_status_display.set()
                raise RuntimeError(error_msg) from e

    def stop_recording(self) -> None:
        """Stop recording events"""
        with self._recording_lock:
            if not self._recording:
                return

            self._recording = False

            # Stop status display thread
            self._stop_status_display.set()
            if self._status_thread and self._status_thread.is_alive():
                self._status_thread.join(timeout=2.0)
            self._status_thread = None

            if self._mouse_listener:
                self._mouse_listener.stop()
                self._mouse_listener = None

            if self._keyboard_listener:
                self._keyboard_listener.stop()
                self._keyboard_listener = None

            print('Recording stopped')

    def get_recorded_events(self) -> List[InputEvent]:
        """Get the list of recorded events"""
        with self._recording_lock:
            return self._recorded_events.copy()

    def is_recording(self) -> bool:
        """Check if currently recording"""
        with self._recording_lock:
            return self._recording

    def _display_recording_status(self) -> None:
        """Display 'Recording...' message every second while recording"""
        while not self._stop_status_display.wait(1.0):
            if self._recording:
                print('Recording...')
            else:
                break

    def _on_mouse_click(
        self, x: int, y: int, button: mouse.Button, pressed: bool
    ) -> None:
        """Handle mouse click events for all supported buttons (left, right, middle)"""
        if not self._recording or not pressed:
            return

        try:
            mouse_button = self._convert_mouse_button(button)
            if mouse_button:
                event = MouseEvent(
                    type=EventType.MOUSE_CLICK,
                    x=x,
                    y=y,
                    button=mouse_button,
                    timestamp=datetime.now(),
                )

                with self._recording_lock:
                    self._recorded_events.append(event)
                    print(f'Mouse click recorded: {button.name} at ({x}, {y})')
                    logger.debug(
                        f'Mouse {button.name} click recorded at coordinates ({x}, {y})'
                    )
            else:
                logger.warning(f'Unknown mouse button received: {button}')
        except Exception as e:
            error_msg = f'{ErrorCodes.CAPTURE_RUNTIME_ERROR}: Error processing mouse click - {str(e)}'
            logger.error(error_msg)
            print(f'Error recording mouse click: {str(e)}')

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
            elif key == keyboard.Key.space:
                char = ' '
        except AttributeError:
            pass

        event = KeyboardEvent(
            type=EventType.KEY_PRESS, key=key_str, timestamp=datetime.now(), char=char
        )

        with self._recording_lock:
            self._recorded_events.append(event)
            print(f'Key press recorded: {key_str}')

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
            elif key == keyboard.Key.space:
                char = ' '
        except AttributeError:
            pass

        event = KeyboardEvent(
            type=EventType.KEY_RELEASE, key=key_str, timestamp=datetime.now(), char=char
        )

        with self._recording_lock:
            self._recorded_events.append(event)

    def _convert_mouse_button(self, button: mouse.Button) -> Optional[MouseButton]:
        """Convert pynput mouse button to our MouseButton enum"""
        button_map = {
            mouse.Button.left: MouseButton.LEFT,
            mouse.Button.right: MouseButton.RIGHT,
            mouse.Button.middle: MouseButton.MIDDLE,
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

    def load_test_data(self, file_path: str) -> bool:
        """Load test data from JSON file for non-interactive testing

        Args:
            file_path: Path to JSON file containing test event data

        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        try:
            with open(file_path, 'r') as f:
                test_data = json.load(f)

            events = []

            # Process mouse events
            for mouse_event_data in test_data.get('mouse_events', []):
                try:
                    button = MouseButton(mouse_event_data['button'])
                    timestamp = datetime.fromisoformat(
                        mouse_event_data['timestamp'].replace('Z', '+00:00')
                    )

                    event = MouseEvent(
                        type=EventType.MOUSE_CLICK,
                        x=mouse_event_data['x'],
                        y=mouse_event_data['y'],
                        button=button,
                        timestamp=timestamp,
                    )
                    events.append(event)
                except (KeyError, ValueError) as e:
                    logger.warning(f'Skipping invalid mouse event: {e}')
                    continue

            # Process keyboard events
            for kb_event_data in test_data.get('keyboard_events', []):
                try:
                    timestamp = datetime.fromisoformat(
                        kb_event_data['timestamp'].replace('Z', '+00:00')
                    )

                    event = KeyboardEvent(
                        type=EventType.KEY_PRESS,
                        key=kb_event_data['key'],
                        timestamp=timestamp,
                        char=kb_event_data.get('char'),
                    )
                    events.append(event)

                    # Stop recording simulation when ESC is encountered
                    if kb_event_data['key'] == 'esc':
                        break

                except (KeyError, ValueError) as e:
                    logger.warning(f'Skipping invalid keyboard event: {e}')
                    continue

            # Sort events by timestamp
            events.sort(key=lambda x: x.timestamp)

            # Store the test events
            with self._recording_lock:
                self._recorded_events = events

            logger.info(f'Loaded {len(events)} test events from {file_path}')
            return True

        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            logger.error(f'Failed to load test data from {file_path}: {e}')
            return False
