"""
Test script for image editing functionality.

This script creates a sample macro recording with screenshot data
and opens the visual editor to demonstrate image editing capabilities.
"""

import tkinter as tk
from PIL import Image, ImageDraw
import io
import time

from src.core.macro_data import (
    MacroRecording, OperationBlock, OperationType, ScreenCondition,
    MouseOperation, MouseButton, Position, create_mouse_click_operation
)
from src.ui.visual_editor import VisualEditor


def create_sample_image() -> bytes:
    """Create a sample screenshot image for testing."""
    # Create a test image
    width, height = 400, 300
    image = Image.new('RGB', (width, height), color='lightblue')
    
    # Draw some test elements
    draw = ImageDraw.Draw(image)
    
    # Draw a button-like rectangle
    draw.rectangle([50, 50, 150, 100], fill='lightgray', outline='black', width=2)
    draw.text((75, 70), "Button", fill='black')
    
    # Draw another element
    draw.rectangle([200, 150, 300, 200], fill='lightgreen', outline='darkgreen', width=2)
    draw.text((225, 170), "Element", fill='black')
    
    # Draw some text
    draw.text((50, 250), "Sample Screenshot for Testing", fill='darkblue')
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')
    return img_bytes.getvalue()


def create_sample_recording() -> MacroRecording:
    """Create a sample macro recording for testing."""
    current_time = time.time()
    
    # Create sample operations
    operations = []
    
    # Mouse click operation
    mouse_click = create_mouse_click_operation(
        MouseButton.LEFT,
        Position(100, 75),  # Click on the button
        current_time
    )
    operations.append(mouse_click)
    
    # Screen condition operation with sample image
    image_data = create_sample_image()
    screen_condition = ScreenCondition(
        image_data=image_data,
        region=None,  # Will be set by image editor
        threshold=0.8,
        timeout=5.0
    )
    
    screen_condition_block = OperationBlock(
        id=f"screen_condition_{int(current_time * 1000)}",
        operation_type=OperationType.SCREEN_CONDITION,
        timestamp=current_time + 1.0,
        screen_condition=screen_condition
    )
    operations.append(screen_condition_block)
    
    # Another mouse click
    mouse_click2 = create_mouse_click_operation(
        MouseButton.LEFT,
        Position(250, 175),  # Click on the element
        current_time + 2.0
    )
    operations.append(mouse_click2)
    
    # Create macro recording
    recording = MacroRecording(
        name="サンプルマクロ - 画像編集テスト",
        created_at=current_time,
        operations=operations,
        metadata={"test": True, "version": "1.0"}
    )
    
    return recording


def main():
    """Main test function."""
    print("画像編集機能のテストを開始します...")
    
    # Create sample recording
    recording = create_sample_recording()
    
    print(f"サンプル記録を作成しました:")
    print(f"- 名前: {recording.name}")
    print(f"- 操作数: {recording.operation_count}")
    print(f"- 再生時間: {recording.duration:.1f}秒")
    print()
    
    # Create root window (hidden)
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    try:
        # Open visual editor
        print("ビジュアルエディタを開きます...")
        print("操作手順:")
        print("1. スクリーンショット画像をダブルクリックしてください")
        print("2. 画像編集ウィンドウでマウスをドラッグして領域を選択してください")
        print("3. 'OK'ボタンで選択を確定してください")
        print("4. 選択領域が更新されたメッセージを確認してください")
        print()
        
        editor = VisualEditor.open_visual_editor(recording, root)
        editor.show()
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        root.destroy()


if __name__ == "__main__":
    main()