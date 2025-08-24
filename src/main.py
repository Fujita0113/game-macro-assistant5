#!/usr/bin/env python3
"""
GameMacroAssistant - Main application entry point
"""
import argparse
import time
import sys
import json
from datetime import datetime

from core.input_capture import InputCaptureManager


def test_input_capture():
    """Test the input capture functionality."""
    print("=== Input Capture Test ===")
    print("This test will record mouse clicks and keyboard input.")
    print("Instructions:")
    print("1. Click 3 different locations on screen")
    print("2. Type 'Hello World'")
    print("3. Press ESC to stop recording")
    print()
    
    input("Press Enter to start recording...")
    
    manager = InputCaptureManager()
    manager.start_recording()
    
    # Wait for user to complete the test
    while manager.is_recording():
        time.sleep(0.1)
    
    print()
    print("=== Recording Results ===")
    events = manager.get_recorded_events()
    
    if not events:
        print("No events were recorded!")
        return False
    
    # Analyze recorded events
    mouse_clicks = [e for e in events if hasattr(e, 'button')]
    key_events = [e for e in events if hasattr(e, 'key')]
    
    print(f"Total events recorded: {len(events)}")
    print(f"Mouse clicks: {len(mouse_clicks)}")
    print(f"Keyboard events: {len(key_events)}")
    print()
    
    # Show mouse click details
    if mouse_clicks:
        print("Mouse clicks:")
        for i, event in enumerate(mouse_clicks, 1):
            print(f"  {i}. {event.button.value} click at ({event.x}, {event.y}) - {event.timestamp}")
    
    # Show keyboard input reconstruction
    if key_events:
        print("\nKeyboard input:")
        text_chars = []
        for event in key_events:
            # Only use KEY_PRESS events to avoid duplication
            if (event.type.value == "key_press" and 
                event.char and len(event.char) == 1 and event.char.isprintable()):
                text_chars.append(event.char)
        
        if text_chars:
            reconstructed_text = ''.join(text_chars)
            print(f"  Reconstructed text: '{reconstructed_text}'")
        
        key_list = [(e.key, e.type.value) for e in key_events[:20]]  # Show first 20 keys with type
        print(f"  All key events: {key_list}")
    
    # Export results to JSON
    try:
        export_data = {
            "test_timestamp": datetime.now().isoformat(),
            "total_events": len(events),
            "mouse_clicks": len(mouse_clicks),
            "keyboard_events": len(key_events),
            "events": [event.to_dict() for event in events]
        }
        
        with open("input_capture_test_results.json", "w") as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\nResults exported to: input_capture_test_results.json")
    except Exception as e:
        print(f"Failed to export results: {e}")
    
    # Validate test requirements
    success = True
    if len(mouse_clicks) < 3:
        print(f"❌ Expected at least 3 mouse clicks, got {len(mouse_clicks)}")
        success = False
    else:
        print("✅ Mouse clicks recorded successfully")
    
    # Check if "Hello World" was typed (approximate check)
    text_chars = [e.char for e in key_events if e.type.value == "key_press" and e.char and len(e.char) == 1 and e.char.isprintable()]
    reconstructed = ''.join(text_chars).lower()
    if "hello" in reconstructed and "world" in reconstructed:
        print("✅ 'Hello World' text input detected")
    else:
        print("❌ 'Hello World' text input not clearly detected")
        print(f"   Detected text: '{reconstructed}'")
        success = False
    
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    return success


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="GameMacroAssistant")
    parser.add_argument("--test-input", action="store_true", 
                       help="Run input capture integration test")
    
    args = parser.parse_args()
    
    if args.test_input:
        success = test_input_capture()
        sys.exit(0 if success else 1)
    
    print("GameMacroAssistant - Starting...")
    print("Use --test-input to run input capture test")
    # TODO: Initialize application components


if __name__ == "__main__":
    main()