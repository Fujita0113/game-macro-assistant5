"""
Image editor window for selecting regions within screenshots.

This module provides a GUI window for editing screenshot images by selecting
rectangular regions for macro condition matching.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from typing import Optional, Tuple, Callable
import io


class ImageEditor:
    """Image editor window for selecting regions within screenshots."""

    def __init__(
        self,
        parent: tk.Widget,
        image_data: bytes,
        on_confirm: Optional[Callable[[Tuple[int, int, int, int]], None]] = None,
    ):
        """
        Initialize the image editor window.

        Args:
            parent: Parent widget
            image_data: Screenshot image data as bytes
            on_confirm: Callback function called with selected region (x, y, width, height)
        """
        self.parent = parent
        self.image_data = image_data
        self.on_confirm = on_confirm

        # Selection state
        self.selection_start: Optional[Tuple[int, int]] = None
        self.selection_end: Optional[Tuple[int, int]] = None
        self.selection_rect: Optional[int] = None
        self.is_selecting = False

        # Window and canvas
        self.window: Optional[tk.Toplevel] = None
        self.canvas: Optional[tk.Canvas] = None
        self.image: Optional[Image.Image] = None
        self.photo: Optional[ImageTk.PhotoImage] = None
        self.image_item: Optional[int] = None
        self.ok_button: Optional[ttk.Button] = None
        self.load_failed = False

        # Scale factor for display
        self.scale_factor = 1.0
        self.display_width = 0
        self.display_height = 0

        self._setup_window()
        self._load_image()
        self._setup_ui()
        self._bind_events()

    def _setup_window(self):
        """Set up the image editor window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title('画像編集 - 領域選択')
        self.window.resizable(True, True)
        self.window.grab_set()  # Make window modal

        # Center the window
        self.window.geometry('800x600')
        self._center_window()

        # Handle window close
        self.window.protocol('WM_DELETE_WINDOW', self._on_cancel)

        # Bind keyboard shortcuts
        self.window.bind('<Return>', lambda e: self._on_confirm_click())
        self.window.bind('<Escape>', lambda e: self._on_cancel())

    def _center_window(self):
        """Center the window on the parent."""
        self.window.update_idletasks()

        # Get parent window position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Get this window size
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()

        # Calculate centered position
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2

        self.window.geometry(f'{window_width}x{window_height}+{x}+{y}')

    def _load_image(self):
        """Load and process the image for display."""
        try:
            # Load image from bytes
            self.image = Image.open(io.BytesIO(self.image_data))

            # Issue requirement: Handle very large images
            img_width, img_height = self.image.size
            if img_width > 10000 or img_height > 10000:
                self.load_failed = True
                self._show_error(
                    '画像が大きすぎます。10000x10000ピクセル以下の画像を使用してください。'
                )
                return

            # Calculate scale factor to fit in window while maintaining aspect ratio
            max_width = 700
            max_height = 500

            scale_x = max_width / img_width
            scale_y = max_height / img_height
            self.scale_factor = min(scale_x, scale_y, 1.0)  # Don't scale up

            # Calculate display size with improved precision
            self.display_width = round(img_width * self.scale_factor)
            self.display_height = round(img_height * self.scale_factor)

            # Resize image for display
            display_image = self.image.resize(
                (self.display_width, self.display_height), Image.Resampling.LANCZOS
            )

            # Convert to PhotoImage for tkinter
            self.photo = ImageTk.PhotoImage(display_image)

        except Exception as e:
            # Issue requirement: Appropriate error handling
            print(f'Error loading image: {e}')
            self.load_failed = True
            if 'cannot identify image file' in str(e).lower():
                self._show_error(
                    '画像形式が認識できません。PNG、JPEGなどの標準的な形式を使用してください。'
                )
            elif 'out of memory' in str(e).lower():
                self._show_error('メモリ不足です。より小さな画像を使用してください。')
            else:
                self._show_error('画像を読み込めませんでした。')

    def _setup_ui(self):
        """Set up the user interface elements."""
        # Main frame
        main_frame = ttk.Frame(self.window, padding='10')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Instructions label
        instructions = ttk.Label(
            main_frame,
            text='マウスをドラッグして領域を選択してください。',
            font=('Arial', 10),
        )
        instructions.pack(pady=(0, 10))

        # Canvas frame with scrollbars
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create canvas with scrollbars
        self.canvas = tk.Canvas(
            canvas_frame,
            bg='white',
            width=self.display_width,
            height=self.display_height,
        )

        v_scrollbar = ttk.Scrollbar(
            canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )
        h_scrollbar = ttk.Scrollbar(
            canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview
        )

        self.canvas.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # Pack scrollbars and canvas
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add image to canvas if loaded successfully
        if self.photo:
            self.image_item = self.canvas.create_image(
                0, 0, anchor=tk.NW, image=self.photo
            )
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        # Buttons
        self.ok_button = ttk.Button(
            button_frame, text='OK', command=self._on_confirm_click, width=15
        )
        self.ok_button.pack(side=tk.RIGHT, padx=(10, 0))

        # Disable OK button if image loading failed
        if self.load_failed or not self.photo:
            self.ok_button.config(state='disabled')

        ttk.Button(
            button_frame, text='キャンセル', command=self._on_cancel, width=15
        ).pack(side=tk.RIGHT)

        # Clear selection button
        ttk.Button(
            button_frame, text='選択をクリア', command=self._clear_selection, width=15
        ).pack(side=tk.LEFT)

    def _bind_events(self):
        """Bind mouse events for selection."""
        if self.canvas and self.photo and not self.load_failed:
            self.canvas.bind('<Button-1>', self._on_mouse_down)
            self.canvas.bind('<B1-Motion>', self._on_mouse_drag)
            self.canvas.bind('<ButtonRelease-1>', self._on_mouse_up)

    def _on_mouse_down(self, event):
        """Handle mouse button down event."""
        # Convert canvas coordinates to image coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Check if click is within image bounds
        if 0 <= canvas_x <= self.display_width and 0 <= canvas_y <= self.display_height:
            self.selection_start = (int(canvas_x), int(canvas_y))
            self.selection_end = self.selection_start
            self.is_selecting = True

            # Clear previous selection
            self._clear_selection_rect()

    def _on_mouse_drag(self, event):
        """Handle mouse drag event."""
        if not self.is_selecting or not self.selection_start:
            return

        # Convert canvas coordinates to image coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Clamp coordinates to image bounds
        canvas_x = max(0, min(canvas_x, self.display_width))
        canvas_y = max(0, min(canvas_y, self.display_height))

        self.selection_end = (int(canvas_x), int(canvas_y))

        # Update selection rectangle
        self._update_selection_rect()

    def _on_mouse_up(self, event):
        """Handle mouse button up event."""
        self.is_selecting = False

    def _update_selection_rect(self):
        """Update the selection rectangle on canvas."""
        if not self.selection_start or not self.selection_end:
            return

        # Clear previous rectangle
        self._clear_selection_rect()

        # Calculate rectangle coordinates
        x1, y1 = self.selection_start
        x2, y2 = self.selection_end

        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)

        # Only draw if there's a meaningful selection
        if abs(right - left) > 2 and abs(bottom - top) > 2:
            self.selection_rect = self.canvas.create_rectangle(
                left,
                top,
                right,
                bottom,
                outline='red',
                width=2,
                fill='red',
                stipple='gray25',
            )

    def _clear_selection_rect(self):
        """Clear the selection rectangle from canvas."""
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None

    def _clear_selection(self):
        """Clear the current selection."""
        self.selection_start = None
        self.selection_end = None
        self._clear_selection_rect()

    def _get_selection_region(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Get the selected region in original image coordinates.

        Returns:
            Tuple of (x, y, width, height) in original image coordinates,
            or None if no valid selection.
        """
        if not self.selection_start or not self.selection_end:
            return None

        # Get display coordinates
        x1, y1 = self.selection_start
        x2, y2 = self.selection_end

        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)

        width = right - left
        height = bottom - top

        # Check for minimum selection size
        if width < 5 or height < 5:
            return None

        # Convert to original image coordinates with improved precision
        orig_x = round(left / self.scale_factor)
        orig_y = round(top / self.scale_factor)
        orig_width = round(width / self.scale_factor)
        orig_height = round(height / self.scale_factor)

        # Ensure coordinates are within original image bounds
        if self.image:
            img_width, img_height = self.image.size
            orig_x = max(0, min(orig_x, img_width - 1))
            orig_y = max(0, min(orig_y, img_height - 1))
            orig_width = min(orig_width, img_width - orig_x)
            orig_height = min(orig_height, img_height - orig_y)

        return (orig_x, orig_y, orig_width, orig_height)

    def _on_confirm_click(self):
        """Handle OK button click."""
        selection = self._get_selection_region()

        if selection is None:
            self._show_error(
                '有効な領域を選択してください。\n（最小サイズ: 5x5ピクセル）'
            )
            return

        # Call confirmation callback
        if self.on_confirm:
            self.on_confirm(selection)

        self._close_window()

    def _on_cancel(self):
        """Handle cancel button click or window close."""
        self._close_window()

    def _close_window(self):
        """Close the image editor window."""
        if self.window:
            self.window.grab_release()
            self.window.destroy()

    def _show_error(self, message: str):
        """Show error message to user."""
        messagebox.showerror('エラー', message, parent=self.window)

    @staticmethod
    def open_image_editor(
        parent: tk.Widget,
        image_data: bytes,
        on_confirm: Optional[Callable[[Tuple[int, int, int, int]], None]] = None,
    ) -> 'ImageEditor':
        """
        Open an image editor window.

        Args:
            parent: Parent widget
            image_data: Screenshot image data as bytes
            on_confirm: Callback function called with selected region

        Returns:
            ImageEditor instance
        """
        return ImageEditor(parent, image_data, on_confirm)
