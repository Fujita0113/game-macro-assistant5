"""
Unit tests for visual editor drag-and-drop functionality.
"""

import pytest
import tkinter as tk
import time
from unittest.mock import Mock, patch

from src.ui.visual_editor import VisualEditor, UndoRedoManager, DragDropCanvas
from src.core.macro_data import (
    MacroRecording, OperationBlock, OperationType,
    create_mouse_click_operation, create_key_operation,
    MouseButton, Position
)


class TestUndoRedoManager:
    """Test undo/redo functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = UndoRedoManager(max_history=3)
        self.sample_ops = [
            create_mouse_click_operation(MouseButton.LEFT, Position(10, 20)),
            create_key_operation("space", "press")
        ]
    
    def test_initial_state(self):
        """Test initial state of undo/redo manager."""
        assert not self.manager.can_undo()
        assert not self.manager.can_redo()
        assert self.manager.undo() is None
        assert self.manager.redo() is None
    
    def test_save_and_undo(self):
        """Test saving state and undo functionality."""
        # Save first state
        self.manager.save_state(self.sample_ops)
        assert not self.manager.can_undo()  # Need at least 2 states
        
        # Save second state  
        modified_ops = self.sample_ops[::-1]  # Reversed order
        self.manager.save_state(modified_ops)
        assert self.manager.can_undo()
        
        # Test undo
        previous_state = self.manager.undo()
        assert previous_state is not None
        assert len(previous_state) == len(self.sample_ops)
        assert previous_state[0].id == self.sample_ops[0].id
    
    def test_redo(self):
        """Test redo functionality."""
        # Save two states
        self.manager.save_state(self.sample_ops)
        modified_ops = self.sample_ops[::-1]
        self.manager.save_state(modified_ops)
        
        # Undo then redo
        self.manager.undo()
        assert self.manager.can_redo()
        
        next_state = self.manager.redo()
        assert next_state is not None
        assert next_state[0].id == modified_ops[0].id
    
    def test_history_limit(self):
        """Test history size limitation."""
        # Add more states than the limit
        for i in range(5):
            ops = [create_mouse_click_operation(MouseButton.LEFT, Position(i, i))]
            self.manager.save_state(ops)
        
        # Should not exceed max history
        assert len(self.manager.history) <= self.manager.max_history
    
    def test_save_after_undo_clears_redo(self):
        """Test that saving new state after undo clears redo history."""
        # Save states and undo
        self.manager.save_state(self.sample_ops)
        modified_ops = self.sample_ops[::-1]
        self.manager.save_state(modified_ops)
        self.manager.undo()
        
        # Save new state - should clear redo
        new_ops = [create_key_operation("a", "press")]
        self.manager.save_state(new_ops)
        assert not self.manager.can_redo()


class TestDragDropCanvas:
    """Test drag-drop canvas functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        self.canvas = DragDropCanvas(self.root)
        self.sample_ops = [
            create_mouse_click_operation(MouseButton.LEFT, Position(10, 20)),
            create_key_operation("space", "press"),
            create_mouse_click_operation(MouseButton.RIGHT, Position(30, 40))
        ]
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.root.destroy()
    
    def test_add_block(self):
        """Test adding blocks to canvas."""
        # Add a block
        self.canvas.add_block(self.sample_ops[0])
        assert len(self.canvas.blocks) == 1
        
        # Check block data
        block = self.canvas.blocks[0]
        assert block["operation"] == self.sample_ops[0]
        assert block["index"] == 0
    
    def test_add_multiple_blocks(self):
        """Test adding multiple blocks."""
        # Add blocks
        for op in self.sample_ops:
            self.canvas.add_block(op)
        
        assert len(self.canvas.blocks) == len(self.sample_ops)
        
        # Check order
        for i, block in enumerate(self.canvas.blocks):
            assert block["index"] == i
            assert block["operation"] == self.sample_ops[i]
    
    def test_get_ordered_operations(self):
        """Test getting ordered operations."""
        # Add blocks
        for op in self.sample_ops:
            self.canvas.add_block(op)
        
        ordered_ops = self.canvas.get_ordered_operations()
        assert len(ordered_ops) == len(self.sample_ops)
        assert ordered_ops == self.sample_ops
    
    def test_clear_blocks(self):
        """Test clearing all blocks."""
        # Add blocks then clear
        for op in self.sample_ops:
            self.canvas.add_block(op)
        
        self.canvas.clear_blocks()
        assert len(self.canvas.blocks) == 0
        assert len(self.canvas.get_ordered_operations()) == 0
    
    def test_reorder_block(self):
        """Test reordering blocks."""
        # Add blocks
        for op in self.sample_ops:
            self.canvas.add_block(op)
        
        # Mock the callback
        self.canvas.master = Mock()
        self.canvas.master._on_blocks_reordered = Mock()
        
        # Reorder: move first block to last position
        self.canvas._reorder_block(0, 3)  # Move to end
        
        # Check new order
        ordered_ops = self.canvas.get_ordered_operations()
        assert len(ordered_ops) == 3
        assert ordered_ops[0] == self.sample_ops[1]  # Second becomes first
        assert ordered_ops[1] == self.sample_ops[2]  # Third becomes second
        assert ordered_ops[2] == self.sample_ops[0]  # First becomes last
        
        # Check callback was called
        self.canvas.master._on_blocks_reordered.assert_called_once()
    
    def test_block_text_generation(self):
        """Test block text generation for different operation types."""
        # Mouse click
        mouse_op = self.sample_ops[0]
        text = self.canvas._get_block_text(mouse_op)
        assert "マウスクリック" in text
        assert "left" in text
        assert "(10, 20)" in text
        
        # Key press
        key_op = self.sample_ops[1]
        text = self.canvas._get_block_text(key_op)
        assert "キー押下" in text
        assert "space" in text


class TestVisualEditor:
    """Test visual editor main functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
        self.editor = VisualEditor(self.root)
        
        # Create test macro
        self.test_macro = MacroRecording(
            name="Test Macro",
            created_at=time.time(),
            operations=[
                create_mouse_click_operation(MouseButton.LEFT, Position(10, 20)),
                create_key_operation("space", "press")
            ],
            metadata={}
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.root.destroy()
    
    def test_load_macro(self):
        """Test loading a macro into the editor."""
        self.editor.load_macro(self.test_macro)
        
        assert self.editor.macro_recording == self.test_macro
        assert len(self.editor.canvas.blocks) == len(self.test_macro.operations)
        
        # Check undo manager has initial state
        assert len(self.editor.undo_manager.history) == 1
    
    def test_get_current_macro(self):
        """Test getting current macro state."""
        self.editor.load_macro(self.test_macro)
        
        current_macro = self.editor.get_current_macro()
        assert current_macro is not None
        assert current_macro.name == self.test_macro.name
        assert len(current_macro.operations) == len(self.test_macro.operations)
    
    def test_undo_redo_integration(self):
        """Test undo/redo integration with canvas."""
        self.editor.load_macro(self.test_macro)
        
        # Simulate block reorder
        original_order = [op.id for op in self.test_macro.operations]
        
        # Manually trigger reorder
        self.editor._on_blocks_reordered(0, 1)
        
        # Should have more history now
        assert len(self.editor.undo_manager.history) == 2
        
        # Test undo
        self.editor._undo()
        current_order = [op.id for op in self.editor.macro_recording.operations]
        assert current_order == original_order
    
    def test_callback_notification(self):
        """Test callback notification on changes."""
        callback_mock = Mock()
        self.editor.on_macro_changed = callback_mock
        
        self.editor.load_macro(self.test_macro)
        
        # Simulate change
        self.editor._on_blocks_reordered(0, 1)
        
        # Callback should be called
        callback_mock.assert_called()


def run_tests():
    """Run all tests manually without pytest runner."""
    print("Running Visual Editor Tests...")
    
    # Test UndoRedoManager
    print("\n1. Testing UndoRedoManager...")
    manager_tests = TestUndoRedoManager()
    try:
        manager_tests.setup_method()
        manager_tests.test_initial_state()
        manager_tests.test_save_and_undo()
        manager_tests.test_redo()
        manager_tests.test_history_limit()
        manager_tests.test_save_after_undo_clears_redo()
        print("   ✓ UndoRedoManager tests passed")
    except Exception as e:
        print(f"   ✗ UndoRedoManager tests failed: {e}")
    
    # Test DragDropCanvas
    print("\n2. Testing DragDropCanvas...")
    canvas_tests = TestDragDropCanvas()
    try:
        canvas_tests.setup_method()
        canvas_tests.test_add_block()
        canvas_tests.test_add_multiple_blocks()
        canvas_tests.test_get_ordered_operations()
        canvas_tests.test_clear_blocks()
        canvas_tests.test_reorder_block()
        canvas_tests.test_block_text_generation()
        canvas_tests.teardown_method()
        print("   ✓ DragDropCanvas tests passed")
    except Exception as e:
        print(f"   ✗ DragDropCanvas tests failed: {e}")
    
    # Test VisualEditor
    print("\n3. Testing VisualEditor...")
    editor_tests = TestVisualEditor()
    try:
        editor_tests.setup_method()
        editor_tests.test_load_macro()
        editor_tests.test_get_current_macro()
        editor_tests.test_undo_redo_integration()
        editor_tests.test_callback_notification()
        editor_tests.teardown_method()
        print("   ✓ VisualEditor tests passed")
    except Exception as e:
        print(f"   ✗ VisualEditor tests failed: {e}")
    
    print("\nAll tests completed!")


if __name__ == "__main__":
    run_tests()