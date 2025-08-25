from typing import Optional, Callable
from datetime import datetime
import os

from .screen_capture import ScreenCaptureManager
from ..utils.logging import log_info, log_error


class ScreenCaptureEventHandler:
    def __init__(self, capture_manager: Optional[ScreenCaptureManager] = None):
        self.capture_manager = capture_manager or ScreenCaptureManager()
        self.screenshot_dir = 'screenshots'
        self._ensure_screenshot_directory()

        # Callback for when screenshot is taken
        self.on_screenshot_taken: Optional[Callable[[str], None]] = None

    def _ensure_screenshot_directory(self):
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)

    def handle_input_event(self, event_type: str, event_data: dict) -> Optional[str]:
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f'capture_{event_type}_{timestamp}.png'
            save_path = os.path.join(self.screenshot_dir, filename)

            screenshot = self.capture_manager.capture_screen(save_path)

            if screenshot:
                log_info(f'Screenshot captured for {event_type} event: {filename}')

                if self.on_screenshot_taken:
                    self.on_screenshot_taken(save_path)

                return save_path
            else:
                log_error(
                    'Err-CAP', f'Failed to capture screenshot for {event_type} event'
                )
                return None

        except Exception as e:
            log_error('Err-CAP', f'Screenshot event handling failed: {str(e)}')
            return None

    def capture_on_mouse_click(self, x: int, y: int, button: str) -> Optional[str]:
        event_data = {'x': x, 'y': y, 'button': button}
        return self.handle_input_event('mouse_click', event_data)

    def capture_on_key_press(self, key: str) -> Optional[str]:
        event_data = {'key': key}
        return self.handle_input_event('key_press', event_data)

    def capture_manual(self) -> Optional[str]:
        return self.handle_input_event('manual', {})

    def set_screenshot_directory(self, directory: str):
        self.screenshot_dir = directory
        self._ensure_screenshot_directory()

    def set_screenshot_callback(self, callback: Callable[[str], None]):
        self.on_screenshot_taken = callback
