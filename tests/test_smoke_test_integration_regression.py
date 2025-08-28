#!/usr/bin/env python3
"""
Regression tests for smoke test integration issues.

This file contains tests that reproduce the exact errors found in the smoke test,
ensuring that fixes are properly validated and preventing future regressions.
"""

import pytest
import tkinter as tk
import time
from unittest.mock import Mock, patch
from PIL import Image, ImageDraw
import io

from src.core.macro_data import OperationBlock, OperationType, ScreenCondition, MacroRecording


class TestSmokeTestRegressionErrors:
    """Test cases that reproduce the exact smoke test errors."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create test image data same as smoke test
        self.test_image = Image.new('RGB', (300, 200), color='lightblue')
        draw = ImageDraw.Draw(self.test_image)
        draw.rectangle([50, 50, 150, 100], fill='red', outline='black', width=2)
        draw.text((60, 65), 'Button 1', fill='white')

        # Convert to bytes for ScreenCondition
        image_buffer = io.BytesIO()
        self.test_image.save(image_buffer, format='PNG')
        self.image_data = image_buffer.getvalue()

        # Create test operation (same as smoke test)
        current_time = time.time()
        screen_condition = ScreenCondition(
            image_data=self.image_data,
            region=(0, 0, self.test_image.width, self.test_image.height),
            threshold=0.8,
            timeout=5.0,
        )

        self.test_operation = OperationBlock(
            id=f'test_screen_condition_{int(current_time * 1000)}',
            operation_type=OperationType.SCREEN_CONDITION,
            timestamp=current_time,
            screen_condition=screen_condition,
            delay_after=0.0,
        )

    def test_visual_editor_callback_parameter_error(self, tk_root):
        """
        FAILING TEST: VisualEditor作成時にcallbackパラメータを使用するとエラーになることを確認
        
        修正前: TypeError: VisualEditor.__init__() got an unexpected keyword argument 'callback'
        """
        from src.ui.visual_editor import VisualEditor

        # This should fail exactly as in the smoke test
        with pytest.raises(TypeError) as exc_info:
            VisualEditor(tk_root, callback=lambda x, y: None)
        
        assert "unexpected keyword argument 'callback'" in str(exc_info.value)

    def test_load_macro_with_operation_list_error(self, tk_root):
        """
        FAILING TEST: load_macroにList[OperationBlock]を渡すとエラーになることを確認
        
        修正前: AttributeError: 'list' object has no attribute 'operations'
        """
        from src.ui.visual_editor import VisualEditor

        editor = VisualEditor(tk_root)
        
        # This should fail when trying to load a list instead of MacroRecording
        with pytest.raises(AttributeError) as exc_info:
            editor.load_macro([self.test_operation])  # List instead of MacroRecording
        
        # The error should be about missing 'operations' attribute on list
        assert "'list' object has no attribute 'operations'" in str(exc_info.value)

    def test_callback_signature_mismatch(self, tk_root):
        """
        FAILING TEST: コールバック関数のシグネチャ不一致でエラーになることを確認
        
        修正前: TypeError during callback execution due to signature mismatch
        """
        from src.ui.visual_editor import VisualEditor

        editor = VisualEditor(tk_root)

        # Create callback with wrong signature (from smoke test)
        def wrong_callback(from_index, to_index):
            pass

        # Set the wrong callback
        editor.on_macro_changed = wrong_callback

        # Create proper MacroRecording
        test_macro = MacroRecording(
            name='Test Macro',
            created_at=time.time(),
            operations=[self.test_operation],
            metadata={},
        )

        editor.load_macro(test_macro)

        # Trigger callback through block reordering - this should fail
        with pytest.raises(TypeError) as exc_info:
            editor._on_blocks_reordered(0, 0)

        # Should fail due to wrong number of arguments
        assert "missing 1 required positional argument" in str(exc_info.value)

    def test_geometry_manager_conflict_error(self, tk_root):
        """
        FAILING TEST: 既存のgridを使用しているrootウィンドウでVisualEditorを開くとエラーになることを確認
        
        修正前: TclError: cannot use geometry manager pack inside . which already has slaves managed by grid
        """
        from src.ui.visual_editor import VisualEditor
        import tkinter as tk
        from tkinter import ttk

        # Simulate the smoke test scenario: create widgets using grid in the root
        test_frame = ttk.Frame(tk_root, padding='10')
        test_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        test_label = ttk.Label(test_frame, text='Test Label')
        test_label.grid(row=0, column=0)

        # This should fail because root already has grid-managed children
        with pytest.raises(tk.TclError) as exc_info:
            VisualEditor(tk_root)  # Passing root with existing grid children
        
        assert "cannot use geometry manager pack inside . which already has slaves managed by grid" in str(exc_info.value)


class TestSmokeTestCorrectImplementation:
    """Test cases for the correct implementation after fixes."""

    def setup_method(self):
        """Set up test fixtures."""
        # Same setup as error tests but for success scenarios
        self.test_image = Image.new('RGB', (300, 200), color='lightblue')
        draw = ImageDraw.Draw(self.test_image)
        draw.rectangle([50, 50, 150, 100], fill='red', outline='black', width=2)

        image_buffer = io.BytesIO()
        self.test_image.save(image_buffer, format='PNG')
        self.image_data = image_buffer.getvalue()

        screen_condition = ScreenCondition(
            image_data=self.image_data,
            region=(0, 0, self.test_image.width, self.test_image.height),
            threshold=0.8,
            timeout=5.0,
        )

        self.test_operation = OperationBlock(
            id=f'test_screen_condition_{int(time.time() * 1000)}',
            operation_type=OperationType.SCREEN_CONDITION,
            timestamp=time.time(),
            screen_condition=screen_condition,
            delay_after=0.0,
        )

    def test_visual_editor_correct_initialization(self, tk_root):
        """
        SUCCESS TEST: 正しい方法でVisualEditorが初期化できることを確認
        """
        from src.ui.visual_editor import VisualEditor

        # Should work without callback parameter
        editor = VisualEditor(tk_root)
        
        # Should be able to set callback after initialization
        callback_mock = Mock()
        editor.on_macro_changed = callback_mock
        
        assert editor.on_macro_changed == callback_mock
        assert editor.root is not None

    def test_load_macro_with_macro_recording_success(self, tk_root):
        """
        SUCCESS TEST: MacroRecordingオブジェクトでload_macroが成功することを確認
        """
        from src.ui.visual_editor import VisualEditor

        editor = VisualEditor(tk_root)
        
        # Create proper MacroRecording object
        test_macro = MacroRecording(
            name='Test Macro',
            created_at=time.time(),
            operations=[self.test_operation],
            metadata={},
        )

        # This should work without errors
        editor.load_macro(test_macro)
        
        assert editor.macro_recording == test_macro
        assert len(editor.canvas.blocks) == 1

    def test_correct_callback_signature(self, tk_root):
        """
        SUCCESS TEST: 正しいシグネチャのコールバックが動作することを確認
        """
        from src.ui.visual_editor import VisualEditor

        editor = VisualEditor(tk_root)

        # Create callback with correct signature
        callback_mock = Mock()
        editor.on_macro_changed = callback_mock

        # Create and load macro
        test_macro = MacroRecording(
            name='Test Macro',
            created_at=time.time(),
            operations=[self.test_operation],
            metadata={},
        )

        editor.load_macro(test_macro)

        # Trigger callback - should work without errors
        editor._on_blocks_reordered(0, 0)

        # Callback should be called with MacroRecording object
        callback_mock.assert_called_once()
        call_args = callback_mock.call_args[0]
        assert len(call_args) == 1
        assert isinstance(call_args[0], MacroRecording)

    def test_geometry_manager_no_conflict_with_new_window(self, tk_root):
        """
        SUCCESS TEST: 新しいTopLevelウィンドウを使用することで競合を避けられることを確認
        """
        from src.ui.visual_editor import VisualEditor
        import tkinter as tk
        from tkinter import ttk

        # Simulate the smoke test scenario: create widgets using grid in the root
        test_frame = ttk.Frame(tk_root, padding='10')
        test_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        test_label = ttk.Label(test_frame, text='Test Label')
        test_label.grid(row=0, column=0)

        # This should work by creating a new Toplevel window instead of using root
        editor = VisualEditor(None)  # Pass None to create new Toplevel
        
        # Should create its own window successfully
        assert editor.root is not None
        assert editor.root != tk_root  # Should be a different window
        assert isinstance(editor.root, tk.Toplevel)

    def test_smoke_test_complete_flow_simulation(self, tk_root):
        """
        SUCCESS TEST: 修正後のスモークテストの完全なフローをシミュレーション
        """
        from src.ui.visual_editor import VisualEditor

        # Step 1: Correct VisualEditor initialization
        editor = VisualEditor(tk_root)
        
        # Step 2: Set callback with correct signature
        callback_results = []
        def correct_callback(macro):
            callback_results.append(macro)
        
        editor.on_macro_changed = correct_callback

        # Step 3: Create proper MacroRecording from operations list
        operations_list = [self.test_operation]
        test_macro = MacroRecording(
            name='Smoke Test Macro',
            created_at=time.time(),
            operations=operations_list,
            metadata={'source': 'smoke_test'},
        )

        # Step 4: Load macro successfully
        editor.load_macro(test_macro)

        # Verify everything is set up correctly
        assert editor.macro_recording == test_macro
        assert len(editor.canvas.blocks) == 1
        assert editor.canvas.blocks[0]['operation'].operation_type == OperationType.SCREEN_CONDITION

        # Step 5: Simulate image editing callback trigger
        editor._on_blocks_reordered(0, 0)

        # Verify callback was triggered correctly
        assert len(callback_results) == 1
        assert isinstance(callback_results[0], MacroRecording)
        assert callback_results[0].name == 'Smoke Test Macro'