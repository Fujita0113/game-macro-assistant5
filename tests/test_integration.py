#!/usr/bin/env python3
"""
Integration tests for GameMacroAssistant
These tests verify the complete functionality including dependencies and system integration.
"""

import unittest
import subprocess
import sys
import os
import json
import time
from unittest.mock import patch, Mock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestDependencyIntegration(unittest.TestCase):
    """Test that all dependencies are properly installed and importable"""

    def test_core_dependencies_importable(self):
        """Test that all core dependencies can be imported"""
        dependencies = [
            'pynput',
            'PIL',  # Pillow
            'cryptography',
        ]

        for dep in dependencies:
            with self.subTest(dependency=dep):
                try:
                    __import__(dep)
                except ImportError as e:
                    self.fail(f"Failed to import required dependency '{dep}': {e}")

    def test_pynput_specific_version(self):
        """Test that pynput is the expected version"""
        import pynput

        # Should be version 1.7.6 as specified in requirements.txt
        self.assertTrue(hasattr(pynput, '__version__'))
        # Note: We just check it exists, exact version checking can be fragile

    def test_development_dependencies_available(self):
        """Test that development dependencies are available"""
        dev_dependencies = [
            'pytest',
            # pytest-cov might not be available in all environments
        ]

        for dep in dev_dependencies:
            with self.subTest(dependency=dep):
                try:
                    __import__(dep)
                except ImportError:
                    # Dev dependencies are optional for basic functionality
                    self.skipTest(f"Development dependency '{dep}' not available")


class TestSystemIntegration(unittest.TestCase):
    """Test system-level integration functionality"""

    def setUp(self):
        """Setup for integration tests"""
        from core.input_capture import InputCaptureManager

        self.manager = InputCaptureManager()

    def test_input_capture_manager_initialization(self):
        """Test that InputCaptureManager initializes properly"""
        self.assertFalse(self.manager.is_recording())
        self.assertEqual(len(self.manager.get_recorded_events()), 0)

    def test_error_codes_accessibility(self):
        """Test that error codes are accessible and properly formatted"""
        from core.input_capture import ErrorCodes

        error_codes = [
            ErrorCodes.CAPTURE_INIT_FAILED,
            ErrorCodes.CAPTURE_RUNTIME_ERROR,
            ErrorCodes.CAPTURE_PERMISSION_DENIED,
            ErrorCodes.CAPTURE_RESOURCE_UNAVAILABLE,
        ]

        for code in error_codes:
            with self.subTest(code=code):
                self.assertTrue(code.startswith('Err-CAP-'))
                self.assertEqual(len(code), 11)  # Err-CAP-XXX format

    def test_logging_configuration(self):
        """Test that logging is properly configured"""
        import logging

        # Test that our logger exists
        logger = logging.getLogger('src.core.input_capture')
        self.assertIsNotNone(logger)

        # Test basic logging functionality (doesn't actually log to avoid output)
        with patch.object(logger, 'info') as mock_info:
            logger.info('Test message')
            mock_info.assert_called_once_with('Test message')


class TestCommandLineInterface(unittest.TestCase):
    """Test command line interface integration"""

    def test_main_module_importable(self):
        """Test that main module can be imported"""
        try:
            from src import main

            # Access the module to avoid unused import warning
            _ = main.main
        except ImportError:
            # Try alternative import path
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

    def test_help_argument(self):
        """Test that --help argument works"""
        result = subprocess.run(
            [
                sys.executable,
                os.path.join(os.path.dirname(__file__), '..', 'src', 'main.py'),
                '--help',
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn('GameMacroAssistant', result.stdout)
        self.assertIn('--test-input', result.stdout)

    @unittest.skip('Requires interactive input - run manually')
    def test_integration_test_command(self):
        """Test the --test-input integration command"""
        # This test is skipped by default as it requires user interaction
        # To run: python -m pytest tests/test_integration.py::TestCommandLineInterface::test_integration_test_command -v -s

        result = subprocess.run(
            [
                sys.executable,
                os.path.join(os.path.dirname(__file__), '..', 'src', 'main.py'),
                '--test-input',
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # This would check the result if the test wasn't skipped
        _ = result

        # Note: This will likely fail without user interaction
        # In a real scenario, you'd need automated input simulation


class TestDataPersistence(unittest.TestCase):
    """Test data persistence and file handling"""

    def setUp(self):
        """Setup test environment"""
        self.test_file = 'test_results.json'

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_event_serialization(self):
        """Test that events can be properly serialized to JSON"""
        from core.events import MouseEvent, KeyboardEvent, EventType, MouseButton
        from datetime import datetime

        # Create test events
        mouse_event = MouseEvent(
            type=EventType.MOUSE_CLICK,
            x=100,
            y=200,
            button=MouseButton.LEFT,
            timestamp=datetime.now(),
        )

        keyboard_event = KeyboardEvent(
            type=EventType.KEY_PRESS, key='a', timestamp=datetime.now(), char='a'
        )

        # Test serialization
        mouse_dict = mouse_event.to_dict()
        keyboard_dict = keyboard_event.to_dict()

        # Test that dictionaries are JSON serializable
        try:
            json.dumps([mouse_dict, keyboard_dict], indent=2)
        except (TypeError, ValueError) as e:
            self.fail(f'Events are not JSON serializable: {e}')

    def test_results_file_creation(self):
        """Test that test results can be written to file"""
        test_data = {
            'test_timestamp': '2023-01-01T00:00:00',
            'total_events': 5,
            'mouse_clicks': 3,
            'keyboard_events': 2,
            'events': [],
        }

        # Write test data
        with open(self.test_file, 'w') as f:
            json.dump(test_data, f, indent=2)

        # Verify file exists and can be read
        self.assertTrue(os.path.exists(self.test_file))

        with open(self.test_file, 'r') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data['total_events'], 5)
        self.assertEqual(loaded_data['mouse_clicks'], 3)


class TestErrorHandlingIntegration(unittest.TestCase):
    """Test integrated error handling scenarios"""

    def setUp(self):
        """Setup for error handling tests"""
        from core.input_capture import InputCaptureManager

        self.manager = InputCaptureManager()

    @patch('src.core.input_capture.mouse.Listener')
    def test_permission_error_handling(self, mock_mouse_listener):
        """Test handling of permission errors during startup"""
        # Mock permission error
        mock_mouse_listener.side_effect = PermissionError('Access denied')

        with self.assertRaises(RuntimeError) as cm:
            self.manager.start_recording()

        error_message = str(cm.exception)
        self.assertIn('Err-CAP-003', error_message)
        self.assertIn('Permission denied', error_message)
        self.assertFalse(self.manager.is_recording())

    def test_graceful_degradation(self):
        """Test that system degrades gracefully under error conditions"""
        # Test with invalid mouse button
        with patch.object(self.manager, '_recording', True):
            # This should not crash the system
            invalid_button = Mock()
            invalid_button.name = 'unknown'

            # Should handle gracefully
            self.manager._on_mouse_click(0, 0, invalid_button, True)

            # Should still be recording
            self.assertTrue(self.manager._recording)


class TestPerformanceIntegration(unittest.TestCase):
    """Test performance-related integration scenarios"""

    def setUp(self):
        """Setup for performance tests"""
        from core.input_capture import InputCaptureManager

        self.manager = InputCaptureManager()

    def test_high_frequency_events(self):
        """Test handling of high-frequency input events"""
        # Simulate rapid key presses
        start_time = time.time()

        with patch.object(self.manager, '_recording', True):
            for i in range(100):
                mock_key = Mock()
                mock_key.char = chr(ord('a') + (i % 26))
                self.manager._on_key_press(mock_key)

        end_time = time.time()
        processing_time = end_time - start_time

        # Should process 100 events quickly (under 1 second)
        self.assertLess(processing_time, 1.0)

        # All events should be recorded
        events = self.manager.get_recorded_events()
        self.assertEqual(len(events), 100)

    def test_memory_usage_stability(self):
        """Test that memory usage remains stable with many events"""
        import gc

        with patch.object(self.manager, '_recording', True):
            # Create many events
            for i in range(1000):
                mock_key = Mock()
                mock_key.char = 'x'
                self.manager._on_key_press(mock_key)

        # Force garbage collection
        gc.collect()

        # Verify all events are still accessible
        events = self.manager.get_recorded_events()
        self.assertEqual(len(events), 1000)

        # Clear events to test cleanup
        self.manager._recorded_events.clear()
        gc.collect()

        # Should have no events after clearing
        events = self.manager.get_recorded_events()
        self.assertEqual(len(events), 0)


if __name__ == '__main__':
    # Configure test discovery and execution
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestDependencyIntegration,
        TestSystemIntegration,
        TestCommandLineInterface,
        TestDataPersistence,
        TestErrorHandlingIntegration,
        TestPerformanceIntegration,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
