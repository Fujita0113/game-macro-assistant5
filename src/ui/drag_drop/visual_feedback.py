"""
Visual feedback system for drag and drop operations.

This module provides visual indicators during drag-and-drop operations including
drop zones, drag ghosts, and highlight effects.
"""

import tkinter as tk
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class DropIndicatorConfig:
    """Configuration for drop indicator appearance."""

    height: int = 3
    color: str = '#4285f4'  # Google Blue
    highlight_color: str = '#1565c0'  # Darker blue
    margin: int = 5


class DropIndicator:
    """Visual indicator showing where an item will be dropped."""

    def __init__(self, parent: tk.Widget, config: Optional[DropIndicatorConfig] = None):
        """
        Initialize drop indicator.

        Args:
            parent: Parent widget to contain the indicator
            config: Configuration for indicator appearance
        """
        self.parent = parent
        self.config = config or DropIndicatorConfig()
        self.indicator_frame: Optional[tk.Frame] = None
        self.is_visible = False

    def show(self, index: int, total_items: int) -> None:
        """
        Show drop indicator at specified position.

        Args:
            index: Index position to show indicator
            total_items: Total number of items in container
        """
        self.hide()  # Clear any existing indicator

        # Create indicator frame
        self.indicator_frame = tk.Frame(
            self.parent, height=self.config.height, bg=self.config.color, relief=tk.FLAT
        )

        # Calculate position in the parent's grid/pack layout
        if index == 0:
            # Insert at beginning
            self.indicator_frame.pack(
                fill=tk.X,
                padx=self.config.margin,
                pady=(0, self.config.margin),
                before=self._get_child_at_index(0),
            )
        elif index >= total_items:
            # Insert at end
            self.indicator_frame.pack(
                fill=tk.X, padx=self.config.margin, pady=(self.config.margin, 0)
            )
        else:
            # Insert between items
            before_widget = self._get_child_at_index(index)
            if before_widget:
                self.indicator_frame.pack(
                    fill=tk.X,
                    padx=self.config.margin,
                    pady=self.config.margin,
                    before=before_widget,
                )

        self.is_visible = True

    def hide(self) -> None:
        """Hide the drop indicator."""
        if self.indicator_frame:
            self.indicator_frame.destroy()
            self.indicator_frame = None
        self.is_visible = False

    def _get_child_at_index(self, index: int) -> Optional[tk.Widget]:
        """
        Get child widget at specified index.

        Args:
            index: Index of child to retrieve

        Returns:
            Child widget or None if index is out of range
        """
        children = list(self.parent.winfo_children())
        if 0 <= index < len(children):
            return children[index]
        return None


@dataclass
class DragGhostConfig:
    """Configuration for drag ghost appearance."""

    opacity: float = 0.7
    border_color: str = '#4285f4'
    border_width: int = 2
    background_color: str = '#f0f0f0'
    text_color: str = '#666666'


class DragGhost:
    """Semi-transparent ghost image that follows cursor during drag."""

    def __init__(self, config: Optional[DragGhostConfig] = None):
        """
        Initialize drag ghost.

        Args:
            config: Configuration for ghost appearance
        """
        self.config = config or DragGhostConfig()
        self.ghost_window: Optional[tk.Toplevel] = None
        self.is_visible = False

    def show(self, source_widget: tk.Widget, cursor_pos: Tuple[int, int]) -> None:
        """
        Show drag ghost at cursor position.

        Args:
            source_widget: Widget being dragged (for appearance reference)
            cursor_pos: Current cursor position (x, y)
        """
        self.hide()  # Clear any existing ghost

        # Create toplevel window for ghost
        self.ghost_window = tk.Toplevel()
        self.ghost_window.wm_overrideredirect(True)
        self.ghost_window.attributes('-topmost', True)

        # Make window semi-transparent
        try:
            self.ghost_window.attributes('-alpha', self.config.opacity)
        except tk.TclError:
            # Fallback for systems that don't support transparency
            pass

        # Create ghost content similar to source widget
        ghost_frame = tk.Frame(
            self.ghost_window,
            bg=self.config.background_color,
            relief=tk.SOLID,
            bd=self.config.border_width,
        )
        ghost_frame.pack(fill=tk.BOTH, expand=True)

        # Add simplified content
        ghost_label = tk.Label(
            ghost_frame,
            text='移動中...',
            bg=self.config.background_color,
            fg=self.config.text_color,
            font=('Arial', 9),
        )
        ghost_label.pack(padx=10, pady=5)

        # Position at cursor
        self.update_position(cursor_pos)
        self.is_visible = True

    def hide(self) -> None:
        """Hide the drag ghost."""
        if self.ghost_window:
            self.ghost_window.destroy()
            self.ghost_window = None
        self.is_visible = False

    def update_position(self, cursor_pos: Tuple[int, int]) -> None:
        """
        Update ghost position to follow cursor.

        Args:
            cursor_pos: Current cursor position (x, y)
        """
        if self.ghost_window and self.is_visible:
            x, y = cursor_pos
            # Offset slightly to avoid covering cursor
            self.ghost_window.wm_geometry(f'+{x + 10}+{y - 10}')


@dataclass
class BlockHighlightConfig:
    """Configuration for block highlighting during drag."""

    drag_color: str = '#e3f2fd'  # Light blue
    target_color: str = '#fff3e0'  # Light orange
    original_color: str = '#ffffff'  # White
    border_drag: str = '#2196f3'  # Blue
    border_target: str = '#ff9800'  # Orange


class BlockHighlight:
    """Manages highlighting of blocks during drag operations."""

    def __init__(self, config: Optional[BlockHighlightConfig] = None):
        """
        Initialize block highlight manager.

        Args:
            config: Configuration for highlight appearance
        """
        self.config = config or BlockHighlightConfig()
        self.highlighted_widgets: Dict[tk.Widget, Dict[str, Any]] = {}

    def highlight_as_dragging(self, widget: tk.Widget) -> None:
        """
        Highlight widget as currently being dragged.

        Args:
            widget: Widget to highlight
        """
        if widget not in self.highlighted_widgets:
            # Store original appearance
            self.highlighted_widgets[widget] = {
                'bg': widget.cget('bg') if hasattr(widget, 'cget') else None,
                'relief': widget.cget('relief') if hasattr(widget, 'cget') else None,
                'bd': widget.cget('bd') if hasattr(widget, 'cget') else None,
            }

        # Apply drag highlighting
        try:
            widget.configure(bg=self.config.drag_color, relief=tk.SOLID, bd=2)
        except tk.TclError:
            # Handle widgets that don't support these options
            pass

    def highlight_as_target(self, widget: tk.Widget) -> None:
        """
        Highlight widget as potential drop target.

        Args:
            widget: Widget to highlight
        """
        if widget not in self.highlighted_widgets:
            # Store original appearance
            self.highlighted_widgets[widget] = {
                'bg': widget.cget('bg') if hasattr(widget, 'cget') else None,
                'relief': widget.cget('relief') if hasattr(widget, 'cget') else None,
                'bd': widget.cget('bd') if hasattr(widget, 'cget') else None,
            }

        # Apply target highlighting
        try:
            widget.configure(bg=self.config.target_color, relief=tk.SOLID, bd=2)
        except tk.TclError:
            # Handle widgets that don't support these options
            pass

    def remove_highlight(self, widget: tk.Widget) -> None:
        """
        Remove highlighting from widget.

        Args:
            widget: Widget to restore original appearance
        """
        if widget in self.highlighted_widgets:
            original = self.highlighted_widgets[widget]

            # Restore original appearance
            try:
                if original['bg'] is not None:
                    widget.configure(bg=original['bg'])
                if original['relief'] is not None:
                    widget.configure(relief=original['relief'])
                if original['bd'] is not None:
                    widget.configure(bd=original['bd'])
            except tk.TclError:
                # Handle widgets that don't support these options
                pass

            del self.highlighted_widgets[widget]

    def clear_all_highlights(self) -> None:
        """Remove all highlights and restore original appearances."""
        for widget in list(self.highlighted_widgets.keys()):
            self.remove_highlight(widget)


class VisualFeedbackManager:
    """
    Central manager for all visual feedback during drag-and-drop operations.

    Coordinates drop indicators, drag ghosts, and block highlighting to provide
    comprehensive visual feedback to users.
    """

    def __init__(self, parent: tk.Widget):
        """
        Initialize visual feedback manager.

        Args:
            parent: Parent widget for creating visual elements
        """
        self.parent = parent
        self.drop_indicator = DropIndicator(parent)
        self.drag_ghost = DragGhost()
        self.block_highlight = BlockHighlight()

    def start_drag_feedback(
        self, source_widget: tk.Widget, cursor_pos: Tuple[int, int]
    ) -> None:
        """
        Start visual feedback for drag operation.

        Args:
            source_widget: Widget being dragged
            cursor_pos: Current cursor position
        """
        self.block_highlight.highlight_as_dragging(source_widget)
        self.drag_ghost.show(source_widget, cursor_pos)

    def update_drag_feedback(self, cursor_pos: Tuple[int, int]) -> None:
        """
        Update visual feedback during drag.

        Args:
            cursor_pos: Current cursor position
        """
        self.drag_ghost.update_position(cursor_pos)

    def show_drop_target(self, index: int, total_items: int) -> None:
        """
        Show drop target indicator.

        Args:
            index: Target index for drop
            total_items: Total number of items
        """
        self.drop_indicator.show(index, total_items)

    def hide_drop_target(self) -> None:
        """Hide drop target indicator."""
        self.drop_indicator.hide()

    def end_drag_feedback(self) -> None:
        """End all visual feedback for drag operation."""
        self.drag_ghost.hide()
        self.drop_indicator.hide()
        self.block_highlight.clear_all_highlights()

    def highlight_target_widget(self, widget: tk.Widget) -> None:
        """
        Highlight a widget as potential target.

        Args:
            widget: Widget to highlight
        """
        self.block_highlight.highlight_as_target(widget)

    def remove_target_highlight(self, widget: tk.Widget) -> None:
        """
        Remove target highlight from widget.

        Args:
            widget: Widget to unhighlight
        """
        self.block_highlight.remove_highlight(widget)
