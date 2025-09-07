# GameMacroAssistant

A desktop automation tool for PC games that allows users to record, edit, and replay mouse/keyboard operations with visual recognition capabilities.

## Features

- **Global Input Capture**: Records mouse clicks (left, right, middle) and keyboard input system-wide
- **Space Character Support**: Properly captures space characters in text input
- **Visual Recognition**: Screen capture with native resolution support and GDI fallback
- **Error Handling**: Comprehensive error logging with structured error codes
- **Secure Storage**: Encrypted macro files with password protection
- **Real-time Execution**: Global hotkey triggering with progress indication

## Requirements

- Python 3.8+
- Windows 10/11 (primary platform)
- Administrator privileges (for global input capture)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd GameMacroAssistant
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

Run the integration test to ensure everything is working:

```bash
python src/main.py --test-input
```

## Usage

### Basic Recording Test

To test the input capture functionality:

```bash
python src/main.py --test-input
```

Follow the on-screen instructions:
1. LEFT-click at one location
2. RIGHT-click at another location  
3. MIDDLE-click (scroll wheel) at a third location
4. Type 'Hello World Test' (with spaces)
5. Press ESC to stop recording

### Running Unit Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_input_capture.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## Architecture

### Core Components

- **InputCaptureManager**: Handles global mouse and keyboard event capture
- **Events System**: Structured event representation for mouse clicks and keyboard input
- **Error Handling**: Unified error codes and logging system

### Error Codes

The system uses structured error codes for troubleshooting:

- `Err-CAP-001`: Failed to initialize input capture
- `Err-CAP-002`: Runtime error during capture
- `Err-CAP-003`: Permission denied for input capture
- `Err-CAP-004`: System resources unavailable

### Supported Input Events

**Mouse Events:**
- Left button clicks
- Right button clicks  
- Middle button clicks (scroll wheel)
- Coordinates and timestamps

**Keyboard Events:**
- Character keys (a-z, 0-9, symbols)
- Space characters (properly handled)
- Special keys (ESC for stop recording)
- Key press and release events

## Development

### Project Structure

```
GameMacroAssistant/
├── src/
│   ├── core/
│   │   ├── input_capture.py    # Main input capture logic
│   │   └── events.py           # Event type definitions
│   └── main.py                 # Application entry point
├── tests/
│   ├── test_input_capture.py   # Unit tests
│   └── test_integration.py     # Integration tests
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

### Adding New Features

1. **Event Types**: Add new event types in `src/core/events.py`
2. **Capture Logic**: Extend `InputCaptureManager` in `src/core/input_capture.py`
3. **Tests**: Add corresponding tests in `tests/`
4. **Documentation**: Update this README with new functionality

### Code Quality

Run linting and formatting:

```bash
# Format code
black src/ tests/

# Check code style  
flake8 src/ tests/

# Type checking (if using type hints)
mypy src/
```

## Troubleshooting

### Common Issues

**Permission Errors (Err-CAP-003)**
- Run as administrator on Windows
- Check antivirus software blocking input capture
- Verify pynput permissions

**Resource Unavailable (Err-CAP-004)**
- Close other applications using input capture
- Restart the application
- Check system resource usage

**Installation Issues**
- Ensure Python 3.8+ is installed
- Use virtual environment to avoid conflicts
- Install Visual C++ redistributables on Windows

### Debug Logging

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.getLogger('src.core.input_capture').setLevel(logging.DEBUG)
```

### Testing Issues

**Unit Tests Failing**
- Check Python path configuration
- Verify all dependencies are installed
- Run tests in virtual environment

**Integration Test Issues**
- Ensure GUI environment is available
- Check mouse/keyboard hardware functionality
- Verify administrator privileges

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

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
- 画面キャプチャやGUIテストをヘッドレスで実行する場合は `xvfb` を利用してください。
- Windows専用依存の `pywin32` は Linux ではインストールされません（環境マーカーで制御済み）。

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

# ヘッドレスでGUIテストも通したい場合
xvfb-run -a python -m pytest -q

# Lint / Format チェック
ruff check .
ruff format . --check
```

### 動作確認

- 非対話テスト: `python src/main.py --test-input-file input_capture_test_results.json`
- 対話テスト（要ディスプレイ）: `python src/main.py --test-input`（ESC で停止）

Wayland 環境では `ImageGrab` やグローバルフック（pynput）が制約を受ける場合があります。必要に応じて X11 セッションや `xvfb-run` を利用してください。

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
