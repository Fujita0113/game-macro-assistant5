#!/usr/bin/env python3
"""
Issue#12 画像編集機能 - 手動スモークテスト

このスクリプトを実行して、画像編集機能を手動でテストしてください。
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw
import io
import sys
import os
import time

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.macro_data import OperationBlock, OperationType, ScreenCondition
from ui.visual_editor import VisualEditor


def create_test_image():
    """テスト用の画像を作成"""
    image = Image.new('RGB', (300, 200), color='lightblue')
    draw = ImageDraw.Draw(image)

    # テスト用の要素を描画
    draw.rectangle([50, 50, 150, 100], fill='red', outline='black', width=2)
    draw.text((60, 65), 'Button 1', fill='white')

    draw.rectangle([180, 50, 250, 100], fill='green', outline='black', width=2)
    draw.text((190, 65), 'Button 2', fill='white')

    draw.rectangle([100, 120, 200, 170], fill='blue', outline='black', width=2)
    draw.text((120, 135), 'Button 3', fill='white')

    return image


def create_test_macro_with_screenshot():
    """スクリーンショット付きのテスト用マクロを作成

    画像編集機能のテストに必要なScreenConditionブロックを含む
    テスト用マクロデータを作成します。

    Returns:
        List[OperationBlock]: スクリーン条件チェック操作を含むリスト
    """
    # テスト用の模擬画像を作成（カラフルなボタン要素を含む）
    test_image = create_test_image()

    # PIL画像をバイト配列に変換（ScreenConditionで使用）
    image_buffer = io.BytesIO()
    test_image.save(image_buffer, format='PNG')
    image_data = image_buffer.getvalue()

    # スクリーン条件オブジェクトを作成
    # 画像全体を対象領域として設定（後で画像編集で部分選択可能）
    screen_condition = ScreenCondition(
        image_data=image_data,
        region=(0, 0, test_image.width, test_image.height),  # 全画像領域
        threshold=0.8,  # 画像マッチング閾値
        timeout=5.0,  # タイムアウト（デフォルト値）
    )

    # 操作ブロックを作成（必須パラメータを明示的に指定）
    current_time = time.time()
    operation = OperationBlock(
        id=f'test_screen_condition_{int(current_time * 1000)}',  # ユニークID生成
        operation_type=OperationType.SCREEN_CONDITION,
        timestamp=current_time,  # 作成時刻
        screen_condition=screen_condition,
        delay_after=0.0,  # 後続操作までの遅延
    )

    return [operation]


class SmokeTestApp:
    """スモークテスト用のアプリケーション"""

    def __init__(self, root):
        self.root = root
        self.root.title('Issue#12 画像編集機能 スモークテスト')
        self.root.geometry('800x600')

        self.visual_editor = None
        self.setup_ui()

    def setup_ui(self):
        """UIセットアップ"""
        main_frame = ttk.Frame(self.root, padding='10')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # タイトル
        title_label = ttk.Label(
            main_frame,
            text='Issue#12 画像編集機能 スモークテスト',
            font=('Arial', 14, 'bold'),
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # 手順説明
        instructions = """
手順:
1. 下の「テスト開始」ボタンをクリック
2. ビジュアルエディタが開きます
3. 画面条件チェックブロック（青いボタンが描かれた画像）をダブルクリック
4. 画像編集ウィンドウが開くので、以下をテスト:
   - マウスドラッグで矩形選択
   - 選択領域の赤枠ハイライト表示
   - 5x5未満の選択でエラーメッセージ
   - OKで選択確定、キャンセルで破棄
        """

        instruction_label = ttk.Label(main_frame, text=instructions, justify=tk.LEFT)
        instruction_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 20))

        # テスト開始ボタン
        start_button = ttk.Button(
            main_frame, text='テスト開始', command=self.start_test
        )
        start_button.grid(row=2, column=0, pady=10)

        # 終了ボタン
        quit_button = ttk.Button(main_frame, text='終了', command=self.root.quit)
        quit_button.grid(row=2, column=1, pady=10, padx=(10, 0))

        # 結果表示エリア
        result_frame = ttk.LabelFrame(main_frame, text='テスト結果', padding='5')
        result_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20)

        self.result_text = tk.Text(result_frame, height=10, width=70)
        scrollbar = ttk.Scrollbar(
            result_frame, orient=tk.VERTICAL, command=self.result_text.yview
        )
        self.result_text.configure(yscrollcommand=scrollbar.set)

        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 初期メッセージ
        self.log_result('スモークテスト準備完了')
        self.log_result('「テスト開始」ボタンをクリックしてテストを開始してください')

    def log_result(self, message):
        """結果をログに記録"""
        self.result_text.insert(tk.END, f'{message}\n')
        self.result_text.see(tk.END)
        self.root.update()

    def start_test(self):
        """テスト開始"""
        try:
            self.log_result('=' * 50)
            self.log_result('スモークテスト開始')
            self.log_result('=' * 50)

            # テスト用マクロデータを作成
            try:
                test_operations = create_test_macro_with_screenshot()
                self.log_result(
                    f'OK テストデータ作成完了 ({len(test_operations)}個の操作)'
                )
            except Exception as e:
                self.log_result(f'NG テストデータ作成失敗: {e}')
                raise

            # 既存のビジュアルエディタがあれば閉じる
            if self.visual_editor:
                try:
                    self.visual_editor.destroy()
                except (AttributeError, tk.TclError):
                    pass  # 既に破棄されている場合は無視

            # ビジュアルエディタを開く
            try:
                self.visual_editor = VisualEditor(None)  # Create new Toplevel window
                self.visual_editor.on_macro_changed = self.on_visual_editor_change

                # Convert operations list to MacroRecording
                from core.macro_data import MacroRecording

                test_macro = MacroRecording(
                    name='Smoke Test Macro',
                    created_at=time.time(),
                    operations=test_operations,
                    metadata={'source': 'smoke_test'},
                )
                self.visual_editor.load_macro(test_macro)
                self.log_result('OK ビジュアルエディタが開きました')
            except Exception as e:
                self.log_result(f'NG ビジュアルエディタ作成失敗: {e}')
                raise

            # 手順説明
            self.log_result('')
            self.log_result('📋 次の手順でテストしてください:')
            self.log_result('1. ビジュアルエディタの画面条件ブロックをダブルクリック')
            self.log_result('2. 画像編集ウィンドウが開くことを確認')
            self.log_result('3. マウスドラッグで矩形選択をテスト')
            self.log_result('4. 選択領域が赤枠でハイライトされることを確認')
            self.log_result('5. 小さな選択（5x5未満）でエラーが出ることを確認')
            self.log_result('6. 適切なサイズでOKボタンをクリック')
            self.log_result('7. キャンセルボタンの動作も確認')
            self.log_result('')
            self.log_result(
                '⚠️  テスト中に問題があれば、このウィンドウで報告してください'
            )

        except Exception as e:
            self.log_result(f'NG 重大エラー: {e}')
            self.log_result('スタックトレース:')
            import traceback

            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    self.log_result(f'  {line}')
            self.log_result('')
            self.log_result('修正が必要です。開発者に連絡してください。')

    def on_visual_editor_change(self, macro):
        """ビジュアルエディタからの変更通知"""
        self.log_result('🔄 マクロが更新されました')
        if macro:
            self.log_result(f'   操作数: {len(macro.operations)}個')


def main():
    """メイン関数"""
    print('Issue#12 画像編集機能 スモークテストを開始します...')

    root = tk.Tk()
    SmokeTestApp(root)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        print('テストが中断されました')
    except Exception as e:
        print(f'エラー: {e}')
        import traceback

        traceback.print_exc()


if __name__ == '__main__':
    main()
