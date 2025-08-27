"""
Drag and drop manager for handling block reordering operations.

This module provides core drag-and-drop functionality for reordering operation blocks
in the visual editor with proper event handling and state management.
"""

import tkinter as tk
from typing import Optional, List, Protocol, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class DragState:
    """State information during drag operation."""

    source_widget: tk.Widget
    source_index: int
    target_index: Optional[int] = None
    drag_start_pos: Optional[Tuple[int, int]] = None
    is_dragging: bool = False


class DragDropCallback(Protocol):
    """Protocol for drag and drop completion callbacks."""

    def __call__(self, source_index: int, target_index: int) -> bool:
        """
        Called when drag operation completes.

        Args:
            source_index: Original index of dragged item
            target_index: Target index for drop

        Returns:
            True if operation was successful, False otherwise
        """
        ...


class DragSource(ABC):
    """Abstract interface for draggable widgets."""

    @abstractmethod
    def get_widget(self) -> tk.Widget:
        """Get the underlying tkinter widget."""
        ...

    @abstractmethod
    def get_index(self) -> int:
        """Get the index of this item in the container."""
        ...

    @abstractmethod
    def set_drag_appearance(self, dragging: bool) -> None:
        """Update appearance during drag operation."""
        ...


class DropZone(ABC):
    """Abstract interface for drop target areas."""

    @abstractmethod
    def get_widget(self) -> tk.Widget:
        """Get the underlying tkinter widget."""
        ...

    @abstractmethod
    def get_drop_index(self, y_position: int) -> int:
        """
        Calculate drop index based on y position.

        Args:
            y_position: Y coordinate for drop calculation

        Returns:
            Target index for drop operation
        """
        ...

    @abstractmethod
    def show_drop_indicator(self, index: int) -> None:
        """Show visual indicator at target drop position."""
        ...

    @abstractmethod
    def hide_drop_indicator(self) -> None:
        """Hide drop indicator."""
        ...


class DragDropManager:
    """
    Manager for drag and drop operations on operation blocks.

    Handles all aspects of drag-and-drop including event binding, visual feedback,
    and completion callbacks.
    """

    def __init__(
        self, drop_zone: DropZone, on_reorder: Optional[DragDropCallback] = None
    ):
        """
        Initialize drag drop manager.

        Args:
            drop_zone: Container that can receive dropped items
            on_reorder: Callback for when reorder operation completes
        """
        self.drop_zone = drop_zone
        self.on_reorder = on_reorder
        self.drag_sources: List[DragSource] = []
        self.current_drag: Optional[DragState] = None

        # Minimum distance to start drag operation
        self.drag_threshold = 5

        # Bind events to drop zone
        self._bind_drop_zone_events()

    def register_drag_source(self, drag_source: DragSource) -> None:
        """
        Register a draggable widget.

        Args:
            drag_source: Widget that can be dragged
        """
        if drag_source not in self.drag_sources:
            self.drag_sources.append(drag_source)
            self._bind_drag_events(drag_source)

    def unregister_drag_source(self, drag_source: DragSource) -> None:
        """
        Unregister a draggable widget.

        Args:
            drag_source: Widget to unregister
        """
        if drag_source in self.drag_sources:
            self.drag_sources.remove(drag_source)
            self._unbind_drag_events(drag_source)

    def clear_drag_sources(self) -> None:
        """Remove all registered drag sources."""
        for drag_source in self.drag_sources[:]:
            self.unregister_drag_source(drag_source)

    def _bind_drop_zone_events(self) -> None:
        """Bind events to the drop zone widget."""
        widget = self.drop_zone.get_widget()
        widget.bind('<Motion>', self._on_drop_zone_motion, add=True)
        widget.bind('<ButtonRelease-1>', self._on_drop_zone_release, add=True)

    def _bind_drag_events(self, drag_source: DragSource) -> None:
        """
        Bind drag events to a source widget.

        Args:
            drag_source: Source widget to bind events to
        """
        widget = drag_source.get_widget()
        widget.bind(
            '<Button-1>', lambda e: self._on_drag_start(e, drag_source), add=True
        )
        widget.bind(
            '<B1-Motion>', lambda e: self._on_drag_motion(e, drag_source), add=True
        )
        widget.bind(
            '<ButtonRelease-1>',
            lambda e: self._on_drag_release(e, drag_source),
            add=True,
        )

    def _unbind_drag_events(self, drag_source: DragSource) -> None:
        """
        Unbind drag events from a source widget.

        Args:
            drag_source: Source widget to unbind events from
        """
        # Note: tkinter doesn't provide easy way to unbind specific handlers
        # In practice, this would require more sophisticated event management
        pass

    def _on_drag_start(self, event: tk.Event, drag_source: DragSource) -> None:
        """
        Handle drag start event.

        Args:
            event: Mouse button press event
            drag_source: Widget being dragged
        """
        # Store initial position for threshold check
        if self.current_drag is None:
            self.current_drag = DragState(
                source_widget=drag_source.get_widget(),
                source_index=drag_source.get_index(),
                drag_start_pos=(event.x_root, event.y_root),
                is_dragging=False,
            )

    def _on_drag_motion(self, event: tk.Event, drag_source: DragSource) -> None:
        """
        Handle drag motion event.

        Args:
            event: Mouse motion event
            drag_source: Widget being dragged
        """
        if self.current_drag is None:
            return

        # Check if we've moved enough to start dragging
        if not self.current_drag.is_dragging:
            if self.current_drag.drag_start_pos:
                start_x, start_y = self.current_drag.drag_start_pos
                distance = (
                    (event.x_root - start_x) ** 2 + (event.y_root - start_y) ** 2
                ) ** 0.5

                if distance >= self.drag_threshold:
                    self._start_drag_operation(drag_source)

        if self.current_drag.is_dragging:
            # Update drop target based on current position
            self._update_drop_target(event)

    def _on_drag_release(self, event: tk.Event, drag_source: DragSource) -> None:
        """
        Handle drag release event.

        Args:
            event: Mouse button release event
            drag_source: Widget being dragged
        """
        if self.current_drag and self.current_drag.is_dragging:
            self._complete_drag_operation()
        else:
            # Clean up if drag never started
            self._cancel_drag_operation()

    def _on_drop_zone_motion(self, event: tk.Event) -> None:
        """
        Handle motion over drop zone.

        Args:
            event: Mouse motion event over drop zone
        """
        if self.current_drag and self.current_drag.is_dragging:
            self._update_drop_target(event)

    def _on_drop_zone_release(self, event: tk.Event) -> None:
        """
        Handle release over drop zone.

        Args:
            event: Mouse release event over drop zone
        """
        if self.current_drag and self.current_drag.is_dragging:
            self._complete_drag_operation()

    def _start_drag_operation(self, drag_source: DragSource) -> None:
        """
        Start the drag operation with visual feedback.

        Args:
            drag_source: Source widget being dragged
        """
        if self.current_drag:
            self.current_drag.is_dragging = True
            drag_source.set_drag_appearance(True)

    def _update_drop_target(self, event: tk.Event) -> None:
        """
        Update drop target based on current mouse position.

        Args:
            event: Mouse event with current position
        """
        if not self.current_drag:
            return

        try:
            # Convert to drop zone coordinates
            drop_zone_widget = self.drop_zone.get_widget()
            y_in_zone = (
                drop_zone_widget.winfo_pointery() - drop_zone_widget.winfo_rooty()
            )

            new_target_index = self.drop_zone.get_drop_index(y_in_zone)

            # Update visual feedback if target changed
            if self.current_drag.target_index != new_target_index:
                self.current_drag.target_index = new_target_index
                self.drop_zone.show_drop_indicator(new_target_index)

        except tk.TclError:
            # Handle case where widget is no longer valid
            pass

    def _complete_drag_operation(self) -> None:
        """Complete the drag operation and trigger callback."""
        if not self.current_drag or not self.current_drag.is_dragging:
            self._cancel_drag_operation()
            return

        source_index = self.current_drag.source_index
        target_index = self.current_drag.target_index

        # Clean up visual state
        self._cleanup_drag_state()

        # Execute reorder callback if target is valid
        if (
            target_index is not None
            and target_index != source_index
            and self.on_reorder
        ):
            success = self.on_reorder(source_index, target_index)
            if not success:
                # Could implement rollback visual feedback here
                pass

    def _cancel_drag_operation(self) -> None:
        """Cancel the current drag operation."""
        self._cleanup_drag_state()

    def _cleanup_drag_state(self) -> None:
        """Clean up drag state and visual feedback."""
        if self.current_drag:
            # Find and reset drag source appearance
            for drag_source in self.drag_sources:
                if drag_source.get_widget() == self.current_drag.source_widget:
                    drag_source.set_drag_appearance(False)
                    break

        # Hide drop indicators
        self.drop_zone.hide_drop_indicator()

        # Reset drag state
        self.current_drag = None

    def is_dragging(self) -> bool:
        """
        Check if drag operation is currently in progress.

        Returns:
            True if dragging, False otherwise
        """
        return self.current_drag is not None and self.current_drag.is_dragging

    def cancel_current_drag(self) -> None:
        """Cancel any current drag operation."""
        if self.current_drag:
            self._cancel_drag_operation()
