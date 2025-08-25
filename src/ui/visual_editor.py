"""
Visual editor for GameMacroAssistant with drag-and-drop functionality.

This module provides a visual interface for editing macro operations with
drag-and-drop reordering and undo/redo functionality.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable, Dict, Any
import uuid
from copy import deepcopy

from src.core.macro_data import OperationBlock, OperationType, MacroRecording


class DragDropCanvas(tk.Canvas):
    """Canvas widget with drag-and-drop functionality for operation blocks."""
    
    def __init__(self, parent, **kwargs):
        """Initialize the drag-drop canvas."""
        super().__init__(parent, **kwargs)
        
        # Drag and drop state
        self.drag_data = {"item": None, "x": 0, "y": 0}
        self.drop_indicator = None
        self.blocks = []  # List of visual block items
        self.block_height = 60
        self.block_width = 300
        self.block_spacing = 10
        self.margin = 20
        
        # Bind drag events
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_drop)
        self.bind("<Motion>", self._on_motion)
        
        # Configure scrollable area
        self.configure(scrollregion=(0, 0, 400, 600))
        
    def add_block(self, operation: OperationBlock, index: Optional[int] = None):
        """Add a new operation block to the canvas."""
        if index is None:
            index = len(self.blocks)
        
        y_pos = self.margin + index * (self.block_height + self.block_spacing)
        
        # Create block rectangle
        block_rect = self.create_rectangle(
            self.margin, y_pos,
            self.margin + self.block_width, y_pos + self.block_height,
            fill="#f0f0f0", outline="#888888", width=2,
            tags=("block", f"block_{operation.id}")
        )
        
        # Create block text
        text_content = self._get_block_text(operation)
        block_text = self.create_text(
            self.margin + 10, y_pos + 10,
            text=text_content,
            anchor="nw",
            font=("Arial", 9),
            width=self.block_width - 20,
            tags=("block", f"block_{operation.id}")
        )
        
        # Store block data
        block_data = {
            "operation": operation,
            "rect": block_rect,
            "text": block_text,
            "index": index
        }
        
        if index == len(self.blocks):
            self.blocks.append(block_data)
        else:
            self.blocks.insert(index, block_data)
            self._update_indices()
        
        self._update_scroll_region()
        
    def _get_block_text(self, operation: OperationBlock) -> str:
        """Generate display text for an operation block."""
        if operation.operation_type == OperationType.MOUSE_CLICK:
            if operation.mouse_op:
                return f"マウスクリック: {operation.mouse_op.button.value}\n位置: ({operation.mouse_op.position.x}, {operation.mouse_op.position.y})"
        elif operation.operation_type == OperationType.KEY_PRESS:
            if operation.keyboard_op:
                modifiers = "+".join(operation.keyboard_op.modifiers) + "+" if operation.keyboard_op.modifiers else ""
                return f"キー押下: {modifiers}{operation.keyboard_op.key}"
        elif operation.operation_type == OperationType.SCREEN_CONDITION:
            return "画面条件チェック\n(画像マッチング)"
        elif operation.operation_type == OperationType.WAIT:
            return f"待機: {operation.delay_after:.1f}秒"
        
        return f"操作: {operation.operation_type.value}"
    
    def _update_indices(self):
        """Update the index values for all blocks."""
        for i, block in enumerate(self.blocks):
            block["index"] = i
    
    def _update_scroll_region(self):
        """Update the scrollable region based on content."""
        if self.blocks:
            height = self.margin * 2 + len(self.blocks) * (self.block_height + self.block_spacing)
        else:
            height = 200
        self.configure(scrollregion=(0, 0, self.block_width + self.margin * 2, height))
    
    def _on_click(self, event):
        """Handle mouse click to start drag operation."""
        item = self.find_closest(event.x, event.y)[0]
        tags = self.gettags(item)
        
        # Check if clicked on a block
        if "block" in tags:
            block_tag = [tag for tag in tags if tag.startswith("block_")]
            if block_tag:
                operation_id = block_tag[0][6:]  # Remove "block_" prefix
                
                # Find the block data
                for block in self.blocks:
                    if block["operation"].id == operation_id:
                        self.drag_data["item"] = block
                        self.drag_data["x"] = event.x
                        self.drag_data["y"] = event.y
                        
                        # Highlight the dragged block
                        self.itemconfig(block["rect"], fill="#e0e0ff")
                        break
    
    def _on_drag(self, event):
        """Handle drag motion."""
        if self.drag_data["item"]:
            # Calculate movement delta
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            
            # Move the block visually
            block = self.drag_data["item"]
            self.move(block["rect"], dx, dy)
            self.move(block["text"], dx, dy)
            
            # Update drag position
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            
            # Show drop indicator
            self._update_drop_indicator(event.y)
    
    def _on_motion(self, event):
        """Handle mouse motion for visual feedback."""
        if self.drag_data["item"]:
            self._update_drop_indicator(event.y)
    
    def _update_drop_indicator(self, y_pos):
        """Update the visual drop indicator."""
        if self.drop_indicator:
            self.delete(self.drop_indicator)
        
        # Calculate target index based on y position
        target_index = max(0, min(len(self.blocks), 
                                 int((y_pos - self.margin + self.block_spacing // 2) // 
                                     (self.block_height + self.block_spacing))))
        
        # Draw drop indicator line
        indicator_y = self.margin + target_index * (self.block_height + self.block_spacing) - 5
        self.drop_indicator = self.create_line(
            self.margin, indicator_y,
            self.margin + self.block_width, indicator_y,
            fill="red", width=3, tags="drop_indicator"
        )
    
    def _on_drop(self, event):
        """Handle drop operation to reorder blocks."""
        if self.drag_data["item"]:
            block = self.drag_data["item"]
            
            # Calculate target index
            target_index = max(0, min(len(self.blocks), 
                                     int((event.y - self.margin + self.block_spacing // 2) // 
                                         (self.block_height + self.block_spacing))))
            
            # Perform the reorder
            current_index = block["index"]
            if target_index != current_index and target_index != current_index + 1:
                self._reorder_block(current_index, target_index)
            else:
                # Just reset the position if no actual move
                self._redraw_all_blocks()
            
            # Reset drag state
            self.drag_data = {"item": None, "x": 0, "y": 0}
            
            # Clean up visual indicators
            if self.drop_indicator:
                self.delete(self.drop_indicator)
                self.drop_indicator = None
    
    def _reorder_block(self, from_index: int, to_index: int):
        """Reorder blocks and redraw."""
        # Adjust target index if moving down
        if to_index > from_index:
            to_index -= 1
        
        # Move the block in the list
        block = self.blocks.pop(from_index)
        self.blocks.insert(to_index, block)
        
        # Redraw all blocks
        self._redraw_all_blocks()
        
        # Update indices
        self._update_indices()
        
        # Notify parent of the change
        if hasattr(self.master, '_on_blocks_reordered'):
            self.master._on_blocks_reordered(from_index, to_index)
    
    def _redraw_all_blocks(self):
        """Redraw all blocks in their correct positions."""
        # Clear all blocks
        self.delete("block")
        
        # Redraw blocks
        for i, block_data in enumerate(self.blocks):
            y_pos = self.margin + i * (self.block_height + self.block_spacing)
            
            # Recreate rectangle
            block_data["rect"] = self.create_rectangle(
                self.margin, y_pos,
                self.margin + self.block_width, y_pos + self.block_height,
                fill="#f0f0f0", outline="#888888", width=2,
                tags=("block", f"block_{block_data['operation'].id}")
            )
            
            # Recreate text
            text_content = self._get_block_text(block_data["operation"])
            block_data["text"] = self.create_text(
                self.margin + 10, y_pos + 10,
                text=text_content,
                anchor="nw",
                font=("Arial", 9),
                width=self.block_width - 20,
                tags=("block", f"block_{block_data['operation'].id}")
            )
        
        self._update_scroll_region()
    
    def get_ordered_operations(self) -> List[OperationBlock]:
        """Get the current ordered list of operations."""
        return [block["operation"] for block in self.blocks]
    
    def clear_blocks(self):
        """Clear all blocks from the canvas."""
        self.delete("all")
        self.blocks.clear()
        self._update_scroll_region()


class UndoRedoManager:
    """Manages undo/redo operations for the visual editor."""
    
    def __init__(self, max_history: int = 10):
        """Initialize with maximum history size."""
        self.max_history = max_history
        self.history: List[List[OperationBlock]] = []
        self.current_index = -1
    
    def save_state(self, operations: List[OperationBlock]):
        """Save current state to history."""
        # Remove any redo history if we're not at the end
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        # Add new state
        self.history.append(deepcopy(operations))
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
        else:
            self.current_index += 1
    
    def undo(self) -> Optional[List[OperationBlock]]:
        """Undo to previous state."""
        if self.current_index > 0:
            self.current_index -= 1
            return deepcopy(self.history[self.current_index])
        return None
    
    def redo(self) -> Optional[List[OperationBlock]]:
        """Redo to next state."""
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return deepcopy(self.history[self.current_index])
        return None
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return self.current_index > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return self.current_index < len(self.history) - 1


class VisualEditor:
    """Visual editor for macro operations with drag-and-drop functionality."""
    
    def __init__(self, root: Optional[tk.Tk] = None):
        """Initialize the visual editor."""
        self.root = root if root else tk.Toplevel()
        self.root.title("GameMacroAssistant - ビジュアルエディタ")
        self.root.geometry("500x700")
        
        # Current macro data
        self.macro_recording: Optional[MacroRecording] = None
        self.undo_manager = UndoRedoManager()
        
        # Callbacks
        self.on_macro_changed: Optional[Callable[[MacroRecording], None]] = None
        
        self._setup_ui()
        self._setup_keyboard_shortcuts()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="マクロ操作ブロック", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Toolbar frame
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Undo/Redo buttons
        self.undo_button = ttk.Button(toolbar_frame, text="元に戻す (Ctrl+Z)", command=self._undo, state="disabled")
        self.undo_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.redo_button = ttk.Button(toolbar_frame, text="やり直し (Ctrl+Y)", command=self._redo, state="disabled")
        self.redo_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(toolbar_frame, text="操作をドラッグ&ドロップで並び替えできます")
        self.status_label.pack(side=tk.RIGHT)
        
        # Canvas frame with scrollbar
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas with scrollbar
        self.canvas = DragDropCanvas(canvas_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind canvas events
        self.canvas.master = self  # Allow canvas to call back to editor
    
    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts."""
        self.root.bind("<Control-z>", lambda e: self._undo())
        self.root.bind("<Control-Z>", lambda e: self._undo())
        self.root.bind("<Control-y>", lambda e: self._redo())
        self.root.bind("<Control-Y>", lambda e: self._redo())
        self.root.bind("<Control-Shift-Z>", lambda e: self._redo())
        
        # Make sure the window can receive key events
        self.root.focus_set()
    
    def load_macro(self, macro: MacroRecording):
        """Load a macro recording into the editor."""
        self.macro_recording = macro
        
        # Clear existing blocks
        self.canvas.clear_blocks()
        
        # Add operation blocks
        for operation in macro.operations:
            self.canvas.add_block(operation)
        
        # Save initial state for undo
        self.undo_manager.save_state(macro.operations)
        self._update_undo_redo_buttons()
    
    def get_current_macro(self) -> Optional[MacroRecording]:
        """Get the current macro with reordered operations."""
        if not self.macro_recording:
            return None
        
        ordered_operations = self.canvas.get_ordered_operations()
        
        # Create new macro with reordered operations
        new_macro = MacroRecording(
            name=self.macro_recording.name,
            created_at=self.macro_recording.created_at,
            operations=ordered_operations,
            metadata=self.macro_recording.metadata.copy()
        )
        
        return new_macro
    
    def _on_blocks_reordered(self, from_index: int, to_index: int):
        """Handle block reordering event from canvas."""
        if self.macro_recording:
            # Get current state
            ordered_operations = self.canvas.get_ordered_operations()
            
            # Save to undo history
            self.undo_manager.save_state(ordered_operations)
            self._update_undo_redo_buttons()
            
            # Update macro recording
            self.macro_recording.operations = ordered_operations
            
            # Notify callback
            if self.on_macro_changed:
                self.on_macro_changed(self.macro_recording)
            
            self.status_label.config(text=f"ブロックを移動しました: {from_index + 1} → {to_index + 1}")
    
    def _undo(self):
        """Perform undo operation."""
        previous_state = self.undo_manager.undo()
        if previous_state and self.macro_recording:
            # Update macro
            self.macro_recording.operations = previous_state
            
            # Reload canvas
            self.canvas.clear_blocks()
            for operation in previous_state:
                self.canvas.add_block(operation)
            
            # Update UI
            self._update_undo_redo_buttons()
            self.status_label.config(text="操作を元に戻しました")
            
            # Notify callback
            if self.on_macro_changed:
                self.on_macro_changed(self.macro_recording)
    
    def _redo(self):
        """Perform redo operation."""
        next_state = self.undo_manager.redo()
        if next_state and self.macro_recording:
            # Update macro
            self.macro_recording.operations = next_state
            
            # Reload canvas
            self.canvas.clear_blocks()
            for operation in next_state:
                self.canvas.add_block(operation)
            
            # Update UI
            self._update_undo_redo_buttons()
            self.status_label.config(text="操作をやり直しました")
            
            # Notify callback
            if self.on_macro_changed:
                self.on_macro_changed(self.macro_recording)
    
    def _update_undo_redo_buttons(self):
        """Update undo/redo button states."""
        if self.undo_manager.can_undo():
            self.undo_button.config(state="normal")
        else:
            self.undo_button.config(state="disabled")
        
        if self.undo_manager.can_redo():
            self.redo_button.config(state="normal")
        else:
            self.redo_button.config(state="disabled")
    
    def show(self):
        """Show the visual editor window."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_set()
    
    def hide(self):
        """Hide the visual editor window."""
        self.root.withdraw()