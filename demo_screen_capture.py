#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Screen Capture System Demo and Test Script

Usage:
1. python demo_screen_capture.py - Basic tests
2. python demo_screen_capture.py --manual - Manual test mode
3. python demo_screen_capture.py --fullscreen - Fullscreen test mode
"""

import sys
import os
import time
import argparse
from PIL import Image

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.screen_capture import ScreenCaptureManager
from src.core.event_handler import ScreenCaptureEventHandler
from src.utils.logging import log_info, log_error


def test_basic_capture():
    """基本的なスクリーンキャプチャテスト"""
    print("=== 基本スクリーンキャプチャテスト ===")
    
    capture_manager = ScreenCaptureManager()
    
    # スクリーンショット取得
    print("スクリーンショットを取得中...")
    screenshot = capture_manager.capture_screen("test_basic_capture.png")
    
    if screenshot:
        print(f"✅ 成功: スクリーンショットが保存されました (サイズ: {screenshot.size})")
        print("📁 ファイル: test_basic_capture.png")
    else:
        print("❌ 失敗: スクリーンショット取得に失敗しました")
    
    return screenshot is not None


def test_region_capture():
    """領域キャプチャテスト"""
    print("\n=== 領域キャプチャテスト ===")
    
    capture_manager = ScreenCaptureManager()
    
    # 画面中央の200x200領域をキャプチャ
    print("画面中央の200x200領域をキャプチャ中...")
    screenshot = capture_manager.capture_region(400, 300, 200, 200)
    
    if screenshot:
        screenshot.save("test_region_capture.png")
        print(f"✅ 成功: 領域キャプチャが保存されました (サイズ: {screenshot.size})")
        print("📁 ファイル: test_region_capture.png")
    else:
        print("❌ 失敗: 領域キャプチャに失敗しました")
    
    return screenshot is not None


def test_watermark():
    """透かし機能テスト"""
    print("\n=== 透かし機能テスト ===")
    
    capture_manager = ScreenCaptureManager()
    
    # テスト画像作成
    test_image = Image.new('RGB', (800, 600), color='lightblue')
    
    # 透かしを追加
    print("透かしを追加中...")
    watermarked = capture_manager.add_watermark(test_image)
    
    if watermarked:
        watermarked.save("test_watermark.png")
        print("✅ 成功: 透かし付き画像が保存されました")
        print("📁 ファイル: test_watermark.png")
        print("💧 透かしテキスト:", capture_manager.fallback_watermark_text)
    else:
        print("❌ 失敗: 透かし追加に失敗しました")
    
    return watermarked is not None


def test_event_handler():
    """イベントハンドラテスト"""
    print("\n=== イベントハンドラテスト ===")
    
    event_handler = ScreenCaptureEventHandler()
    
    def screenshot_callback(filepath):
        print(f"📸 コールバック: スクリーンショットが保存されました -> {filepath}")
    
    event_handler.set_screenshot_callback(screenshot_callback)
    
    # マウスクリックイベントのシミュレーション
    print("マウスクリックイベントをシミュレーション...")
    filepath = event_handler.capture_on_mouse_click(100, 200, "left")
    
    if filepath:
        print("✅ 成功: イベントハンドラが正常に動作しました")
    else:
        print("❌ 失敗: イベントハンドラでエラーが発生しました")
    
    return filepath is not None


def test_error_simulation():
    """エラーシミュレーションテスト"""
    print("\n=== エラーシミュレーションテスト ===")
    
    # 無効なパスでのキャプチャテスト
    capture_manager = ScreenCaptureManager()
    
    try:
        print("無効なパスへの保存をテスト...")
        result = capture_manager.capture_screen("invalid/path/test.png")
        if result is None:
            print("✅ 成功: エラーが適切にハンドリングされました")
        else:
            print("⚠️  警告: エラーが発生しませんでした（予期しない結果）")
    except Exception as e:
        print(f"✅ 成功: 例外が適切にキャッチされました - {e}")
    
    print("📋 ログファイルを確認してErr-CAPエラーコードが記録されているか確認してください")


def manual_test():
    """手動テスト（ユーザーインタラクション付き）"""
    print("\n=== 手動テストモード ===")
    print("このモードでは、あなたの操作に応じてスクリーンショットが取得されます")
    
    event_handler = ScreenCaptureEventHandler()
    
    input("準備ができたらEnterキーを押してください...")
    
    print("\n1. 基本キャプチャテスト")
    input("Enterキーを押してスクリーンショットを取得...")
    filepath = event_handler.capture_manual()
    if filepath:
        print(f"✅ スクリーンショット保存: {filepath}")
    
    print("\n2. ディレクトリ変更テスト")
    event_handler.set_screenshot_directory("manual_test_screenshots")
    input("Enterキーを押して別ディレクトリに保存...")
    filepath = event_handler.capture_manual()
    if filepath:
        print(f"✅ スクリーンショット保存: {filepath}")
    
    print("\n手動テスト完了！")


def fullscreen_test():
    """フルスクリーンアプリケーション対応テスト"""
    print("\n=== フルスクリーンテストモード ===")
    print("このテストではGDIフォールバック機能をテストします")
    
    capture_manager = ScreenCaptureManager()
    
    print("\n手順:")
    print("1. このメッセージの後、フルスクリーンアプリケーション（ゲーム、動画プレーヤーなど）を起動")
    print("2. 5秒後に自動でスクリーンショットを取得します")
    print("3. CaptureLimited透かしが付いているか確認してください")
    
    input("準備ができたらEnterを押してください...")
    
    for i in range(5, 0, -1):
        print(f"スクリーンショット取得まであと {i} 秒...")
        time.sleep(1)
    
    print("スクリーンショット取得中...")
    screenshot = capture_manager.capture_screen("fullscreen_test.png")
    
    if screenshot:
        print("✅ フルスクリーンテスト完了")
        print("📁 ファイル: fullscreen_test.png")
        print("💧 透かしが付いている場合、GDIフォールバックが動作しました")
    else:
        print("❌ フルスクリーンテスト失敗")


def main():
    parser = argparse.ArgumentParser(description='スクリーンキャプチャシステムテスト')
    parser.add_argument('--manual', action='store_true', help='手動テストモード')
    parser.add_argument('--fullscreen', action='store_true', help='フルスクリーンテストモード')
    
    args = parser.parse_args()
    
    print("GameMacroAssistant - Screen Capture System Test")
    print("=" * 60)
    
    if args.manual:
        manual_test()
    elif args.fullscreen:
        fullscreen_test()
    else:
        # 自動テストスイート
        results = []
        
        results.append(test_basic_capture())
        results.append(test_region_capture())
        results.append(test_watermark())
        results.append(test_event_handler())
        test_error_simulation()
        
        print("\n" + "=" * 60)
        print("📊 テスト結果サマリー")
        print("=" * 60)
        
        passed = sum(results)
        total = len(results)
        
        print(f"✅ 成功: {passed}/{total} テスト")
        
        if passed == total:
            print("🎉 全てのテストが成功しました！")
        else:
            print("⚠️  一部のテストが失敗しました")
        
        print("\n📁 生成されたファイル:")
        for filename in ["test_basic_capture.png", "test_region_capture.png", 
                        "test_watermark.png", "screenshots/"]:
            if os.path.exists(filename):
                print(f"  - {filename}")
        
        print("\n📋 ログファイルの確認:")
        print("  - logs/ ディレクトリでErr-CAPエラーログを確認してください")


if __name__ == "__main__":
    main()