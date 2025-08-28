#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ScreenConditionクラスの詳細検証とデバッグ用スクリプト
"""

import sys
import os
import traceback
from PIL import Image
import io

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print('=' * 60)
print('ScreenConditionクラス 詳細検証開始')
print('=' * 60)

# Step 1: Import文の検証
print('\n[Step 1] Import文の検証')
print('-' * 30)

try:
    from core.macro_data import ScreenCondition, OperationBlock, OperationType

    print('OK core.macro_data のimport成功')
except Exception as e:
    print(f'NG core.macro_data のimport失敗: {e}')
    traceback.print_exc()
    sys.exit(1)

# Step 2: ScreenConditionクラスの詳細確認
print('\n[Step 2] ScreenConditionクラスの詳細確認')
print('-' * 40)

print(f'ScreenCondition クラス: {ScreenCondition}')
print('ScreenCondition.__init__ シグネチャ:')

try:
    import inspect

    sig = inspect.signature(ScreenCondition.__init__)
    print(f'  {sig}')

    print('\nScreenCondition の利用可能属性:')
    for attr in dir(ScreenCondition):
        if not attr.startswith('_'):
            print(f'  - {attr}')

    # データクラスのフィールド情報
    if hasattr(ScreenCondition, '__dataclass_fields__'):
        print('\nDataclassフィールド:')
        for field_name, field_info in ScreenCondition.__dataclass_fields__.items():
            print(
                f'  - {field_name}: {field_info.type} (default: {field_info.default})'
            )

except Exception as e:
    print(f'NG クラス詳細確認エラー: {e}')
    traceback.print_exc()

# Step 3: 各パラメータでのテスト
print('\n[Step 3] 各パラメータでのインスタンス生成テスト')
print('-' * 50)

# テスト画像データを作成
test_image = Image.new('RGB', (100, 100), color='red')
image_buffer = io.BytesIO()
test_image.save(image_buffer, format='PNG')
image_data = image_buffer.getvalue()

print(f'テスト画像データサイズ: {len(image_data)} bytes')

# パターン1: 最小限のパラメータ
print('\n[テスト1] 最小限のパラメータ')
try:
    sc1 = ScreenCondition(image_data=image_data)
    print('OK 最小限パラメータでの生成成功')
    print(f'  - image_data: {len(sc1.image_data)} bytes')
    print(f'  - region: {sc1.region}')
    if hasattr(sc1, 'threshold'):
        print(f'  - threshold: {sc1.threshold}')
    if hasattr(sc1, 'confidence'):
        print(f'  - confidence: {sc1.confidence}')
    if hasattr(sc1, 'timeout'):
        print(f'  - timeout: {sc1.timeout}')
except Exception as e:
    print(f'NG 最小限パラメータでの生成失敗: {e}')
    traceback.print_exc()

# パターン2: region付き
print('\n[テスト2] region付き')
try:
    sc2 = ScreenCondition(image_data=image_data, region=(10, 10, 50, 50))
    print('OK region付きでの生成成功')
    print(f'  - region: {sc2.region}')
except Exception as e:
    print(f'NG region付きでの生成失敗: {e}')
    traceback.print_exc()

# パターン3: threshold付き（問題の可能性がある箇所）
print('\n[テスト3] threshold付き')
try:
    sc3 = ScreenCondition(image_data=image_data, threshold=0.8)
    print('OK threshold付きでの生成成功')
    print(f'  - threshold: {sc3.threshold}')
except Exception as e:
    print(f'NG threshold付きでの生成失敗: {e}')
    traceback.print_exc()

# パターン4: confidence付き（エラーが予想される）
print('\n[テスト4] confidence付き（エラー予想）')
try:
    sc4 = ScreenCondition(image_data=image_data, confidence=0.8)
    print('WARN confidence付きでの生成成功（予想外）')
    print(f'  - confidence: {sc4.confidence}')
except Exception as e:
    print(f'OK confidence付きでの生成失敗（予想通り）: {e}')

# パターン5: 全パラメータ（正しいもの）
print('\n[テスト5] 全パラメータ（正しいパラメータ名）')
try:
    sc5 = ScreenCondition(
        image_data=image_data, region=(10, 10, 50, 50), threshold=0.8, timeout=5.0
    )
    print('OK 全パラメータでの生成成功')
    print(f'  - image_data: {len(sc5.image_data)} bytes')
    print(f'  - region: {sc5.region}')
    print(f'  - threshold: {sc5.threshold}')
    print(f'  - timeout: {sc5.timeout}')
except Exception as e:
    print(f'NG 全パラメータでの生成失敗: {e}')
    traceback.print_exc()

# Step 4: OperationBlock作成テスト
print('\n[Step 4] OperationBlock作成テスト')
print('-' * 35)

try:
    screen_condition = ScreenCondition(
        image_data=image_data,
        region=None,
        threshold=0.8,  # confidence ではなく threshold
    )

    operation = OperationBlock(
        operation_type=OperationType.SCREEN_CONDITION, screen_condition=screen_condition
    )

    print('OK OperationBlock作成成功')
    print(f'  - operation_type: {operation.operation_type}')
    print(f'  - screen_condition: {operation.screen_condition}')

except Exception as e:
    print(f'NG OperationBlock作成失敗: {e}')
    traceback.print_exc()

print('\n' + '=' * 60)
print('検証完了')
print('=' * 60)
