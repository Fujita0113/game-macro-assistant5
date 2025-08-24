import os
import time
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageGrab
import win32gui
import win32con
import win32api
from ..utils.logging import log_error


class ScreenCaptureManager:
    def __init__(self):
        self.fallback_watermark_text = "CaptureLimited"
    
    def capture_screen(self, save_path: Optional[str] = None) -> Optional[Image.Image]:
        try:
            # Try native screenshot first
            screenshot = self._native_capture()
            
            if screenshot is None:
                # Fallback to GDI capture with watermark
                screenshot = self._gdi_capture_with_watermark()
                log_error("Err-CAP", "Native screen capture failed, using GDI fallback")
            
            if screenshot and save_path:
                screenshot.save(save_path, 'PNG')
            
            return screenshot
            
        except Exception as e:
            log_error("Err-CAP", f"Screen capture failed: {str(e)}")
            return None
    
    def _native_capture(self) -> Optional[Image.Image]:
        try:
            # Use PIL's ImageGrab for native screenshot
            screenshot = ImageGrab.grab()
            return screenshot
        except Exception:
            return None
    
    def _gdi_capture_with_watermark(self) -> Optional[Image.Image]:
        try:
            # Fallback using GDI methods
            hwnd = win32gui.GetDesktopWindow()
            
            # Get screen dimensions
            width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            
            # Create device contexts
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32gui.CreateCompatibleDC(hwndDC)
            
            # Create bitmap
            saveBitMap = win32gui.CreateCompatibleBitmap(hwndDC, width, height)
            win32gui.SelectObject(mfcDC, saveBitMap)
            
            # Copy screen to bitmap
            win32gui.BitBlt(mfcDC, 0, 0, width, height, hwndDC, 0, 0, win32con.SRCCOPY)
            
            # Convert to PIL Image
            bmpinfo = win32gui.GetObject(saveBitMap)
            bmpstr = win32gui.GetBitmapBits(saveBitMap, bmpinfo.bmWidthBytes * bmpinfo.bmHeight)
            
            screenshot = Image.frombuffer(
                'RGB',
                (bmpinfo.bmWidth, bmpinfo.bmHeight),
                bmpstr, 'raw', 'BGRX', 0, 1
            )
            
            # Clean up
            win32gui.DeleteDC(hwndDC)
            win32gui.DeleteDC(mfcDC)
            win32gui.DeleteObject(saveBitMap)
            
            # Add watermark
            screenshot = self.add_watermark(screenshot)
            
            return screenshot
            
        except Exception as e:
            log_error("Err-CAP", f"GDI capture failed: {str(e)}")
            return None
    
    def add_watermark(self, image: Image.Image) -> Image.Image:
        try:
            # Create a copy to avoid modifying original
            watermarked = image.copy()
            draw = ImageDraw.Draw(watermarked)
            
            # Get image dimensions
            width, height = watermarked.size
            
            # Try to use a system font, fallback to default
            try:
                font = ImageFont.truetype("arial.ttf", 36)
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
                fill=(0, 0, 0, 128)
            )
            
            # Add text watermark
            draw.text(
                (x, y),
                self.fallback_watermark_text,
                fill=(255, 255, 255, 200),
                font=font
            )
            
            return watermarked
            
        except Exception as e:
            log_error("Err-CAP", f"Watermark addition failed: {str(e)}")
            return image
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> Optional[Image.Image]:
        try:
            bbox = (x, y, x + width, y + height)
            screenshot = ImageGrab.grab(bbox)
            return screenshot
        except Exception as e:
            log_error("Err-CAP", f"Region capture failed: {str(e)}")
            return None