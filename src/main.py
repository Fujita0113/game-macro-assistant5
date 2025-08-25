#!/usr/bin/env python3
"""
GameMacroAssistant - Main application entry point
"""

import tkinter as tk
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow
from ui.recording_controller import RecordingController


def main():
    """Main application entry point."""
    print("GameMacroAssistant - Starting...")
    
    try:
        # Create root window
        root = tk.Tk()
        
        # Initialize controller
        controller = RecordingController()
        
        # Initialize main window
        window = MainWindow(root)
        
        # Connect controller to window
        setup_window_controller_integration(window, controller)
        
        print("GUI initialized - Ready for recording")
        
        # Start main loop
        window.run()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1
    
    return 0


def setup_window_controller_integration(window: MainWindow, controller: RecordingController):
    """Set up integration between main window and recording controller."""
    
    # Set up controller callbacks
    def on_recording_state_changed(recording: bool):
        """Handle recording state changes."""
        window.set_recording_state(recording)
    
    def on_recording_completed(recording_data):
        """Handle recording completion."""
        operation_count = recording_data.operation_count if recording_data else 0
        window.show_recording_completed(operation_count)
        
        # Print recording data to console for testing
        if recording_data:
            print(f"\n=== Recording Completed ===")
            print(f"Name: {recording_data.name}")
            print(f"Operations: {recording_data.operation_count}")
            print(f"Duration: {recording_data.duration:.2f}s")
            print(f"Created: {recording_data.created_at}")
            
            print("\n=== Operation Details ===")
            for i, op in enumerate(recording_data.operations, 1):
                print(f"{i}. {op.operation_type.value} at {op.timestamp:.3f}")
                if op.mouse_op:
                    print(f"   Mouse: {op.mouse_op.button.value} at ({op.mouse_op.position.x}, {op.mouse_op.position.y})")
                if op.keyboard_op:
                    print(f"   Key: {op.keyboard_op.action} '{op.keyboard_op.key}'")
    
    # Connect callbacks
    controller.on_recording_state_changed = on_recording_state_changed
    controller.on_recording_completed = on_recording_completed
    
    # Set up window callbacks
    def start_recording():
        """Start recording from UI."""
        success = controller.start_recording()
        if not success:
            print("Failed to start recording")
    
    window.on_start_recording = start_recording


if __name__ == "__main__":
    sys.exit(main())