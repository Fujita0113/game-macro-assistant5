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
import math
from enum import Enum


class ImageLoadErrorType(Enum):
    """Types of image loading errors."""

    INVALID_FORMAT = 'invalid_format'
    OVERSIZED_IMAGE = 'oversized_image'
    MEMORY_ERROR = 'memory_error'
    IO_ERROR = 'io_error'
    GENERIC_ERROR = 'generic_error'


class ImageLoadError(Exception):
    """Custom exception for image loading errors."""

    def __init__(
        self,
        error_type: ImageLoadErrorType,
        message: str,
        original_error: Exception = None,
    ):
        self.error_type = error_type
        self.message = message
        self.original_error = original_error
        super().__init__(message)


class CoordinateTransformer:
    """High-precision coordinate transformation for image scaling."""

    def __init__(self, original_size: Tuple[int, int], display_size: Tuple[int, int]):
        """
        Initialize coordinate transformer.

        Args:
            original_size: (width, height) of original image
            display_size: (width, height) of display image

        Raises:
            ValueError: If any dimension is zero or negative
        """
        self.original_width, self.original_height = original_size
        self.display_width, self.display_height = display_size

        # Validate dimensions
        if self.original_width <= 0 or self.original_height <= 0:
            raise ValueError(f'Invalid original size: {original_size}')
        if self.display_width <= 0 or self.display_height <= 0:
            raise ValueError(f'Invalid display size: {display_size}')

        # Calculate precise scale factors
        self.scale_x = self.display_width / self.original_width
        self.scale_y = self.display_height / self.original_height
        self.scale_factor = min(self.scale_x, self.scale_y)

        # Calculate actual display dimensions (maintaining aspect ratio)
        self.actual_display_width = self.original_width * self.scale_factor
        self.actual_display_height = self.original_height * self.scale_factor

    def display_to_original(
        self, x: float, y: float, width: float, height: float
    ) -> Tuple[int, int, int, int]:
        """
        Convert display coordinates to original image coordinates with high precision.

        Args:
            x, y, width, height: Selection in display coordinates

        Returns:
            Tuple of (x, y, width, height) in original image coordinates
        """
        if self.scale_factor <= 0:
            raise ValueError('Invalid scale factor')

        # Convert to original coordinates with high precision
        orig_x = x / self.scale_factor
        orig_y = y / self.scale_factor
        orig_width = width / self.scale_factor
        orig_height = height / self.scale_factor

        # Apply precision rounding (±0.5 pixel accuracy)
        orig_x_int = int(math.floor(orig_x + 0.5))
        orig_y_int = int(math.floor(orig_y + 0.5))
        orig_width_int = int(math.floor(orig_width + 0.5))
        orig_height_int = int(math.floor(orig_height + 0.5))

        # Clamp to original image bounds
        orig_x_int = max(0, min(orig_x_int, self.original_width - 1))
        orig_y_int = max(0, min(orig_y_int, self.original_height - 1))
        orig_width_int = max(1, min(orig_width_int, self.original_width - orig_x_int))
        orig_height_int = max(
            1, min(orig_height_int, self.original_height - orig_y_int)
        )

        return (orig_x_int, orig_y_int, orig_width_int, orig_height_int)

    def original_to_display(
        self, x: int, y: int, width: int, height: int
    ) -> Tuple[float, float, float, float]:
        """
        Convert original coordinates to display coordinates.

        Args:
            x, y, width, height: Selection in original coordinates

        Returns:
            Tuple of (x, y, width, height) in display coordinates
        """
        display_x = x * self.scale_factor
        display_y = y * self.scale_factor
        display_width = width * self.scale_factor
        display_height = height * self.scale_factor

        return (display_x, display_y, display_width, display_height)


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

        # High-precision coordinate transformation
        self.coordinate_transformer: Optional[CoordinateTransformer] = None
        self.display_width = 0
        self.display_height = 0

        self._setup_window()

        # Load image with unified error handling
        try:
            self._load_image()
        except ImageLoadError as e:
            self._handle_image_load_error(e)

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
        try:
            self.window.update_idletasks()

            # Get parent window position and size (with fallback for testing)
            try:
                parent_x = self.parent.winfo_rootx()
                parent_y = self.parent.winfo_rooty()
                parent_width = self.parent.winfo_width()
                parent_height = self.parent.winfo_height()
            except (AttributeError, TypeError):
                # Fallback for testing with mocks
                parent_x, parent_y = 100, 100
                parent_width, parent_height = 1024, 768

            # Get this window size (with fallback)
            try:
                window_width = self.window.winfo_width()
                window_height = self.window.winfo_height()
            except (AttributeError, TypeError):
                # Fallback for testing
                window_width, window_height = 800, 600

            # Calculate centered position
            x = parent_x + (parent_width - window_width) // 2
            y = parent_y + (parent_height - window_height) // 2

            self.window.geometry(f'{window_width}x{window_height}+{x}+{y}')

        except Exception as e:
            # Fallback positioning if centering fails
            print(f'Warning: Could not center window: {e}')
            try:
                self.window.geometry('800x600+100+100')
            except Exception:
                pass  # Ignore geometry errors in test environment

    def _load_image(self):
        """Load and process the image for display."""
        try:
            # Validate image data first
            if not self.image_data:
                raise ImageLoadError(
                    ImageLoadErrorType.INVALID_FORMAT, 'Empty image data provided'
                )

            # Load image from bytes with enhanced validation
            self.image = self._safe_image_open(self.image_data)

            # Validate image dimensions
            img_width, img_height = self.image.size
            if img_width > 10000 or img_height > 10000:
                raise ImageLoadError(
                    ImageLoadErrorType.OVERSIZED_IMAGE,
                    f'Image too large: {img_width}x{img_height} pixels (max: 10000x10000)',
                    None,
                )

            # Initialize high-precision coordinate transformer
            max_width = 700
            max_height = 500
            self.coordinate_transformer = CoordinateTransformer(
                original_size=(img_width, img_height),
                display_size=(max_width, max_height),
            )

            # Calculate precise display dimensions
            self.display_width = int(self.coordinate_transformer.actual_display_width)
            self.display_height = int(self.coordinate_transformer.actual_display_height)

            # Resize image for display with high quality resampling
            display_image = self.image.resize(
                (self.display_width, self.display_height), Image.Resampling.LANCZOS
            )

            # Convert to PhotoImage for tkinter
            self.photo = ImageTk.PhotoImage(display_image)

        except ImageLoadError:
            # Re-raise custom errors for unified handling
            raise
        except Exception as e:
            # Convert generic exceptions to custom errors
            error_type, message = self._classify_image_error(e)
            raise ImageLoadError(error_type, message, e) from e

    def _safe_image_open(self, image_data: bytes) -> Image.Image:
        """Safely open image with validation and error classification."""
        try:
            # Basic format validation
            if len(image_data) < 8:  # Too small to be a valid image
                raise ValueError('Image data too small')

            # Try to open the image
            image = Image.open(io.BytesIO(image_data))

            # Verify the image can be loaded
            image.load()

            # Validate basic properties
            if image.size[0] <= 0 or image.size[1] <= 0:
                raise ValueError('Invalid image dimensions')

            return image

        except (IOError, OSError) as e:
            # Handle I/O related errors
            if 'cannot identify image file' in str(e).lower():
                raise ImageLoadError(
                    ImageLoadErrorType.INVALID_FORMAT,
                    'Unsupported image format. Please use PNG, JPEG, or other standard formats.',
                    e,
                ) from e
            else:
                raise ImageLoadError(
                    ImageLoadErrorType.IO_ERROR, 'Failed to read image data', e
                ) from e
        except MemoryError as e:
            raise ImageLoadError(
                ImageLoadErrorType.MEMORY_ERROR,
                'Insufficient memory to load image. Please use a smaller image.',
                e,
            ) from e
        except Exception as e:
            raise ImageLoadError(
                ImageLoadErrorType.GENERIC_ERROR,
                f'Unexpected error loading image: {str(e)}',
                e,
            ) from e

    def _classify_image_error(self, error: Exception) -> Tuple[ImageLoadErrorType, str]:
        """Classify generic exceptions into specific error types."""
        error_msg = str(error).lower()

        if (
            'cannot identify image file' in error_msg
            or 'invalid image format' in error_msg
        ):
            return (
                ImageLoadErrorType.INVALID_FORMAT,
                '画像形式が認識できません。PNG、JPEGなどの標準的な形式を使用してください。',
            )
        elif 'out of memory' in error_msg or 'memory' in error_msg:
            return (
                ImageLoadErrorType.MEMORY_ERROR,
                'メモリ不足です。より小さな画像を使用してください。',
            )
        elif 'io' in error_msg or 'read' in error_msg or 'file' in error_msg:
            return (
                ImageLoadErrorType.IO_ERROR,
                '画像ファイルの読み込みに失敗しました。',
            )
        else:
            return (ImageLoadErrorType.GENERIC_ERROR, '画像を読み込めませんでした。')

    def _handle_image_load_error(self, error: ImageLoadError):
        """Unified error handling for all image loading errors."""
        self.load_failed = True
        print(f'Image loading error ({error.error_type.value}): {error.message}')

        if error.original_error:
            print(f'Original error: {error.original_error}')

        # Show user-friendly error message
        self._show_error(error.message)

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
        Get the selected region in original image coordinates with high precision.

        Returns:
            Tuple of (x, y, width, height) in original image coordinates,
            or None if no valid selection.
        """
        if (
            not self.selection_start
            or not self.selection_end
            or not self.coordinate_transformer
        ):
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

        # Check for minimum selection size in display coordinates
        if width < 5 or height < 5:
            return None

        # Use high-precision coordinate transformation
        try:
            orig_x, orig_y, orig_width, orig_height = (
                self.coordinate_transformer.display_to_original(
                    left, top, width, height
                )
            )

            # Validate minimum size in original coordinates
            if orig_width < 1 or orig_height < 1:
                return None

            return (orig_x, orig_y, orig_width, orig_height)

        except (ValueError, ZeroDivisionError) as e:
            print(f'Coordinate transformation error: {e}')
            return None

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
        """Close the image editor window with proper resource cleanup."""
        try:
            if self.window:
                # Release modal grab first
                try:
                    self.window.grab_release()
                except tk.TclError:
                    # Ignore grab release errors (window might be already destroyed)
                    pass

                # Clean up image resources
                self._cleanup_image_resources()

                # Destroy window
                try:
                    self.window.destroy()
                except tk.TclError:
                    # Ignore destruction errors (window might be already destroyed)
                    pass
                finally:
                    self.window = None

        except Exception as e:
            print(f'Warning: Error during window cleanup: {e}')
            # Ensure window reference is cleared even if cleanup fails
            self.window = None

    def _cleanup_image_resources(self):
        """Clean up image and canvas resources to prevent memory leaks."""
        try:
            # Clear PhotoImage reference to free memory
            if self.photo:
                # PhotoImage cleanup is handled by Python garbage collection
                self.photo = None

            # Clear PIL Image reference
            if self.image:
                try:
                    self.image.close()
                except Exception:
                    pass  # Ignore close errors
                self.image = None

            # Clear canvas item reference
            if self.canvas and self.image_item:
                try:
                    self.canvas.delete(self.image_item)
                except tk.TclError:
                    pass  # Canvas might already be destroyed
                self.image_item = None

        except Exception as e:
            print(f'Warning: Error during image resource cleanup: {e}')

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
