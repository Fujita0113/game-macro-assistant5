"""
Draggable block widget for operation blocks in the visual editor.

This module provides an enhanced operation block widget that implements
drag-and-drop functionality with visual feedback.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
from PIL import Image, ImageTk
import io

from ...core.macro_data import OperationBlock, OperationType
from ..drag_drop.drag_drop_manager import DragSource


class DraggableBlockWidget(DragSource):
    """
    Enhanced operation block widget with drag-and-drop support.

    This widget extends the basic operation block display with dragging capabilities
    and improved visual feedback during interactions.
    """

    def __init__(
        self,
        parent: tk.Widget,
        block: OperationBlock,
        index: int,
        on_image_edit: Optional[Callable[['DraggableBlockWidget'], None]] = None,
        on_drag_start: Optional[Callable[['DraggableBlockWidget'], None]] = None,
        on_selection_change: Optional[
            Callable[['DraggableBlockWidget', bool], None]
        ] = None,
    ):
        """
        Initialize draggable block widget.

        Args:
            parent: Parent widget
            block: Operation block data
            index: Index of this block in the container
            on_image_edit: Callback for image editing requests
            on_drag_start: Callback when drag operation starts
            on_selection_change: Callback when selection state changes
        """
        self.parent = parent
        self.block = block
        self.index = index
        self.on_image_edit = on_image_edit
        self.on_drag_start = on_drag_start
        self.on_selection_change = on_selection_change

        # Widget state
        self.is_selected = False
        self.is_dragging = False
        self.original_bg_color = None
        self.drag_handle: Optional[tk.Widget] = None

        # Create main frame with enhanced styling
        self.frame = ttk.LabelFrame(
            parent,
            text=self._get_block_title(),
            padding='12',
            style='Block.TLabelFrame',
        )

        # Configure custom style if not already done
        self._configure_styles()

        # Create content
        self._setup_content()
        self._setup_drag_handle()

        # Bind selection events
        self._bind_selection_events()

    def _configure_styles(self) -> None:
        """Configure custom TTK styles for the widget."""
        style = ttk.Style()

        # Configure block style
        if 'Block.TLabelFrame' not in style.theme_names():
            style.configure(
                'Block.TLabelFrame', borderwidth=1, relief='solid', background='#ffffff'
            )

        # Configure drag handle style
        if 'DragHandle.TLabel' not in style.theme_names():
            style.configure(
                'DragHandle.TLabel',
                background='#f5f5f5',
                foreground='#666666',
                font=('Arial', 8, 'bold'),
                anchor='center',
            )

        # Configure selected style
        if 'Selected.TLabelFrame' not in style.theme_names():
            style.configure(
                'Selected.TLabelFrame',
                borderwidth=2,
                relief='solid',
                background='#e3f2fd',
            )

        # Configure dragging style
        if 'Dragging.TLabelFrame' not in style.theme_names():
            style.configure(
                'Dragging.TLabelFrame',
                borderwidth=2,
                relief='solid',
                background='#f3e5f5',
            )

    def _get_block_title(self) -> str:
        """Get display title for this block."""
        type_map = {
            OperationType.MOUSE_CLICK: '🖱️ マウスクリック',
            OperationType.MOUSE_MOVE: '🖱️ マウス移動',
            OperationType.KEY_PRESS: '⌨️ キー押下',
            OperationType.KEY_RELEASE: '⌨️ キー離す',
            OperationType.WAIT: '⏱️ 待機',
            OperationType.SCREEN_CONDITION: '📸 画面条件',
        }
        base_title = type_map.get(self.block.operation_type, '❓ 不明な操作')
        return f'{self.index + 1:02d}. {base_title}'

    def _setup_content(self) -> None:
        """Set up block content based on operation type."""
        # Main content container
        content_frame = ttk.Frame(self.frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Create content based on operation type
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
            # Default content for other operation types
            self._setup_default_content(content_frame)

        # Add timing information
        self._add_timing_info(content_frame)

    def _setup_drag_handle(self) -> None:
        """Set up drag handle for easy dragging."""
        handle_frame = ttk.Frame(self.frame)
        handle_frame.pack(fill=tk.X, pady=(0, 5))

        self.drag_handle = ttk.Label(
            handle_frame,
            text='⋮⋮⋮ ドラッグして移動',
            style='DragHandle.TLabel',
            cursor='hand2',
        )
        self.drag_handle.pack(fill=tk.X)

        # Make the entire frame draggable, but highlight the handle
        self._bind_drag_events()

    def _setup_mouse_content(self, parent: tk.Widget) -> None:
        """Set up content for mouse operation."""
        if not self.block.mouse_op:
            return

        mouse_op = self.block.mouse_op

        # Create info frame
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=2)

        # Mouse button info
        button_label = ttk.Label(info_frame, text='ボタン:', font=('Arial', 9, 'bold'))
        button_label.pack(side=tk.LEFT)

        button_value = ttk.Label(
            info_frame, text=f'{mouse_op.button.value}', font=('Arial', 9)
        )
        button_value.pack(side=tk.LEFT, padx=(5, 15))

        # Position info
        pos_label = ttk.Label(info_frame, text='座標:', font=('Arial', 9, 'bold'))
        pos_label.pack(side=tk.LEFT)

        pos_value = ttk.Label(
            info_frame,
            text=f'({mouse_op.position.x}, {mouse_op.position.y})',
            font=('Arial', 9),
        )
        pos_value.pack(side=tk.LEFT, padx=(5, 0))

    def _setup_keyboard_content(self, parent: tk.Widget) -> None:
        """Set up content for keyboard operation."""
        if not self.block.keyboard_op:
            return

        keyboard_op = self.block.keyboard_op

        # Create info frame
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=2)

        # Key combination
        modifiers_text = (
            ' + '.join(keyboard_op.modifiers) if keyboard_op.modifiers else ''
        )
        key_text = (
            f'{modifiers_text} + {keyboard_op.key}'
            if modifiers_text
            else keyboard_op.key
        )

        key_label = ttk.Label(info_frame, text='キー:', font=('Arial', 9, 'bold'))
        key_label.pack(side=tk.LEFT)

        key_value = ttk.Label(
            info_frame,
            text=key_text,
            font=('Arial', 9, 'italic'),
            background='#f0f0f0',
            relief=tk.RAISED,
            padding=(4, 2),
        )
        key_value.pack(side=tk.LEFT, padx=(5, 15))

        # Action info
        action_label = ttk.Label(
            info_frame, text='アクション:', font=('Arial', 9, 'bold')
        )
        action_label.pack(side=tk.LEFT)

        action_value = ttk.Label(info_frame, text=keyboard_op.action, font=('Arial', 9))
        action_value.pack(side=tk.LEFT, padx=(5, 0))

    def _setup_screen_condition_content(self, parent: tk.Widget) -> None:
        """Set up content for screen condition operation."""
        if not self.block.screen_condition:
            return

        screen_condition = self.block.screen_condition

        # Create content container
        content_container = ttk.Frame(parent)
        content_container.pack(fill=tk.BOTH, expand=True, pady=2)

        # Image display if available
        if screen_condition.image_data:
            self._create_image_display(content_container, screen_condition.image_data)

        # Condition details
        self._create_condition_details(content_container, screen_condition)

    def _create_image_display(self, parent: tk.Widget, image_data: bytes) -> None:
        """Create image display with edit functionality."""
        try:
            # Load and resize image for display
            image = Image.open(io.BytesIO(image_data))

            # Calculate display size (maintain aspect ratio)
            display_width = 120
            aspect_ratio = image.height / image.width
            display_height = int(display_width * aspect_ratio)
            display_height = min(display_height, 80)  # Cap height

            # Resize image
            image_resized = image.resize(
                (display_width, display_height), Image.Resampling.LANCZOS
            )

            # Convert to PhotoImage
            self.photo = ImageTk.PhotoImage(image_resized)

            # Create image frame
            image_frame = ttk.Frame(parent)
            image_frame.pack(side=tk.LEFT, padx=(0, 10))

            # Create image label with click handling
            self.image_label = tk.Label(
                image_frame, image=self.photo, cursor='hand2', relief=tk.RAISED, bd=1
            )
            self.image_label.pack()

            # Bind double-click event
            self.image_label.bind('<Double-Button-1>', self._on_image_double_click)

            # Add edit hint
            hint_label = ttk.Label(
                image_frame,
                text='ダブルクリックで編集',
                font=('Arial', 7),
                foreground='#666666',
            )
            hint_label.pack(pady=(2, 0))

        except Exception as e:
            # Fallback if image loading fails
            error_label = ttk.Label(
                parent,
                text=f'画像読み込みエラー: {str(e)[:30]}...',
                font=('Arial', 8),
                foreground='red',
            )
            error_label.pack(side=tk.LEFT)

    def _create_condition_details(self, parent: tk.Widget, screen_condition) -> None:
        """Create condition details display."""
        details_frame = ttk.Frame(parent)
        details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Region info
        region_text = (
            '全画面'
            if not screen_condition.region
            else f'領域: {screen_condition.region[2]}×{screen_condition.region[3]} at ({screen_condition.region[0]}, {screen_condition.region[1]})'
        )

        region_label = ttk.Label(
            details_frame, text=region_text, font=('Arial', 8), wraplength=200
        )
        region_label.pack(anchor=tk.W, pady=1)

        # Threshold info
        threshold_label = ttk.Label(
            details_frame,
            text=f'一致閾値: {screen_condition.threshold:.1%}',
            font=('Arial', 8),
        )
        threshold_label.pack(anchor=tk.W, pady=1)

        # Timeout info
        timeout_label = ttk.Label(
            details_frame,
            text=f'タイムアウト: {screen_condition.timeout}秒',
            font=('Arial', 8),
        )
        timeout_label.pack(anchor=tk.W, pady=1)

    def _setup_default_content(self, parent: tk.Widget) -> None:
        """Set up default content for other operation types."""
        info_label = ttk.Label(
            parent, text=f'操作ID: {self.block.id}', font=('Arial', 9)
        )
        info_label.pack(anchor=tk.W, pady=2)

        if hasattr(self.block, 'delay_after') and self.block.delay_after > 0:
            delay_label = ttk.Label(
                parent,
                text=f'待機時間: {self.block.delay_after:.1f}秒',
                font=('Arial', 9),
            )
            delay_label.pack(anchor=tk.W, pady=1)

    def _add_timing_info(self, parent: tk.Widget) -> None:
        """Add timing information display."""
        if hasattr(self.block, 'timestamp'):
            import datetime

            timestamp = datetime.datetime.fromtimestamp(self.block.timestamp)

            timing_frame = ttk.Frame(parent)
            timing_frame.pack(fill=tk.X, pady=(5, 0))

            ttk.Separator(timing_frame, orient=tk.HORIZONTAL).pack(
                fill=tk.X, pady=(0, 2)
            )

            time_label = ttk.Label(
                timing_frame,
                text=f'記録時刻: {timestamp.strftime("%H:%M:%S.%f")[:-3]}',
                font=('Arial', 7),
                foreground='#666666',
            )
            time_label.pack(anchor=tk.W)

    def _bind_selection_events(self) -> None:
        """Bind events for selection handling."""

        # Bind click events to the frame and its children
        def bind_recursive(widget):
            widget.bind('<Button-1>', self._on_click, add=True)
            for child in widget.winfo_children():
                bind_recursive(child)

        bind_recursive(self.frame)

    def _bind_drag_events(self) -> None:
        """Bind drag-related events."""
        # These events will be handled by the DragDropManager
        # We just need to make sure the widget is properly configured
        pass

    def _on_click(self, event: tk.Event) -> None:
        """Handle click events for selection."""
        # Toggle selection state
        self.set_selected(not self.is_selected)

        # Prevent event propagation to parent
        return 'break'

    def _on_image_double_click(self, event: tk.Event) -> None:
        """Handle double-click on screenshot image."""
        if self.on_image_edit:
            self.on_image_edit(self)

        # Prevent event propagation
        return 'break'

    # DragSource interface implementation

    def get_widget(self) -> tk.Widget:
        """Get the underlying tkinter widget."""
        return self.frame

    def get_index(self) -> int:
        """Get the index of this item in the container."""
        return self.index

    def set_index(self, new_index: int) -> None:
        """Update the index of this widget."""
        self.index = new_index
        # Update the title to reflect new position
        self.frame.configure(text=self._get_block_title())

    def set_drag_appearance(self, dragging: bool) -> None:
        """Update appearance during drag operation."""
        self.is_dragging = dragging

        if dragging:
            self.frame.configure(style='Dragging.TLabelFrame')
            if self.drag_handle:
                self.drag_handle.configure(text='移動中...')
        else:
            # Restore normal or selected appearance
            if self.is_selected:
                self.frame.configure(style='Selected.TLabelFrame')
            else:
                self.frame.configure(style='Block.TLabelFrame')

            if self.drag_handle:
                self.drag_handle.configure(text='⋮⋮⋮ ドラッグして移動')

    # Selection management

    def set_selected(self, selected: bool) -> None:
        """
        Set selection state of the widget.

        Args:
            selected: True to select, False to deselect
        """
        if self.is_selected == selected:
            return

        self.is_selected = selected

        # Update visual appearance
        if selected and not self.is_dragging:
            self.frame.configure(style='Selected.TLabelFrame')
        elif not self.is_dragging:
            self.frame.configure(style='Block.TLabelFrame')

        # Notify callback
        if self.on_selection_change:
            self.on_selection_change(self, selected)

    def is_selected_widget(self) -> bool:
        """
        Check if widget is currently selected.

        Returns:
            True if selected, False otherwise
        """
        return self.is_selected

    # Widget lifecycle

    def pack(self, **kwargs) -> None:
        """Pack the block widget."""
        self.frame.pack(**kwargs)

    def destroy(self) -> None:
        """Destroy the block widget and clean up resources."""
        # Clean up any references
        if hasattr(self, 'photo'):
            delattr(self, 'photo')

        self.frame.destroy()
