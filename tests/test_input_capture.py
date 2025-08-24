import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from datetime import datetime

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
    def test_multiple_start_recording_calls(self, mock_keyboard_listener, mock_mouse_listener):
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
    
    @patch('src.core.input_capture.mouse.Button')
    def test_mouse_click_recording(self, mock_button):
        """Test mouse click event recording"""
        # Setup
        mock_button.left = "left"
        mock_button.left.name = "left"
        
        # Simulate mouse click
        with patch.object(self.manager, '_recording', True):
            self.manager._on_mouse_click(100, 200, mock_button.left, True)
        
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
        mock_key.esc = "esc"
        
        with patch.object(self.manager, 'stop_recording') as mock_stop:
            with patch.object(self.manager, '_recording', True):
                self.manager._on_key_press(mock_key.esc)
            
            mock_stop.assert_called_once()
    
    def test_key_to_string_conversion(self):
        """Test _key_to_string method"""
        # Test with character key
        mock_key_char = Mock()
        mock_key_char.char = 'a'
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


if __name__ == '__main__':
    unittest.main()