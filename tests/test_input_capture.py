import unittest
from unittest.mock import Mock, patch
import time
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.input_capture import InputCaptureManager
from src.core.events import MouseEvent, KeyboardEvent, EventType, MouseButton


class TestInputCaptureManager(unittest.TestCase):
    def setUp(self):
        self.manager = InputCaptureManager()

    def tearDown(self):
        if self.manager.is_recording():
            self.manager.stop_recording()

    def test_initial_state(self):
        """Test initial state of InputCaptureManager"""
        self.assertFalse(self.manager.is_recording())
        self.assertEqual(len(self.manager.get_recorded_events()), 0)

    @patch('src.core.input_capture.mouse.Listener')
    @patch('src.core.input_capture.keyboard.Listener')
    def test_start_recording(self, mock_keyboard_listener, mock_mouse_listener):
        """Test start_recording method"""
        # Setup mocks
        mock_mouse_instance = Mock()
        mock_keyboard_instance = Mock()
        mock_mouse_listener.return_value = mock_mouse_instance
        mock_keyboard_listener.return_value = mock_keyboard_instance

        # Start recording
        self.manager.start_recording()

        # Verify state
        self.assertTrue(self.manager.is_recording())

        # Verify listeners are created and started
        mock_mouse_listener.assert_called_once()
        mock_keyboard_listener.assert_called_once()
        mock_mouse_instance.start.assert_called_once()
        mock_keyboard_instance.start.assert_called_once()

    @patch('src.core.input_capture.mouse.Listener')
    @patch('src.core.input_capture.keyboard.Listener')
    def test_stop_recording(self, mock_keyboard_listener, mock_mouse_listener):
        """Test stop_recording method"""
        # Setup mocks
        mock_mouse_instance = Mock()
        mock_keyboard_instance = Mock()
        mock_mouse_listener.return_value = mock_mouse_instance
        mock_keyboard_listener.return_value = mock_keyboard_instance

        # Start then stop recording
        self.manager.start_recording()
        self.manager.stop_recording()

        # Verify state
        self.assertFalse(self.manager.is_recording())

        # Verify listeners are stopped
        mock_mouse_instance.stop.assert_called_once()
        mock_keyboard_instance.stop.assert_called_once()

    def test_stop_recording_when_not_recording(self):
        """Test stop_recording when not currently recording"""
        # Should not raise any exception
        self.manager.stop_recording()
        self.assertFalse(self.manager.is_recording())

    @patch('src.core.input_capture.mouse.Listener')
    @patch('src.core.input_capture.keyboard.Listener')
    def test_multiple_start_recording_calls(
        self, mock_keyboard_listener, mock_mouse_listener
    ):
        """Test multiple calls to start_recording"""
        # Setup mocks
        mock_mouse_instance = Mock()
        mock_keyboard_instance = Mock()
        mock_mouse_listener.return_value = mock_mouse_instance
        mock_keyboard_listener.return_value = mock_keyboard_instance

        # Start recording twice
        self.manager.start_recording()
        self.manager.start_recording()

        # Should only be called once
        self.assertEqual(mock_mouse_listener.call_count, 1)
        self.assertEqual(mock_keyboard_listener.call_count, 1)
        self.assertTrue(self.manager.is_recording())

    def test_mouse_click_recording(self):
        """Test mouse click event recording"""
        from pynput import mouse

        # Simulate mouse click
        with patch.object(self.manager, '_recording', True):
            self.manager._on_mouse_click(100, 200, mouse.Button.left, True)

        # Verify event was recorded
        events = self.manager.get_recorded_events()
        self.assertEqual(len(events), 1)

        event = events[0]
        self.assertIsInstance(event, MouseEvent)
        self.assertEqual(event.x, 100)
        self.assertEqual(event.y, 200)
        self.assertEqual(event.type, EventType.MOUSE_CLICK)

    def test_mouse_click_not_recording(self):
        """Test mouse click when not recording"""
        from pynput import mouse

        # Simulate mouse click when not recording
        self.manager._on_mouse_click(100, 200, mouse.Button.left, True)

        # Verify no events were recorded
        events = self.manager.get_recorded_events()
        self.assertEqual(len(events), 0)

    def test_all_mouse_buttons_recording(self):
        """Test recording of left, right, and middle mouse buttons"""
        from pynput import mouse

        test_cases = [
            (mouse.Button.left, MouseButton.LEFT),
            (mouse.Button.right, MouseButton.RIGHT),
            (mouse.Button.middle, MouseButton.MIDDLE),
        ]

        for pynput_button, expected_button in test_cases:
            with self.subTest(button=pynput_button.name):
                # Clear events for each test
                self.manager._recorded_events.clear()

                # Simulate mouse click
                with patch.object(self.manager, '_recording', True):
                    self.manager._on_mouse_click(150, 250, pynput_button, True)

                # Verify event was recorded
                events = self.manager.get_recorded_events()
                self.assertEqual(len(events), 1)

                event = events[0]
                self.assertIsInstance(event, MouseEvent)
                self.assertEqual(event.x, 150)
                self.assertEqual(event.y, 250)
                self.assertEqual(event.button, expected_button)
                self.assertEqual(event.type, EventType.MOUSE_CLICK)

    def test_mouse_click_error_handling(self):
        """Test error handling in mouse click processing"""

        # Test with invalid button (should not crash)
        with patch.object(self.manager, '_recording', True):
            # Create a mock button that's not in the conversion map
            invalid_button = Mock()
            invalid_button.name = 'invalid'

            # This should not raise an exception
            self.manager._on_mouse_click(100, 200, invalid_button, True)

            # Should have no events recorded
            events = self.manager.get_recorded_events()
            self.assertEqual(len(events), 0)

    def test_key_press_recording(self):
        """Test keyboard key press event recording"""
        # Create a mock key with char attribute
        mock_key = Mock()
        mock_key.char = 'a'

        # Simulate key press
        with patch.object(self.manager, '_recording', True):
            self.manager._on_key_press(mock_key)

        # Verify event was recorded
        events = self.manager.get_recorded_events()
        self.assertEqual(len(events), 1)

        event = events[0]
        self.assertIsInstance(event, KeyboardEvent)
        self.assertEqual(event.char, 'a')
        self.assertEqual(event.type, EventType.KEY_PRESS)

    @patch('src.core.input_capture.keyboard.Key')
    def test_esc_key_stops_recording(self, mock_key):
        """Test that ESC key stops recording"""
        mock_key.esc = 'esc'

        with patch.object(self.manager, 'stop_recording') as mock_stop:
            with patch.object(self.manager, '_recording', True):
                self.manager._on_key_press(mock_key.esc)

            mock_stop.assert_called_once()

    def test_key_to_string_conversion(self):
        """Test _key_to_string method"""
        # Test with character key
        mock_key_char = Mock()
        mock_key_char.char = 'a'
        # Remove name attribute to test char path
        delattr(mock_key_char, 'name')
        result = self.manager._key_to_string(mock_key_char)
        self.assertEqual(result, 'a')

        # Test with special key
        mock_key_special = Mock()
        mock_key_special.name = 'space'
        mock_key_special.char = None
        result = self.manager._key_to_string(mock_key_special)
        self.assertEqual(result, 'space')

    def test_convert_mouse_button(self):
        """Test _convert_mouse_button method"""
        from pynput import mouse

        # Test left button conversion
        result = self.manager._convert_mouse_button(mouse.Button.left)
        self.assertEqual(result, MouseButton.LEFT)

        # Test right button conversion
        result = self.manager._convert_mouse_button(mouse.Button.right)
        self.assertEqual(result, MouseButton.RIGHT)

        # Test middle button conversion
        result = self.manager._convert_mouse_button(mouse.Button.middle)
        self.assertEqual(result, MouseButton.MIDDLE)

    @patch('src.core.input_capture.mouse.Listener')
    @patch('src.core.input_capture.keyboard.Listener')
    def test_start_recording_permission_error(
        self, mock_keyboard_listener, mock_mouse_listener
    ):
        """Test start_recording with permission error"""
        # Setup mock to raise PermissionError
        mock_mouse_listener.side_effect = PermissionError('Access denied')

        # Attempt to start recording
        with self.assertRaises(RuntimeError) as cm:
            self.manager.start_recording()

        # Verify error message contains correct error code
        self.assertIn('Err-CAP-003', str(cm.exception))
        self.assertFalse(self.manager.is_recording())

    @patch('src.core.input_capture.mouse.Listener')
    @patch('src.core.input_capture.keyboard.Listener')
    def test_start_recording_os_error(
        self, mock_keyboard_listener, mock_mouse_listener
    ):
        """Test start_recording with OS error"""
        # Setup mock to raise OSError
        mock_mouse_listener.side_effect = OSError('Resource unavailable')

        # Attempt to start recording
        with self.assertRaises(RuntimeError) as cm:
            self.manager.start_recording()

        # Verify error message contains correct error code
        self.assertIn('Err-CAP-004', str(cm.exception))
        self.assertFalse(self.manager.is_recording())

    @patch('src.core.input_capture.mouse.Listener')
    @patch('src.core.input_capture.keyboard.Listener')
    def test_start_recording_generic_error(
        self, mock_keyboard_listener, mock_mouse_listener
    ):
        """Test start_recording with generic error"""
        # Setup mock to raise generic Exception
        mock_mouse_listener.side_effect = Exception('Unexpected error')

        # Attempt to start recording
        with self.assertRaises(RuntimeError) as cm:
            self.manager.start_recording()

        # Verify error message contains correct error code
        self.assertIn('Err-CAP-001', str(cm.exception))
        self.assertFalse(self.manager.is_recording())

    def test_error_codes_format(self):
        """Test that error codes follow the correct format"""
        from src.core.input_capture import ErrorCodes

        error_codes = [
            ErrorCodes.CAPTURE_INIT_FAILED,
            ErrorCodes.CAPTURE_RUNTIME_ERROR,
            ErrorCodes.CAPTURE_PERMISSION_DENIED,
            ErrorCodes.CAPTURE_RESOURCE_UNAVAILABLE,
        ]

        for code in error_codes:
            with self.subTest(code=code):
                # Verify format: Err-CAP-XXX
                self.assertTrue(code.startswith('Err-CAP-'))
                self.assertEqual(len(code), 11)  # "Err-CAP-XXX" is 11 characters
                self.assertTrue(
                    code.endswith('001')
                    or code.endswith('002')
                    or code.endswith('003')
                    or code.endswith('004')
                )

    def test_get_recorded_events_returns_copy(self):
        """Test that get_recorded_events returns a copy of the events list"""
        # Add a mock event
        with patch.object(self.manager, '_recording', True):
            mock_key = Mock()
            mock_key.char = 'a'
            self.manager._on_key_press(mock_key)

        # Get events and modify the returned list
        events = self.manager.get_recorded_events()
        original_length = len(events)
        events.clear()

        # Verify original list is unchanged
        events_again = self.manager.get_recorded_events()
        self.assertEqual(len(events_again), original_length)

    @patch('src.core.input_capture.mouse.Listener')
    @patch('src.core.input_capture.keyboard.Listener')
    @patch('builtins.print')
    def test_continuous_recording_display(
        self, mock_print, mock_keyboard_listener, mock_mouse_listener
    ):
        """Test that 'Recording...' is displayed continuously every second during recording"""

        # Setup mocks
        mock_mouse_instance = Mock()
        mock_keyboard_instance = Mock()
        mock_mouse_listener.return_value = mock_mouse_instance
        mock_keyboard_listener.return_value = mock_keyboard_instance

        # Start recording
        self.manager.start_recording()

        # Wait for multiple status display cycles
        time.sleep(2.5)

        # Stop recording
        self.manager.stop_recording()

        # Verify 'Recording...' was printed multiple times (at least 2 times in 2.5 seconds)
        recording_calls = [
            call for call in mock_print.call_args_list if 'Recording...' in str(call)
        ]
        self.assertGreaterEqual(
            len(recording_calls),
            2,
            "Should print 'Recording...' at least 2 times during 2.5 second recording",
        )

        # Verify final "Recording stopped" message
        stop_calls = [
            call
            for call in mock_print.call_args_list
            if 'Recording stopped' in str(call)
        ]
        self.assertEqual(
            len(stop_calls), 1, "Should print 'Recording stopped' exactly once"
        )


if __name__ == '__main__':
    unittest.main()
