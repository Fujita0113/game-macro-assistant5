"""
Image editor module for GameMacroAssistant.

This module provides an image editing window that allows users to select
rectangular areas from screenshots for macro condition checking.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk


class ImageEditor(tk.Toplevel):
    """Image editing window for selecting rectangular areas from screenshots."""

    def __init__(self, parent: tk.Tk, image: Image.Image):
        """Initialize the image editor window.

        Args:
            parent: Parent tkinter window
            image: PIL Image to edit
        """
        super().__init__(parent)

        self.title('画像編集')
        self.image = image
        self.photo_image = None
        self.canvas = None
        self.selection_rect = None
        self.selection_coords = None
        self.start_x = 0
        self.start_y = 0

        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        # Make window modal
        self.transient(self.master)
        self.grab_set()

        # Set up main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create canvas for image display
        self.canvas = tk.Canvas(main_frame, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Convert PIL image to PhotoImage for display
        self.photo_image = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)

        # Configure canvas size
        self.canvas.configure(scrollregion=(0, 0, self.image.width, self.image.height))

        # Bind mouse events for rectangle selection
        self.canvas.bind('<Button-1>', self._on_mouse_press)
        self.canvas.bind('<B1-Motion>', self._on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_mouse_release)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # OK and Cancel buttons
        ttk.Button(button_frame, text='キャンセル', command=self.destroy).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        ttk.Button(button_frame, text='OK', command=self._on_ok).pack(side=tk.RIGHT)

        # Resize window to fit image
        window_width = min(800, self.image.width + 40)
        window_height = min(600, self.image.height + 100)
        self.geometry(f'{window_width}x{window_height}')

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (window_width // 2)
        y = (self.winfo_screenheight() // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')

    def _on_mouse_press(self, event):
        """Handle mouse press to start rectangle selection."""
        self.start_x = event.x
        self.start_y = event.y

        # Remove existing selection rectangle if any
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None

    def _on_mouse_drag(self, event):
        """Handle mouse drag to update rectangle selection."""
        # Remove existing selection rectangle if any
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)

        # Create new selection rectangle
        self.selection_rect = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            event.x,
            event.y,
            outline='red',
            width=2,
            fill='',
            tags='selection',
        )

    def _on_mouse_release(self, event):
        """Handle mouse release to finalize rectangle selection."""
        if self.start_x is not None and self.start_y is not None:
            # Store selection coordinates
            x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
            x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
            self.selection_coords = (x1, y1, x2, y2)

    def _on_ok(self):
        """Handle OK button click."""
        # Check if we have a valid selection
        if self.selection_coords:
            x1, y1, x2, y2 = self.selection_coords
            width = x2 - x1
            height = y2 - y1

            # Check minimum size requirement (5x5 pixels)
            if width < 5 or height < 5:
                messagebox.showerror(
                    '選択エラー',
                    '選択領域は5x5ピクセル以上である必要があります。\n'
                    f'現在の選択: {width}x{height}ピクセル',
                )
                return

        self.destroy()
