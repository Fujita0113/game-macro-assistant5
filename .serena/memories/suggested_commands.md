# Suggested Commands for Development

## Testing Commands
```bash
# Run all tests with verbose output
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_input_capture.py -v
python -m pytest tests/test_integration.py -v
python -m pytest tests/test_screen_capture.py -v
python -m pytest tests/test_visual_editor_functionality.py -v

# Run tests with coverage report
python -m pytest tests/ --cov=src --cov-report=html

# Run tests with short traceback
python -m pytest tests/ --tb=short -v
```

## Linting and Formatting Commands
```bash
# Check code style and errors
ruff check .

# Format code (dry run - check what would be changed)
ruff format . --check

# Actually format code
ruff format .

# Fix auto-fixable issues
ruff check . --fix
```

## Application Run Commands
```bash
# Run main application
python src/main.py

# Run input capture integration test
python src/main.py --test-input

# Run non-interactive input test with data file
python src/main.py --test-input-file <filename>
```

## Development Setup Commands
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python src/main.py --test-input
```

## Git and Version Control Commands (Windows)
```bash
# Basic git operations
git status
git add .
git commit -m "commit message"
git push origin branch-name

# Create and switch to new branch
git checkout -b feature/branch-name

# Merge branch
git merge branch-name
```

## Windows System Commands
```bash
# List files and directories
dir
dir /s  # recursive

# Find files
findstr /s /i "pattern" *.py  # search in Python files

# Process management
tasklist | findstr "python"  # find Python processes
```

## Additional Utility Commands
```bash
# Check Python version
python --version

# Check installed packages
pip list

# Check package dependencies
pip show package-name

# Run Python module
python -m module.name
```

## Important Notes
- Always run from project root directory
- Use virtual environment for development
- Administrator privileges required for global input capture
- Tests may require GUI environment to run properly