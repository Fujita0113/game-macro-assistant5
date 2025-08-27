"""
Visual editor for macro operations with block-based representation.

This module provides a GUI window for editing macro recordings with drag-and-drop
block reordering and image editing capabilities.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional, Callable
from PIL import Image, ImageTk
import io

from ..core.macro_data import MacroRecording, OperationBlock, OperationType
from .image_editor import ImageEditor
from .dialogs.file_dialog_manager import FileDialogManager


class OperationBlockWidget:
    """Widget representing a single operation block."""

    def __init__(
        self,
        parent: tk.Widget,
        block: OperationBlock,
        on_image_edit: Optional[Callable[['OperationBlockWidget'], None]] = None,
    ):
        """
        Initialize operation block widget.

        Args:
            parent: Parent widget
            block: Operation block data
            on_image_edit: Callback for image editing
        """
        self.parent = parent
        self.block = block
        self.on_image_edit = on_image_edit

        # Create main frame
        self.frame = ttk.LabelFrame(parent, text=self._get_block_title(), padding='10')

        # Create content
        self._setup_content()

    def _get_block_title(self) -> str:
        """Get display title for this block."""
        type_map = {
            OperationType.MOUSE_CLICK: 'マウスクリック',
            OperationType.MOUSE_MOVE: 'マウス移動',
            OperationType.KEY_PRESS: 'キー押下',
            OperationType.KEY_RELEASE: 'キー離す',
            OperationType.WAIT: '待機',
            OperationType.SCREEN_CONDITION: '画面条件',
        }
        return type_map.get(self.block.operation_type, '不明な操作')

    def _setup_content(self):
        """Set up block content based on operation type."""
        content_frame = ttk.Frame(self.frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        if (
            self.block.operation_type == OperationType.MOUSE_CLICK
            and self.block.mouse_op
        ):
            self._setup_mouse_content(content_frame)
        elif (
            self.block.operation_type == OperationType.KEY_PRESS
            and self.block.keyboard_op
        ):
            self._setup_keyboard_content(content_frame)
        elif (
            self.block.operation_type == OperationType.SCREEN_CONDITION
            and self.block.screen_condition
        ):
            self._setup_screen_condition_content(content_frame)
        else:
            # Default content
            ttk.Label(content_frame, text=f'操作ID: {self.block.id}').pack(anchor=tk.W)

    def _setup_mouse_content(self, parent: tk.Widget):
        """Set up content for mouse operation."""
        if not self.block.mouse_op:
            return

        mouse_op = self.block.mouse_op

        # Mouse button and position info
        info_text = f'ボタン: {mouse_op.button.value}\n座標: ({mouse_op.position.x}, {mouse_op.position.y})'
        ttk.Label(parent, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)

    def _setup_keyboard_content(self, parent: tk.Widget):
        """Set up content for keyboard operation."""
        if not self.block.keyboard_op:
            return

        keyboard_op = self.block.keyboard_op

        # Key and modifiers info
        modifiers_text = (
            ' + '.join(keyboard_op.modifiers) if keyboard_op.modifiers else ''
        )
        key_text = (
            f'{modifiers_text} + {keyboard_op.key}'
            if modifiers_text
            else keyboard_op.key
        )

        info_text = f'キー: {key_text}\nアクション: {keyboard_op.action}'
        ttk.Label(parent, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)

    def _setup_screen_condition_content(self, parent: tk.Widget):
        """Set up content for screen condition operation."""
        if not self.block.screen_condition:
            return

        screen_condition = self.block.screen_condition

        # Create image display if image data exists
        if screen_condition.image_data:
            try:
                # Load and resize image for display
                image = Image.open(io.BytesIO(screen_condition.image_data))

                # Resize to thumbnail size
                thumb_size = (100, 100)
                image.thumbnail(thumb_size, Image.Resampling.LANCZOS)

                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(image)

                # Create image label with double-click binding
                image_label = ttk.Label(parent, image=photo, cursor='hand2')
                image_label.image = (
                    photo  # Keep reference to prevent garbage collection
                )
                image_label.pack(anchor=tk.W, pady=(0, 5))

                # Bind double-click event
                image_label.bind(
                    '<Double-Button-1>', lambda e: self._on_image_double_click()
                )

                # Add tooltip
                self._add_tooltip(image_label, 'ダブルクリックで画像を編集')

            except Exception as e:
                print(f'Error loading image thumbnail: {e}')

        # Condition info
        region_text = (
            '全画面'
            if not screen_condition.region
            else f'領域: {screen_condition.region}'
        )
        info_text = f'{region_text}\n閾値: {screen_condition.threshold}\nタイムアウト: {screen_condition.timeout}秒'
        ttk.Label(parent, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)

    def _on_image_double_click(self):
        """Handle double-click on screenshot image."""
        if self.on_image_edit:
            self.on_image_edit(self)

    def _add_tooltip(self, widget: tk.Widget, text: str):
        """Add tooltip to widget."""

        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f'+{event.x_root + 10}+{event.y_root + 10}')
            label = ttk.Label(
                tooltip,
                text=text,
                background='lightyellow',
                relief=tk.SOLID,
                borderwidth=1,
            )
            label.pack()
            widget.tooltip = tooltip

        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')

        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

    def pack(self, **kwargs):
        """Pack the block widget."""
        self.frame.pack(**kwargs)

    def destroy(self):
        """Destroy the block widget."""
        self.frame.destroy()


class VisualEditor:
    """Visual editor window for macro editing."""

    def __init__(self, recording: MacroRecording, parent: Optional[tk.Widget] = None):
        """
        Initialize visual editor.

        Args:
            recording: Macro recording to edit
            parent: Parent widget (optional)
        """
        self.recording = recording
        self.parent = parent
        self.block_widgets: List[OperationBlockWidget] = []

        # Window components
        self.window: Optional[tk.Toplevel] = None
        self.main_frame: Optional[ttk.Frame] = None
        self.scroll_frame: Optional[ttk.Frame] = None
        self.canvas: Optional[tk.Canvas] = None
        self.scrollable_frame: Optional[ttk.Frame] = None

        # File dialog manager for save/load operations
        self.file_dialog_manager: Optional[FileDialogManager] = None

        self._setup_window()
        self._setup_ui()
        self._create_block_widgets()

    def _setup_window(self):
        """Set up the visual editor window."""
        if self.parent:
            self.window = tk.Toplevel(self.parent)
        else:
            self.window = tk.Tk()

        self.window.title(f'ビジュアルエディタ - {self.recording.name}')
        self.window.geometry('600x800')
        self.window.resizable(True, True)

        # Handle window close
        self.window.protocol('WM_DELETE_WINDOW', self._on_close)

        # Initialize file dialog manager
        self.file_dialog_manager = FileDialogManager(self.window)

    def _setup_ui(self):
        """Set up the user interface."""
        # Main frame
        self.main_frame = ttk.Frame(self.window, padding='10')
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header frame
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Recording info
        info_text = f'操作数: {self.recording.operation_count}  再生時間: {self.recording.duration:.1f}秒'
        ttk.Label(header_frame, text=info_text, font=('Arial', 10)).pack(anchor=tk.W)

        # Instructions
        instructions = ttk.Label(
            header_frame,
            text='• スクリーンショット画像をダブルクリックして領域を編集\n• ブロックをドラッグして順序を変更（未実装）',
            justify=tk.LEFT,
            font=('Arial', 9),
        )
        instructions.pack(anchor=tk.W, pady=(5, 0))

        # Separator
        ttk.Separator(self.main_frame, orient=tk.HORIZONTAL).pack(
            fill=tk.X, pady=(0, 10)
        )

        # Scrollable frame for operation blocks
        self._setup_scrollable_frame()

        # Button frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # Buttons
        ttk.Button(button_frame, text='開く', command=self._on_open, width=15).pack(
            side=tk.LEFT
        )

        ttk.Button(button_frame, text='保存', command=self._on_save, width=15).pack(
            side=tk.RIGHT, padx=(10, 0)
        )

        ttk.Button(button_frame, text='閉じる', command=self._on_close, width=15).pack(
            side=tk.RIGHT
        )

    def _setup_scrollable_frame(self):
        """Set up scrollable frame for operation blocks."""
        # Create frame for canvas and scrollbar
        self.scroll_frame = ttk.Frame(self.main_frame)
        self.scroll_frame.pack(fill=tk.BOTH, expand=True)

        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.scroll_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            self.scroll_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )

        # Configure canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create scrollable frame inside canvas
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor=tk.NW)

        # Bind events for scrolling
        self.scrollable_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)

        # Bind mouse wheel
        self._bind_mousewheel()

    def _on_frame_configure(self, event):
        """Handle frame resize event."""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _on_canvas_configure(self, event):
        """Handle canvas resize event."""
        # Configure the frame width to match canvas width
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas.find_all()[0], width=canvas_width)

    def _bind_mousewheel(self):
        """Bind mouse wheel events for scrolling."""

        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

        def bind_mousewheel(event):
            self.canvas.bind_all('<MouseWheel>', on_mousewheel)

        def unbind_mousewheel(event):
            self.canvas.unbind_all('<MouseWheel>')

        self.canvas.bind('<Enter>', bind_mousewheel)
        self.canvas.bind('<Leave>', unbind_mousewheel)

    def _create_block_widgets(self):
        """Create widgets for all operation blocks."""
        self.block_widgets.clear()

        for i, block in enumerate(self.recording.operations):
            block_widget = OperationBlockWidget(
                self.scrollable_frame, block, on_image_edit=self._on_block_image_edit
            )
            block_widget.pack(fill=tk.X, pady=(0, 10))
            self.block_widgets.append(block_widget)

    def _on_block_image_edit(self, block_widget: OperationBlockWidget):
        """Handle image edit request from block widget."""
        if (
            block_widget.block.operation_type != OperationType.SCREEN_CONDITION
            or not block_widget.block.screen_condition
            or not block_widget.block.screen_condition.image_data
        ):
            return

        # Open image editor
        def on_region_selected(region):
            # Update the screen condition with new region
            block_widget.block.screen_condition.region = region

            # Show confirmation message
            x, y, w, h = region
            messagebox.showinfo(
                '領域更新完了',
                f'選択領域が更新されました。\n座標: ({x}, {y})\nサイズ: {w} x {h}',
                parent=self.window,
            )

        try:
            ImageEditor.open_image_editor(
                self.window,
                block_widget.block.screen_condition.image_data,
                on_confirm=on_region_selected,
            )
        except Exception as e:
            messagebox.showerror(
                'エラー', f'画像エディタを開けませんでした: {e}', parent=self.window
            )

    def _on_save(self):
        """Handle save button click."""
        if self.file_dialog_manager:
            # Generate initial filename based on recording name
            initial_filename = self.recording.name or '新しいマクロ'
            success = self.file_dialog_manager.save_macro(
                self.recording, initial_filename
            )

            if success:
                # Update window title to reflect saved file
                if hasattr(self.file_dialog_manager, 'last_saved_path'):
                    self.window.title(
                        f'ビジュアルエディタ - {self.file_dialog_manager.last_saved_path.name}'
                    )

    def _on_open(self):
        """Handle open button click."""
        if self.file_dialog_manager:
            loaded_recording = self.file_dialog_manager.load_macro()

            if loaded_recording:
                # Update the current recording
                self.recording = loaded_recording

                # Update window title
                self.window.title(f'ビジュアルエディタ - {self.recording.name}')

                # Recreate block widgets with new data
                self._clear_block_widgets()
                self._create_block_widgets()

                # Update header info
                self._update_header_info()

    def _clear_block_widgets(self):
        """Clear all existing block widgets."""
        for widget in self.block_widgets:
            widget.destroy()
        self.block_widgets.clear()

    def _update_header_info(self):
        """Update the header information display."""
        # Find and update the info label
        for child in self.main_frame.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Label) and '操作数:' in subchild.cget(
                        'text'
                    ):
                        info_text = f'操作数: {self.recording.operation_count}  再生時間: {self.recording.duration:.1f}秒'
                        subchild.config(text=info_text)
                        break

    def _on_close(self):
        """Handle close button click."""
        self.window.destroy()

    def show(self):
        """Show the visual editor window."""
        if self.window:
            self.window.deiconify()
            self.window.lift()

            if hasattr(self.window, 'mainloop'):
                self.window.mainloop()

    @staticmethod
    def open_visual_editor(
        recording: MacroRecording, parent: Optional[tk.Widget] = None
    ) -> 'VisualEditor':
        """
        Open visual editor for a macro recording.

        Args:
            recording: Macro recording to edit
            parent: Parent widget (optional)

        Returns:
            VisualEditor instance
        """
        editor = VisualEditor(recording, parent)
        return editor
