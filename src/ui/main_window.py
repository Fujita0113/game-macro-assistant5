"""
Main window for GameMacroAssistant recording interface.

This module provides the primary GUI for controlling macro recording operations.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional


class MainWindow:
    """Main application window for recording control."""
    
    def __init__(self, root: Optional[tk.Tk] = None):
        """
        Initialize the main window.
        
        Args:
            root: Optional existing Tk root. If None, creates new root.
        """
        self.root = root if root else tk.Tk()
        self.root.title("GameMacroAssistant - Recording Control")
        self.root.geometry("400x200")
        self.root.resizable(False, False)
        
        # Recording state
        self.is_recording = False
        
        # Callbacks for recording control
        self.on_start_recording: Optional[Callable[[], None]] = None
        self.on_stop_recording: Optional[Callable[[], None]] = None
        
        self._setup_ui()
        self._center_window()
    
    def _setup_ui(self):
        """Set up the user interface elements."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Title label
        title_label = ttk.Label(
            main_frame, 
            text="GameMacroAssistant",
            font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Status label
        self.status_label = ttk.Label(
            main_frame,
            text="準備完了",
            font=("Arial", 10)
        )
        self.status_label.grid(row=1, column=0, pady=(0, 20))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=(0, 10))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        # Start recording button
        self.start_button = ttk.Button(
            button_frame,
            text="記録開始",
            command=self._on_start_clicked,
            width=12
        )
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        # Exit button
        self.exit_button = ttk.Button(
            button_frame,
            text="終了",
            command=self._on_exit_clicked,
            width=12
        )
        self.exit_button.grid(row=0, column=1, padx=(10, 0))
        
        # Instructions label
        instructions = ttk.Label(
            main_frame,
            text="記録を開始してマウス・キーボード操作を行ってください。\nESCキーで記録を停止します。",
            font=("Arial", 9),
            justify="center"
        )
        instructions.grid(row=3, column=0, pady=(10, 0))
    
    def _center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        
        # Get window size
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        # Get screen size
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _on_start_clicked(self):
        """Handle start recording button click."""
        if self.on_start_recording:
            self.on_start_recording()
    
    def _on_exit_clicked(self):
        """Handle exit button click."""
        if self.is_recording:
            result = messagebox.askyesno(
                "確認",
                "記録中です。終了してもよろしいですか？"
            )
            if not result:
                return
        
        self.root.quit()
    
    def set_recording_state(self, recording: bool):
        """
        Update UI to reflect recording state.
        
        Args:
            recording: True if recording is active, False otherwise.
        """
        self.is_recording = recording
        
        if recording:
            self.start_button.config(state="disabled", text="記録中...")
            self.status_label.config(text="記録中 (ESCキーで停止)")
        else:
            self.start_button.config(state="normal", text="記録開始")
            self.status_label.config(text="準備完了")
    
    def show_recording_completed(self, operation_count: int):
        """
        Show recording completion message.
        
        Args:
            operation_count: Number of operations recorded.
        """
        messagebox.showinfo(
            "記録完了",
            f"記録が完了しました。操作数: {operation_count}"
        )
    
    def run(self):
        """Start the main event loop."""
        self.root.mainloop()
    
    def destroy(self):
        """Clean up and destroy the window."""
        self.root.destroy()