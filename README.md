# GameMacroAssistant

PC ゲーム向けのデスクトップ自動化ツールです。マウス／キーボード操作の記録・編集・再生に加え、画面認識により条件一致時のみアクションを実行します。ネイティブ解像度のキャプチャと、失敗時の GDI フォールバック（Windows）を備えます。

## 主な機能

- グローバル入力キャプチャ（マウス3ボタン／キーボード、ESC で終了）
- 画面認識（保存条件と現在画面のマッチング）
- 可視化エディタ（ブロック操作／ドラッグ＆ドロップ／矩形選択／アンドゥ）
- エラーログ（`Err-CAP`, `Err-TMO` などのコード付き）
- 暗号化保存（パスワード保護付き `.gma.json`）
- 実行エンジン（グローバルホットキー、タイムアウト、通知、トレイ進捗）

## 対応プラットフォーム

- 最終デプロイ: Windows 10/11
- 開発・検証: Linux（CI で ruff/pytest を実行、GUI は Xvfb でヘッドレス実行）
- 注意: Linux の Wayland 環境では一部機能（Pillow の `ImageGrab` やグローバル入力フック）が制約を受けるため、X11 セッションまたは `xvfb-run` による回避を推奨

## セットアップ

### 1. リポジトリ取得

```bash
git clone <repository-url>
cd GameMacroAssistant
```

### 2. 仮想環境（推奨）

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 3. 依存関係インストール

requirements.txt は OS に応じて依存を解決します。`pywin32` は Windows 限定です。

```bash
pip install -U pip
pip install -r requirements.txt
```

Linux では Tkinter と Xvfb を追加インストールしてください（GUI テストや一部 UI モジュールで必要）。

```bash
sudo apt-get update
sudo apt-get install -y python3-tk xvfb
```

## 品質チェック / テスト（DoD）

本プロジェクトの完了の定義（Definition of Done）は以下 2 点の 0 終了です。

```bash
ruff check .
ruff format . --check

# GUI ありの通常実行（開発端末）
python -m pytest -q

# GUI 環境がない場合（CI やヘッドレス環境）
xvfb-run -a python -m pytest -q

# Wayland を使用している場合の推奨（X11 代替が難しいとき）
# → ヘッドレスであっても Xvfb により X11 相当の環境を提供できます
# → 開発端末でもテストは上記 xvfb-run で実行可能です
```

補足:
- Linux では `pywin32` はインストールされません（`platform_system == "Windows"` マーカー）。
- テストは GUI 依存があるため、ヘッドレスでは `xvfb-run` の利用を推奨します。

## 実行方法（動作確認）

入力キャプチャの簡易テスト:

```bash
python src/main.py --test-input
```

画面の指示に従い、3 種類のクリックと文字入力（空白含む）を行い、ESC で終了します。結果は `input_capture_test_results.json` にエクスポートされます。

## Windows でのデプロイ（PyInstaller）

CI と同等の手順（ローカルでも可）:

```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller -F -w src/main.py --name GameMacroAssistant
# 生成物: dist/GameMacroAssistant.exe
```

## CI（GitHub Actions）

- トリガー: 全ブランチ `push` / `pull_request`、手動実行 `workflow_dispatch`
- 公式アクションのみ使用: `actions/checkout@v4`, `actions/setup-python@v5`, `actions/cache@v4`, `actions/upload-artifact@v4`
- pip キャッシュ: Linux `~/.cache/pip` / Windows `~\AppData\Local\pip\Cache`

ジョブ構成:
- Linux: `python3-tk` と `xvfb` を導入 → `ruff check` → `ruff format --check` → `xvfb-run -a pytest`
- Windows: `pytest` 実行 → `pyinstaller` による `.exe` ビルド → `GameMacroAssistant-win` としてアーティファクトアップロード

## アーキテクチャ（概要）

- 入力記録: グローバルフックでマウス／キーボードをキャプチャ、ESC で停止。
- 画面キャプチャ: フルスクリーン対応。失敗時は Windows の GDI にフォールバック（`Err-CAP` をログ）。
- ビジュアルエディタ: ブロック表現、ドラッグ＆ドロップ並べ替え、矩形選択、ダブルクリック編集、アンドゥ／リドゥ。
- 実行エンジン: グローバルホットキー（例: Ctrl+Shift+F10）、画像マッチング条件、タイムアウト（`Err-TMO` ログ）、トレイ進捗表示。
- ファイル形式: パスワード保護付き暗号化 `.gma.json`、最大 3 回のパスワード検証とエラーフィードバック。

## トラブルシューティング

- Linux で `tkinter` ImportError: `sudo apt-get install -y python3-tk` を実行。
- ヘッドレス実行で GUI 関連エラー: `xvfb-run -a python -m pytest -q` を使用。
- Windows で `pywin32` 未解決: `pip install -r requirements.txt` を再実行（環境マーカーにより Windows のみ解決）。
- グローバル入力の権限問題: Windows では管理者権限での実行を検討。

## コントリビュート

1. フォークしブランチを作成（例: `git checkout -b feat/feature-name`）
2. 変更をコミット（`git commit -m "feat: ..."`）
3. プッシュして PR を作成
4. PR は CI がグリーン（DoD 満たす）であること

## 開発環境（Linux）

本プロジェクトは最終的に Windows を主要プラットフォームとしますが、開発は Linux 上でも可能です。以下の手順で Linux 開発環境を構築してください。

### 必須パッケージ（Debian/Ubuntu 例）

```
sudo apt-get update && \
  sudo apt-get install -y \
  python3-venv python3-pip python3-tk \
  build-essential libjpeg-dev zlib1g-dev libpng-dev \
  xvfb
```

注意点:
- Tkinter は Linux では `python3-tk` パッケージが必要です。
- 画面キャプチャや GUI テストをヘッドレスで実行する場合は `xvfb` を利用してください（CI でも採用）。
- Wayland セッションでは `ImageGrab`（Pillow）やグローバル入力フックの制約によりキャプチャ／テストが失敗することがあります。X11 セッションでの実行、または `xvfb-run` による回避を推奨します。
- Windows 専用依存の `pywin32` は Linux ではインストールされません（環境マーカーで制御済み）。

### 仮想環境と依存関係

```
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### テストとコード品質（Definition of Done 準拠）

```
# すべてのテスト（ディスプレイがない場合、GUIテストは自動スキップ）
python -m pytest -q

# ヘッドレスで GUI テストも通したい場合（Wayland 回避含む）
xvfb-run -a python -m pytest -q

# Lint / Format チェック
ruff check .
ruff format . --check
```

### 動作確認

- 非対話テスト: `python src/main.py --test-input-file input_capture_test_results.json`
- 対話テスト（要ディスプレイ）: `python src/main.py --test-input`（ESC で停止）

### Wayland の制約と回避策

- Wayland 環境では以下の制約が発生する可能性があります。
  - Pillow の `ImageGrab` によるスクリーンキャプチャ失敗
  - グローバル入力フック（`pynput`）の権限・イベント取得の制約
- 推奨回避策:
  - 可能なら X11 セッションで実行
  - もしくは `xvfb-run -a` を用いてヘッドレスの X サーバ（Xvfb）上でテストを実行

例（テスト実行）:

```
xvfb-run -a python -m pytest -q
```

### Linux の画面キャプチャと mss フォールバック（背景）

- 本プロジェクトでは、Linux での安定した画面キャプチャのために `mss` をフォールバック候補として採用予定です（Issue #23, #24）。
- 目的: Wayland や権限制約により `ImageGrab` が失敗する環境でもキャプチャの成功率を高める。
- 現状: 既定では Pillow の `ImageGrab` を使用中。今後の実装で、失敗時に `mss` へ自動フォールバックする計画です。
- 最小手順（将来のフォールバック有効化に備える場合）:
  - `pip install mss`
  - 以降のリリースで実装が有効化されると、自動的に `mss` が利用される想定です（追加設定なし）。

## デプロイ（Windows）

最終配布は Windows 向けの実行ファイルを想定します。ビルドは Windows 上で行ってください（クロスビルドは非推奨）。

### 手順（例: PyInstaller）

```
pip install pyinstaller
pyinstaller -F -w src/main.py --name GameMacroAssistant
```

- 生成物は `dist/GameMacroAssistant.exe`
- グローバル入力フックには管理者権限が必要な場合があります
- `pywin32` は Windows 上で自動的にインストールされます

## CI 推奨構成

- Linux ジョブ: `ruff` のチェック、`pytest`（必要に応じて `xvfb-run`）
- Windows ジョブ: `pytest` 実行と PyInstaller によるビルド、成果物の保存

GitHub Actions のサンプルは `.github/workflows/ci.yml` を参照してください。

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

## Security Considerations

- **Input Capture**: Application requires elevated privileges for global input monitoring
- **Data Storage**: Recorded macros can contain sensitive information
- **Network**: Application does not transmit data over network by default
- **Encryption**: Macro files are encrypted with user-provided passwords

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and bug reports:
1. Check the troubleshooting section above
2. Search existing issues in the repository
3. Create a new issue with detailed reproduction steps

## Changelog

### v0.2.0 (Current)
- Fixed critical space character recording bug
- Added comprehensive error handling with structured error codes
- Enhanced mouse button support (left, right, middle)
- Improved test coverage and integration tests
- Added production-quality logging and debugging

### v0.1.0
- Initial implementation of global input capture
- Basic mouse click and keyboard recording
- Simple integration test framework
