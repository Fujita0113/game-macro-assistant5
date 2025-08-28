#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
スモークテストで発見した問題の回帰テスト

このテストは現在失敗することを想定しており、
修正後に成功するようになることで、修正の有効性を検証します。
"""

import pytest
import sys
import os
import io
import time
from PIL import Image

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.macro_data import ScreenCondition, OperationBlock, OperationType


class TestSmokeTestRegression:
    """スモークテストで発見した問題の回帰テスト"""

    def setup_method(self):
        """テストデータのセットアップ"""
        # テスト用画像を作成
        self.test_image = Image.new('RGB', (100, 100), color='red')
        image_buffer = io.BytesIO()
        self.test_image.save(image_buffer, format='PNG')
        self.image_data = image_buffer.getvalue()

    def test_screencondition_with_confidence_parameter_should_fail(self):
        """
        FAILING TEST: ScreenCondition作成時にconfidenceパラメータを使用するとエラーになることを確認

        この問題は smoke_test_image_editor.py で発見された。
        修正前: TypeError: ScreenCondition.__init__() got an unexpected keyword argument 'confidence'
        修正後: このテストは成功し、代わりに threshold パラメータが使用されるべき
        """
        with pytest.raises(TypeError, match="unexpected keyword argument 'confidence'"):
            ScreenCondition(
                image_data=self.image_data,
                region=None,
                confidence=0.8,  # ← この行がエラーの原因
            )

    def test_screencondition_with_missing_region_should_fail(self):
        """
        FAILING TEST: ScreenCondition作成時にregionパラメータを省略するとエラーになることを確認

        デバッグログで発見: regionは必須パラメータだが、型注釈では Optional になっている
        修正前: TypeError: ScreenCondition.__init__() missing 1 required positional argument: 'region'
        修正後: regionを適切に指定することで解決
        """
        with pytest.raises(
            TypeError, match="missing 1 required positional argument: 'region'"
        ):
            ScreenCondition(image_data=self.image_data)

    def test_operationblock_with_missing_required_parameters_should_fail(self):
        """
        FAILING TEST: OperationBlock作成時に必須パラメータが不足するとエラーになることを確認

        デバッグログで発見: id と timestamp が必須パラメータ
        修正前: TypeError: OperationBlock.__init__() missing 2 required positional arguments: 'id' and 'timestamp'
        修正後: 適切にid と timestamp を指定することで解決
        """
        screen_condition = ScreenCondition(
            image_data=self.image_data, region=(0, 0, 100, 100), threshold=0.8
        )

        with pytest.raises(TypeError, match='missing .* required positional argument'):
            OperationBlock(
                operation_type=OperationType.SCREEN_CONDITION,
                screen_condition=screen_condition,
                # id と timestamp が不足
            )

    def test_correct_screencondition_creation_should_work(self):
        """
        SUCCESS TEST: 正しいパラメータでScreenConditionが作成できることを確認

        修正後にこのテストが成功することで、修正の有効性を確認
        """
        screen_condition = ScreenCondition(
            image_data=self.image_data,
            region=(0, 0, 100, 100),  # 画像全体を指定
            threshold=0.8,  # confidence ではなく threshold
        )

        assert screen_condition.image_data == self.image_data
        assert screen_condition.region == (0, 0, 100, 100)
        assert screen_condition.threshold == 0.8
        assert screen_condition.timeout == 5.0  # デフォルト値

    def test_correct_operationblock_creation_should_work(self):
        """
        SUCCESS TEST: 正しいパラメータでOperationBlockが作成できることを確認

        修正後にこのテストが成功することで、修正の有効性を確認
        """
        screen_condition = ScreenCondition(
            image_data=self.image_data, region=(0, 0, 100, 100), threshold=0.8
        )

        operation_block = OperationBlock(
            id='test_operation_1',  # 必須パラメータ
            operation_type=OperationType.SCREEN_CONDITION,
            timestamp=time.time(),  # 必須パラメータ
            screen_condition=screen_condition,
        )

        assert operation_block.id == 'test_operation_1'
        assert operation_block.operation_type == OperationType.SCREEN_CONDITION
        assert operation_block.screen_condition == screen_condition
        assert operation_block.delay_after == 0.0  # デフォルト値

    def test_smoke_test_data_creation_equivalent(self):
        """
        INTEGRATION TEST: スモークテストのデータ作成処理と同等の処理が成功することを確認

        これは smoke_test_image_editor.py の create_test_macro_with_screenshot()
        関数の修正版がうまく動作することを確認する
        """
        # 修正前の問題のあるコード（コメントアウト）
        # screen_condition = ScreenCondition(
        #     image_data=self.image_data,
        #     region=None,  # 問題1: 必須なのにNone
        #     confidence=0.8  # 問題2: 存在しないパラメータ
        # )

        # 修正後の正しいコード
        screen_condition = ScreenCondition(
            image_data=self.image_data,
            region=(0, 0, self.test_image.width, self.test_image.height),  # 画像全体
            threshold=0.8,  # confidence → threshold
        )

        operation = OperationBlock(
            id=f'screen_condition_{int(time.time())}',  # 追加: 必須パラメータ
            operation_type=OperationType.SCREEN_CONDITION,
            timestamp=time.time(),  # 追加: 必須パラメータ
            screen_condition=screen_condition,
        )

        # 作成されたオブジェクトの妥当性を確認
        assert operation.operation_type == OperationType.SCREEN_CONDITION
        assert operation.screen_condition is not None
        assert operation.screen_condition.image_data == self.image_data
        assert operation.screen_condition.region == (0, 0, 100, 100)
        assert operation.screen_condition.threshold == 0.8

    def test_fixed_smoke_test_pattern_should_work_after_fix(self):
        """
        SUCCESS TEST: 修正後のパターンは成功することを確認

        修正前は失敗していたパターンを修正版で置き換え
        """
        # 修正後のスモークテストパターン
        screen_condition = ScreenCondition(
            image_data=self.image_data,
            region=(
                0,
                0,
                self.test_image.width,
                self.test_image.height,
            ),  # 修正: 画像全体を指定
            threshold=0.8,  # 修正: confidence → threshold
        )

        operation = OperationBlock(
            id=f'test_screen_condition_{int(time.time() * 1000)}',  # 修正: 必須パラメータ追加
            operation_type=OperationType.SCREEN_CONDITION,
            timestamp=time.time(),  # 修正: 必須パラメータ追加
            screen_condition=screen_condition,
        )

        # 修正後は正常に動作するはず
        assert operation.operation_type == OperationType.SCREEN_CONDITION
        assert operation.screen_condition is not None
        assert operation.id is not None
        assert operation.timestamp > 0
