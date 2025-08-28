# GameMacroAssistant Project Overview

## Project Purpose
GameMacroAssistant is a desktop automation tool for PC games that allows users to record, edit, and replay mouse/keyboard operations with visual recognition capabilities. It focuses on defensive automation (game assistance) rather than exploitative automation.

## Tech Stack
- **Language**: Python 3.8+
- **Platform**: Windows 10/11 (primary platform)
- **UI Framework**: tkinter (built-in)
- **Key Dependencies**:
  - pynput (≥1.7.6) - For global input capture
  - pillow (≥10.0.0) - For screenshot and image processing
  - cryptography (≥41.0.0) - For macro file encryption
  - pywin32 (≥306) - For Windows API access (GDI fallback)
  - pytest (≥7.0.0) - For testing
  - pytest-cov (≥4.0.0) - For test coverage
  - ruff (≥0.12.0) - For linting and formatting

## Core Architecture Components
### Recording System
- Global input capture for mouse and keyboard operations
- Screen capture with native resolution support and GDI fallback
- ESC key termination for recording sessions
- Error handling for capture failures (logs `Err-CAP` codes)

### Visual Editor
- Block-based macro representation with drag-and-drop reordering
- Image editing for condition screenshots (double-click to edit, rectangular selection)
- Undo/redo support (Ctrl+Z)

### Execution Engine  
- Global hotkey triggering (e.g., Ctrl+Shift+F10)
- Image matching for conditional execution
- Timeout handling with notification system (logs `Err-TMO` codes)
- Progress indication in system tray

### File Management
- Encrypted `.gma.json` file format with password protection (8+ characters)
- Three-attempt password validation with error feedback

## Project Structure
```
GameMacroAssistant/
├── src/
│   ├── core/              # Core components
│   │   ├── input_capture.py    # Main input capture logic
│   │   ├── events.py           # Event type definitions
│   │   ├── event_handler.py    # Event handling logic
│   │   ├── macro_data.py       # Macro data management
│   │   ├── screen_capture.py   # Screen capture functionality
│   │   └── __init__.py
│   ├── ui/                # User interface components
│   │   ├── main_window.py      # Main application window
│   │   ├── recording_controller.py # Recording control logic
│   │   ├── visual_editor.py    # Visual macro editor
│   │   └── __init__.py
│   ├── utils/             # Utility modules
│   │   ├── logging.py          # Logging utilities
│   │   └── __init__.py
│   └── main.py            # Application entry point
├── tests/
│   ├── fixtures/          # Test fixtures
│   ├── utils/            # Test utilities
│   ├── test_input_capture.py   # Unit tests
│   ├── test_integration.py     # Integration tests
│   ├── test_screen_capture.py  # Screen capture tests
│   ├── test_visual_editor_functionality.py # GUI tests
│   └── __init__.py
├── docs/                 # Documentation
├── requirements.txt      # Dependencies
├── pyproject.toml       # Configuration
├── pytest.ini          # Test configuration
├── CLAUDE.md           # Claude Code instructions
└── README.md           # Project documentation
```

## Error Handling
The system uses structured error codes:
- `Err-CAP-001`: Failed to initialize input capture
- `Err-CAP-002`: Runtime error during capture
- `Err-CAP-003`: Permission denied for input capture
- `Err-CAP-004`: System resources unavailable
- `Err-TMO`: Timeout errors during execution

## Supported Input Events
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