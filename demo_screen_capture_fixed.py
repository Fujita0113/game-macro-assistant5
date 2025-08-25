#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Screen Capture System Demo and Test Script

Usage:
1. python demo_screen_capture_fixed.py - Basic tests
2. python demo_screen_capture_fixed.py --manual - Manual test mode
3. python demo_screen_capture_fixed.py --fullscreen - Fullscreen test mode
"""

import sys
import os
import time
import argparse
from PIL import Image

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.screen_capture import ScreenCaptureManager
from src.core.event_handler import ScreenCaptureEventHandler
from src.utils.logging import log_info, log_error


def test_basic_capture():
    """Basic screen capture test"""
    print("=== Basic Screen Capture Test ===")
    
    capture_manager = ScreenCaptureManager()
    
    # Take screenshot
    print("Taking screenshot...")
    screenshot = capture_manager.capture_screen("test_basic_capture.png")
    
    if screenshot:
        print(f"[SUCCESS] Screenshot saved (size: {screenshot.size})")
        print("File: test_basic_capture.png")
    else:
        print("[FAILED] Screenshot capture failed")
    
    return screenshot is not None


def test_region_capture():
    """Region capture test"""
    print("\n=== Region Capture Test ===")
    
    capture_manager = ScreenCaptureManager()
    
    # Capture center 200x200 region
    print("Capturing center 200x200 region...")
    screenshot = capture_manager.capture_region(400, 300, 200, 200)
    
    if screenshot:
        screenshot.save("test_region_capture.png")
        print(f"[SUCCESS] Region capture saved (size: {screenshot.size})")
        print("File: test_region_capture.png")
    else:
        print("[FAILED] Region capture failed")
    
    return screenshot is not None


def test_watermark():
    """Watermark feature test"""
    print("\n=== Watermark Feature Test ===")
    
    capture_manager = ScreenCaptureManager()
    
    # Create test image
    test_image = Image.new('RGB', (800, 600), color='lightblue')
    
    # Add watermark
    print("Adding watermark...")
    watermarked = capture_manager.add_watermark(test_image)
    
    if watermarked:
        watermarked.save("test_watermark.png")
        print("[SUCCESS] Watermarked image saved")
        print("File: test_watermark.png")
        print("Watermark text:", capture_manager.fallback_watermark_text)
    else:
        print("[FAILED] Watermark addition failed")
    
    return watermarked is not None


def test_event_handler():
    """Event handler test"""
    print("\n=== Event Handler Test ===")
    
    event_handler = ScreenCaptureEventHandler()
    
    def screenshot_callback(filepath):
        print(f"Callback: Screenshot saved -> {filepath}")
    
    event_handler.set_screenshot_callback(screenshot_callback)
    
    # Simulate mouse click event
    print("Simulating mouse click event...")
    filepath = event_handler.capture_on_mouse_click(100, 200, "left")
    
    if filepath:
        print("[SUCCESS] Event handler working correctly")
    else:
        print("[FAILED] Event handler error occurred")
    
    return filepath is not None


def test_error_simulation():
    """Error simulation test"""
    print("\n=== Error Simulation Test ===")
    
    # Test with invalid path
    capture_manager = ScreenCaptureManager()
    
    try:
        print("Testing save to invalid path...")
        result = capture_manager.capture_screen("invalid/path/test.png")
        if result is None:
            print("[SUCCESS] Error handled correctly")
        else:
            print("[WARNING] No error occurred (unexpected result)")
    except Exception as e:
        print(f"[SUCCESS] Exception caught properly - {e}")
    
    print("Check log files for Err-CAP error codes")


def manual_test():
    """Manual test with user interaction"""
    print("\n=== Manual Test Mode ===")
    print("This mode captures screenshots based on your interactions")
    
    event_handler = ScreenCaptureEventHandler()
    
    input("Press Enter when ready...")
    
    print("\n1. Basic capture test")
    input("Press Enter to take screenshot...")
    filepath = event_handler.capture_manual()
    if filepath:
        print(f"[SUCCESS] Screenshot saved: {filepath}")
    
    print("\n2. Directory change test")
    event_handler.set_screenshot_directory("manual_test_screenshots")
    input("Press Enter to save to different directory...")
    filepath = event_handler.capture_manual()
    if filepath:
        print(f"[SUCCESS] Screenshot saved: {filepath}")
    
    print("\nManual test complete!")


def fullscreen_test():
    """Fullscreen application test"""
    print("\n=== Fullscreen Test Mode ===")
    print("This test checks GDI fallback functionality")
    
    capture_manager = ScreenCaptureManager()
    
    print("\nInstructions:")
    print("1. After this message, launch a fullscreen application (game, video player, etc.)")
    print("2. Screenshot will be taken automatically after 5 seconds")
    print("3. Check if 'CaptureLimited' watermark is present")
    
    input("Press Enter when ready...")
    
    for i in range(5, 0, -1):
        print(f"Screenshot in {i} seconds...")
        time.sleep(1)
    
    print("Taking screenshot...")
    screenshot = capture_manager.capture_screen("fullscreen_test.png")
    
    if screenshot:
        print("[SUCCESS] Fullscreen test complete")
        print("File: fullscreen_test.png")
        print("If watermark is present, GDI fallback worked")
    else:
        print("[FAILED] Fullscreen test failed")


def main():
    parser = argparse.ArgumentParser(description='Screen Capture System Test')
    parser.add_argument('--manual', action='store_true', help='Manual test mode')
    parser.add_argument('--fullscreen', action='store_true', help='Fullscreen test mode')
    
    args = parser.parse_args()
    
    print("GameMacroAssistant - Screen Capture System Test")
    print("=" * 60)
    
    if args.manual:
        manual_test()
    elif args.fullscreen:
        fullscreen_test()
    else:
        # Automatic test suite
        results = []
        
        results.append(test_basic_capture())
        results.append(test_region_capture())
        results.append(test_watermark())
        results.append(test_event_handler())
        test_error_simulation()
        
        print("\n" + "=" * 60)
        print("Test Results Summary")
        print("=" * 60)
        
        passed = sum(results)
        total = len(results)
        
        print(f"[PASSED] {passed}/{total} tests")
        
        if passed == total:
            print("All tests passed successfully!")
        else:
            print("Some tests failed")
        
        print("\nGenerated files:")
        for filename in ["test_basic_capture.png", "test_region_capture.png", 
                        "test_watermark.png", "screenshots/"]:
            if os.path.exists(filename):
                print(f"  - {filename}")
        
        print("\nLog file check:")
        print("  - Check logs/ directory for Err-CAP error logs")


if __name__ == "__main__":
    main()