# Code Style and Conventions

## Formatting and Linting
- **Primary Tool**: Ruff (≥0.12.0) - replaces black and flake8
- **Line Length**: 88 characters (configured in pyproject.toml)
- **Quote Style**: Single quotes enforced via ruff format
- **Ignored Rules**: E501 (line length handled by ruff)
- **Selected Rules**: "E" (pycodestyle errors), "F" (Pyflakes errors)

## Naming Conventions
Based on analysis of existing code:
- **Classes**: PascalCase (e.g., `InputCaptureManager`, `ErrorCodes`)
- **Functions/Methods**: snake_case (e.g., `start_recording`, `stop_recording`)
- **Variables**: snake_case (e.g., `_recording`, `_recorded_events`)
- **Constants**: UPPER_SNAKE_CASE (implied from error codes)
- **Private Methods/Variables**: Leading underscore (e.g., `_on_mouse_click`, `_recording`)

## Type Hints
- **Usage**: Extensive type hints used throughout codebase
- **Imports**: `from typing import List, Optional` style
- **Examples**:
  - `_recorded_events: List[InputEvent] = []`
  - `_mouse_listener: Optional[mouse.Listener] = None`

## Docstrings
- **Style**: Standard Python docstrings with triple quotes
- **Example**: `"""Main application entry point."""`
- **Coverage**: Methods and functions have descriptive docstrings

## Code Organization
- **Imports**: Standard library first, then third-party, then local imports
- **Class Structure**: 
  - Instance variables defined in `__init__`
  - Public methods first, private methods last
  - Threading-related variables clearly marked (e.g., `_recording_lock`)

## Error Handling
- **Structured Error Codes**: Enum-based error codes (ErrorCodes class)
- **Logging**: Comprehensive logging with logger instances
- **Exception Handling**: Try-except blocks with specific error messages

## Threading Patterns
- **Lock Usage**: `threading.Lock()` for thread safety
- **Event Objects**: `threading.Event()` for signaling
- **Optional Threading**: `Optional[threading.Thread]` type hints

## Testing Patterns
- **Test Classes**: `TestInputCaptureManager` class-based structure
- **File Naming**: `test_*.py` pattern
- **Configuration**: pytest.ini with verbose output and short tracebacks