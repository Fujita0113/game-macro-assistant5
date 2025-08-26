import os
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image
import tempfile
import shutil

from src.core.screen_capture import ScreenCaptureManager


class TestScreenCaptureManager(unittest.TestCase):
    def setUp(self):
        self.capture_manager = ScreenCaptureManager()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('src.core.screen_capture.ImageGrab.grab')
    def test_native_capture_success(self, mock_grab):
        mock_image = MagicMock(spec=Image.Image)
        mock_grab.return_value = mock_image

        result = self.capture_manager._native_capture()

        self.assertEqual(result, mock_image)
        mock_grab.assert_called_once()

    @patch('src.core.screen_capture.ImageGrab.grab')
    def test_native_capture_failure(self, mock_grab):
        mock_grab.side_effect = Exception('Native capture failed')

        result = self.capture_manager._native_capture()

        self.assertIsNone(result)

    @patch('src.core.screen_capture.log_error')
    @patch('src.core.screen_capture.ImageGrab.grab')
    def test_capture_screen_with_fallback(self, mock_grab, mock_log_error):
        mock_grab.side_effect = Exception('Native failed')

        with patch.object(
            self.capture_manager, '_gdi_capture_with_watermark'
        ) as mock_gdi:
            mock_fallback_image = MagicMock(spec=Image.Image)
            mock_gdi.return_value = mock_fallback_image

            result = self.capture_manager.capture_screen()

            self.assertEqual(result, mock_fallback_image)
            mock_log_error.assert_called_with(
                'Err-CAP', 'Native screen capture failed, using GDI fallback'
            )

    def test_add_watermark(self):
        test_image = Image.new('RGB', (100, 100), color='red')

        result = self.capture_manager.add_watermark(test_image)

        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.size, test_image.size)
        self.assertNotEqual(result.tobytes(), test_image.tobytes())

    @patch('src.core.screen_capture.ImageGrab.grab')
    def test_capture_region(self, mock_grab):
        mock_image = MagicMock(spec=Image.Image)
        mock_grab.return_value = mock_image

        result = self.capture_manager.capture_region(10, 10, 100, 100)

        self.assertEqual(result, mock_image)
        mock_grab.assert_called_with((10, 10, 110, 110))

    @patch('src.core.screen_capture.ImageGrab.grab')
    def test_capture_screen_save_to_file(self, mock_grab):
        mock_image = MagicMock(spec=Image.Image)
        mock_grab.return_value = mock_image

        save_path = os.path.join(self.temp_dir, 'test_screenshot.png')

        result = self.capture_manager.capture_screen(save_path)

        self.assertEqual(result, mock_image)
        mock_image.save.assert_called_with(save_path, 'PNG')

    @patch('src.core.screen_capture.log_error')
    @patch('src.core.screen_capture.ImageGrab.grab')
    def test_capture_screen_complete_failure(self, mock_grab, mock_log_error):
        mock_grab.side_effect = Exception('Complete failure')

        with patch.object(
            self.capture_manager, '_gdi_capture_with_watermark', return_value=None
        ):
            result = self.capture_manager.capture_screen()

            self.assertIsNone(result)
            self.assertTrue(mock_log_error.called)

    def test_watermark_text_configuration(self):
        self.assertEqual(self.capture_manager.fallback_watermark_text, 'CaptureLimited')

    @patch('src.core.screen_capture.log_error')
    def test_add_watermark_error_handling(self, mock_log_error):
        test_image = MagicMock(spec=Image.Image)
        test_image.copy.side_effect = Exception('Watermark error')

        result = self.capture_manager.add_watermark(test_image)

        self.assertEqual(result, test_image)
        mock_log_error.assert_called()


if __name__ == '__main__':
    unittest.main()
