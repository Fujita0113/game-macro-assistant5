# Architecture and Key Components

## Core Components

### 1. InputCaptureManager (`src/core/input_capture.py`)
- **Purpose**: Handles global mouse and keyboard event capture
- **Key Features**:
  - Thread-safe recording with `threading.Lock()`
  - Support for left, right, middle mouse clicks
  - Keyboard input capture including space characters
  - ESC key termination
- **Key Methods**:
  - `start_recording()`: Initialize and start input capture
  - `stop_recording()`: Clean shutdown of capture
  - `get_recorded_events()`: Retrieve captured events
  - `load_test_data()`: Load test data from file

### 2. Event System (`src/core/events.py`)
- **Purpose**: Structured event representation
- **Event Types**: Mouse clicks, keyboard input, timestamps
- **Integration**: Used by InputCaptureManager for event storage

### 3. Screen Capture System (`src/core/screen_capture.py`)
- **Purpose**: Handle fullscreen games with native resolution support
- **Features**: GDI fallback when native capture fails
- **Error Codes**: Logs `Err-CAP` codes for capture failures

### 4. Visual Editor (`src/ui/visual_editor.py`)
- **Purpose**: Block-based macro representation
- **Features**:
  - Drag-and-drop reordering
  - Image editing for condition screenshots
  - Undo/redo support (Ctrl+Z)

### 5. Main Application (`src/main.py`)
- **Entry Points**:
  - Standard GUI mode
  - `--test-input`: Integration test mode
  - `--test-input-file`: Non-interactive test with data file
- **Integration**: Connects UI components with core functionality

## Design Patterns

### Thread Safety
- **Locking**: `threading.Lock()` for critical sections
- **Events**: `threading.Event()` for signaling
- **Optional Threads**: Proper handling of background threads

### Error Handling
- **Structured Codes**: Enum-based error codes (ErrorCodes class)
- **Logging**: Comprehensive logging with logger instances
- **Graceful Degradation**: Fallback mechanisms for screen capture

### Event-Driven Architecture
- **Listeners**: Mouse and keyboard listeners from pynput
- **Callbacks**: Event handlers for input processing
- **State Management**: Recording state tracking

## Security Considerations

### Input Capture
- **Elevated Privileges**: Administrator rights required for global input monitoring
- **Data Sensitivity**: Recorded macros can contain sensitive information
- **Local Processing**: No network transmission by default

### File Storage
- **Encryption**: Macro files encrypted with user-provided passwords
- **Password Policy**: 8+ character requirement
- **Validation**: Three-attempt password validation

## Testing Architecture

### Test Structure
- **Unit Tests**: `tests/test_input_capture.py`
- **Integration Tests**: `tests/test_integration.py`
- **Screen Capture Tests**: `tests/test_screen_capture.py`
- **GUI Tests**: `tests/test_visual_editor_functionality.py`

### Test Configuration
- **pytest.ini**: Configured for verbose output, short tracebacks
- **Coverage**: pytest-cov integration
- **Fixtures**: Located in `tests/fixtures/`

### Test Types
- **Interactive Tests**: User input simulation
- **Non-interactive Tests**: File-based test data
- **Mock-based Tests**: Isolated component testing

## Configuration Management

### pyproject.toml
- **Ruff Configuration**: Line length, quote style, rule selection
- **Format Settings**: Single quotes, 88-character lines
- **Linting Rules**: E (pycodestyle), F (Pyflakes)

### Environment Requirements
- **Python Version**: 3.8+
- **Platform**: Windows 10/11 primary
- **Dependencies**: Managed via requirements.txt
- **Virtual Environment**: Recommended for development