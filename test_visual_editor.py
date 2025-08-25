"""
Test script for the visual editor drag-and-drop functionality.
"""

import tkinter as tk
import time
from src.ui.visual_editor import VisualEditor
from src.core.macro_data import (
    MacroRecording,
    create_mouse_click_operation,
    create_key_operation,
    MouseButton,
    Position,
)


def create_test_macro() -> MacroRecording:
    """Create a test macro with sample operations."""
    operations = []
    base_time = time.time()

    # Mouse click operation
    mouse_op = create_mouse_click_operation(
        MouseButton.LEFT, Position(100, 200), base_time
    )
    operations.append(mouse_op)

    # Keyboard operation
    key_op = create_key_operation('space', 'press', [], base_time + 1)
    operations.append(key_op)

    # Another mouse click
    mouse_op2 = create_mouse_click_operation(
        MouseButton.RIGHT, Position(300, 400), base_time + 2
    )
    operations.append(mouse_op2)

    # Keyboard with modifiers
    key_op2 = create_key_operation('s', 'press', ['ctrl'], base_time + 3)
    operations.append(key_op2)

    return MacroRecording(
        name='テスト用マクロ',
        created_at=base_time,
        operations=operations,
        metadata={'description': 'ドラッグ&ドロップテスト用'},
    )


def on_macro_changed(macro: MacroRecording):
    """Callback when macro is changed."""
    print('Macro changed!')
    print(f'Operation count: {len(macro.operations)}')
    for i, op in enumerate(macro.operations):
        print(f'  {i + 1}. {op.operation_type.value} (ID: {op.id})')


def main():
    """Main test function."""
    try:
        root = tk.Tk()
        root.title('ビジュアルエディタテスト')

        # Create visual editor
        editor = VisualEditor(root)
        editor.on_macro_changed = on_macro_changed

        # Create test macro
        test_macro = create_test_macro()

        # Load macro into editor
        editor.load_macro(test_macro)

        # Add instructions
        instructions = tk.Label(
            root,
            text="""
テスト手順:
1. ブロックをマウスでドラッグしてみてください
2. 異なる位置にドロップしてください
3. Ctrl+Z でアンドゥしてください
4. Ctrl+Y でリドゥしてください

期待される動作:
- ブロックがスムーズにドラッグできる
- ドロップ位置に赤い線が表示される
- ドロップ後に順序が変更される
- アンドゥ/リドゥが動作する
            """,
            justify='left',
            font=('Arial', 10),
        )
        instructions.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        print('ビジュアルエディタテストを開始...')
        print('初期操作順序:')
        for i, op in enumerate(test_macro.operations):
            print(f'  {i + 1}. {op.operation_type.value} (ID: {op.id})')
        print('\nGUIでドラッグ&ドロップをテストしてください。')

        # Show editor
        editor.show()

        # タイムアウト対策 - 5分でタイムアウト
        root.after(300000, root.quit)

        # Start main loop
        root.mainloop()

    except tk.TclError as e:
        print(f'Tkinter環境エラー: {e}')
        print('GUI環境が利用できません。')
    except Exception as e:
        print(f'テスト実行エラー: {e}')
        print('Tkinter環境を確認してください')


if __name__ == '__main__':
    main()
