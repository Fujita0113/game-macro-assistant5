#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from smoke_test_image_editor import create_test_macro_with_screenshot

try:
    result = create_test_macro_with_screenshot()
    print('SUCCESS: スモークテスト関数が正常に実行されました')
    print(f'作成された操作数: {len(result)}')
except Exception as e:
    print(f'EXPECTED ERROR: {e}')
    import traceback

    traceback.print_exc()
