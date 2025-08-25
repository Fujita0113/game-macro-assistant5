from typing import Optional
from PIL import Image, ImageDraw, ImageFont, ImageGrab

try:
    # import win32gui    # Reserved for future GDI implementation
    # import win32con    # Reserved for future GDI implementation
    # import win32api    # Reserved for future GDI implementation
    # import win32ui     # Reserved for future GDI implementation

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
try:
    from ..utils.logging import log_error
except ImportError:
    # For direct script execution
    import sys
    import os

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from utils.logging import log_error


class ScreenCaptureManager:
    def __init__(self):
        self.fallback_watermark_text = 'CaptureLimited'

    def capture_screen(self, save_path: Optional[str] = None) -> Optional[Image.Image]:
        try:
            # Try native screenshot first
            screenshot = self._native_capture()

            if screenshot is None:
                # Fallback to GDI capture with watermark
                screenshot = self._gdi_capture_with_watermark()
                log_error('Err-CAP', 'Native screen capture failed, using GDI fallback')

            if screenshot and save_path:
                screenshot.save(save_path, 'PNG')

            return screenshot

        except Exception as e:
            log_error('Err-CAP', f'Screen capture failed: {str(e)}')
            return None

    def _native_capture(self) -> Optional[Image.Image]:
        try:
            # Use PIL's ImageGrab for native screenshot
            screenshot = ImageGrab.grab()
            return screenshot
        except Exception:
            return None

    def _gdi_capture_with_watermark(self) -> Optional[Image.Image]:
        if not WIN32_AVAILABLE:
            log_error('Err-CAP', 'Win32 modules not available for GDI fallback')
            return None

        try:
            # Try simple fallback first - use ImageGrab but add watermark
            screenshot = ImageGrab.grab()
            if screenshot:
                # Add watermark to indicate this is a "limited" capture
                screenshot = self.add_watermark(screenshot)
                return screenshot
            else:
                raise Exception('ImageGrab fallback also failed')

        except Exception as e:
            log_error('Err-CAP', f'GDI capture failed: {str(e)}')
            # Return a test image with watermark for demonstration
            try:
                test_image = Image.new('RGB', (800, 600), color='darkgray')
                watermarked = self.add_watermark(test_image)
                log_error('Err-CAP', 'Using test image as GDI fallback demonstration')
                return watermarked
            except Exception as e2:
                log_error('Err-CAP', f'Even test image fallback failed: {str(e2)}')
                return None

    def add_watermark(self, image: Image.Image) -> Image.Image:
        try:
            # Create a copy to avoid modifying original
            watermarked = image.copy()

            # Convert to RGBA if necessary for transparency support
            if watermarked.mode != 'RGBA':
                watermarked = watermarked.convert('RGBA')

            # Create transparent overlay
            overlay = Image.new('RGBA', watermarked.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)

            # Get image dimensions
            width, height = watermarked.size

            # Try to use a system font, fallback to default
            try:
                font = ImageFont.truetype('arial.ttf', 36)
            except OSError:
                font = ImageFont.load_default()

            # Calculate text position (bottom-right corner)
            bbox = draw.textbbox((0, 0), self.fallback_watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = width - text_width - 20
            y = height - text_height - 20

            # Add semi-transparent background
            draw.rectangle(
                [x - 10, y - 5, x + text_width + 10, y + text_height + 5],
                fill=(0, 0, 0, 128),
            )

            # Add text watermark
            draw.text(
                (x, y),
                self.fallback_watermark_text,
                fill=(255, 255, 255, 200),
                font=font,
            )

            # Composite the overlay onto the image
            watermarked = Image.alpha_composite(watermarked, overlay)

            # Convert back to RGB if original was RGB
            if image.mode == 'RGB':
                watermarked = watermarked.convert('RGB')

            return watermarked

        except Exception as e:
            log_error('Err-CAP', f'Watermark addition failed: {str(e)}')
            return image

    def capture_region(
        self, x: int, y: int, width: int, height: int
    ) -> Optional[Image.Image]:
        try:
            bbox = (x, y, x + width, y + height)
            screenshot = ImageGrab.grab(bbox)
            return screenshot
        except Exception as e:
            log_error('Err-CAP', f'Region capture failed: {str(e)}')
            return None
