# Tkinter Testing Error Fix Guide

## Quick Fix for Common Tkinter Test Errors

If you encounter Tkinter test failures, follow these steps:

### Error 1: `TclError: Can't find a usable init.tcl`

**Fix:** Add environment variables to your test fixture file:

```python
# In tests/conftest.py or test files
import os
import sys

if sys.platform == 'win32':
    python_root = os.path.dirname(sys.executable)
    tcl_path = os.path.join(python_root, 'tcl')
    if os.path.exists(tcl_path):
        os.environ['TCL_LIBRARY'] = os.path.join(tcl_path, 'tcl8.6')
        os.environ['TK_LIBRARY'] = os.path.join(tcl_path, 'tk8.6')
```

### Error 2: `RuntimeError: Too early to create image: no default root window`

**Fix:** Add `master` parameter to ImageTk.PhotoImage calls:

```python
# WRONG
photo = ImageTk.PhotoImage(image)

# CORRECT  
photo = ImageTk.PhotoImage(image, master=canvas)
```

### Error 3: Tests pass individually but fail together

**Fix:** Use unified session management in `conftest.py`:

```python
# Global Tkinter session management
_tk_session = None
_has_display = None

def _check_display():
    global _has_display, _tk_session
    if _has_display is not None:
        return _has_display
    
    try:
        _tk_session = tk.Tk()
        _tk_session.withdraw()
        _has_display = True
        return True
    except tk.TclError:
        _has_display = False
        return False

_check_display()

@pytest.fixture
def tk_root():
    global _tk_session
    
    if not _has_display:
        pytest.skip('No display available')
    
    # Ensure valid session
    if not _tk_session or not _tk_session.winfo_exists():
        _tk_session = tk.Tk()
        _tk_session.withdraw()
    
    # Clean up existing widgets
    for child in _tk_session.winfo_children():
        try:
            child.destroy()
        except tk.TclError:
            pass
    
    # Set as default root
    tk._default_root = _tk_session
    
    yield _tk_session
    
    # Post-test cleanup
    for child in _tk_session.winfo_children():
        try:
            child.destroy()
        except tk.TclError:
            pass
```

## Step-by-Step Resolution

1. **Check error message** - identify which pattern above applies
2. **Apply the fix** - modify your test files accordingly  
3. **Test individually**: `python -m pytest tests/test_file.py::test_name`
4. **Test together**: `python -m pytest tests/test_file.py`
5. **Verify**: All tests should now pass

## Reference Implementation

See `tests/conftest.py` and `tests/test_tkinter_regression.py` for working examples.

---

*This fix resolves the conftest.py TclError issue from 2024-08-28*