#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated fullscreen test - no user input required
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.screen_capture import ScreenCaptureManager
from src.utils.logging import log_info

def test_gdi_fallback():
    """Test GDI fallback by forcing native capture to fail"""
    print("=== GDI Fallback Test ===")
    
    capture_manager = ScreenCaptureManager()
    
    # First test: Normal capture
    print("1. Testing normal capture...")
    normal_screenshot = capture_manager.capture_screen("normal_capture_test.png")
    
    if normal_screenshot:
        print(f"[SUCCESS] Normal capture (size: {normal_screenshot.size})")
    else:
        print("[FAILED] Normal capture failed")
    
    # Second test: Force GDI capture by testing the GDI method directly
    print("2. Testing GDI fallback method...")
    gdi_screenshot = capture_manager._gdi_capture_with_watermark()
    
    if gdi_screenshot:
        gdi_screenshot.save("gdi_fallback_test.png")
        print(f"[SUCCESS] GDI fallback works (size: {gdi_screenshot.size})")
        print("File: gdi_fallback_test.png")
        print("Check for 'CaptureLimited' watermark in the image")
    else:
        print("[FAILED] GDI fallback failed")
    
    # Third test: Watermark functionality
    print("3. Testing watermark on real screenshot...")
    if normal_screenshot:
        watermarked = capture_manager.add_watermark(normal_screenshot)
        watermarked.save("watermark_real_test.png")
        print("[SUCCESS] Watermark applied to real screenshot")
        print("File: watermark_real_test.png")
    
    return True

if __name__ == "__main__":
    print("Automated GDI Fallback and Watermark Test")
    print("=" * 50)
    
    test_gdi_fallback()
    
    print("\nTest complete!")
    print("Generated files:")
    for f in ["normal_capture_test.png", "gdi_fallback_test.png", "watermark_real_test.png"]:
        if os.path.exists(f):
            print(f"  - {f}")