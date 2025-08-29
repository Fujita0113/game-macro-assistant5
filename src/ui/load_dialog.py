"""
Load Dialog UI component for macro file loading.

This module provides a modal dialog for selecting and loading encrypted macro files
with password authentication. Uses MacroFileManager for actual file operations.
"""

import tkinter as tk
from tkinter import ttk, filedialog
from typing import Optional
from src.core.macro_data import MacroRecording
from src.core.file_encryption import MacroFileManager, PasswordValidationError


class LoadDialog:
    """Modal dialog for loading encrypted macro files."""

    def __init__(self, parent: tk.Tk, success_delay_ms: int = 1000):
        """
        Initialize the load dialog.

        Args:
            parent: Parent window for modal behavior
            success_delay_ms: Delay in milliseconds before auto-closing on success (default: 1000)
        """
        self.parent = parent
        self.result: Optional[MacroRecording] = None
        self.file_manager = MacroFileManager()
        self.success_delay_ms = success_delay_ms

        # Create modal dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title('マクロファイル読み込み')
        self.dialog.geometry('500x300')
        self.dialog.resizable(False, False)

        # Make modal
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Variables for UI components
        self.file_path_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.message_var = tk.StringVar()

        # UI components (initialized in _setup_ui)
        self.load_button = None
        self.cancel_button = None
        self.browse_button = None
        self.message_label = None
        self.password_entry = None
        self.progress_label = None

        self._setup_ui()
        self._center_dialog()

    def _setup_ui(self):
        """Set up the user interface elements."""
        # Main frame with padding
        main_frame = ttk.Frame(self.dialog, padding='20')
        main_frame.grid(row=0, column=0, sticky='nsew')

        # Configure grid weights
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # File selection section
        ttk.Label(main_frame, text='ファイル選択:').grid(
            row=0, column=0, sticky='w', pady=(0, 5)
        )

        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 15))
        file_frame.columnconfigure(0, weight=1)

        # File path entry (read-only)
        file_path_entry = ttk.Entry(
            file_frame, textvariable=self.file_path_var, state='readonly'
        )
        file_path_entry.grid(row=0, column=0, sticky='ew', padx=(0, 10))

        # Browse button
        self.browse_button = ttk.Button(
            file_frame, text='参照...', command=self._on_browse_clicked
        )
        self.browse_button.grid(row=0, column=1)

        # Password section
        ttk.Label(main_frame, text='パスワード:').grid(
            row=2, column=0, sticky='w', pady=(0, 5)
        )

        self.password_entry = ttk.Entry(
            main_frame, textvariable=self.password_var, show='*', width=30
        )
        self.password_entry.grid(
            row=3, column=0, columnspan=2, sticky='ew', pady=(0, 15)
        )

        # Message label for success/error messages
        self.message_label = ttk.Label(
            main_frame, textvariable=self.message_var, foreground='red'
        )
        self.message_label.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(0, 5))

        # Progress label (hidden by default)
        self.progress_label = ttk.Label(main_frame, text='', foreground='blue')
        self.progress_label.grid(
            row=5, column=0, columnspan=2, sticky='ew', pady=(0, 10)
        )

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, sticky='ew')
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        # Load and Cancel buttons
        self.load_button = ttk.Button(
            button_frame, text='読み込み', command=self._on_load_clicked
        )
        self.load_button.grid(row=0, column=0, padx=(0, 10), pady=(10, 0))

        self.cancel_button = ttk.Button(
            button_frame, text='キャンセル', command=self._on_cancel_clicked
        )
        self.cancel_button.grid(row=0, column=1, padx=(10, 0), pady=(10, 0))

    def _center_dialog(self):
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()

        # Get dialog size
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()

        # Get parent position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Calculate center position
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.dialog.geometry(f'{width}x{height}+{x}+{y}')

    def _on_browse_clicked(self):
        """Handle browse button click to select file."""
        file_path = filedialog.askopenfilename(
            parent=self.dialog,
            title='マクロファイルを選択',
            filetypes=[('GMAssistant files', '*.gma.json'), ('All files', '*.*')],
        )

        if file_path:
            self.file_path_var.set(file_path)
            self.message_var.set('')  # Clear any previous messages

    def _on_load_clicked(self):
        """Handle load button click."""
        # Basic validation
        file_path = self.file_path_var.get()
        password = self.password_var.get()

        if not file_path:
            self.message_var.set('ファイルを選択してください')
            return

        if not password:
            self.message_var.set('パスワードを入力してください')
            return

        try:
            # Clear previous messages
            self.message_var.set('')

            # Show loading progress and disable UI
            self._show_loading_progress()

            # Load and decrypt the file using MacroFileManager
            decrypted_data = self.file_manager.load_macro_file(file_path, password)

            # Convert dictionary to MacroRecording object
            macro_recording = MacroRecording.from_dict(decrypted_data)
            self._set_result(macro_recording)

            # Show success message
            self.message_var.set('読み込み完了しました')

            # Close dialog automatically after success
            self.dialog.after(self.success_delay_ms, self.dialog.destroy)

        except PasswordValidationError as e:
            # Use robust error classification instead of string matching
            error_message = self._classify_password_error(e)
            self.message_var.set(error_message)
        except Exception as e:
            # Handle other unexpected errors
            self.message_var.set(f'予期しないエラーが発生しました: {str(e)}')
        finally:
            # Always hide loading progress and restore UI
            self._hide_loading_progress()

    def _classify_password_error(self, exception: PasswordValidationError) -> str:
        """
        Classify PasswordValidationError based on exception attributes rather than string matching.

        Args:
            exception: The PasswordValidationError to classify

        Returns:
            Appropriate user-friendly error message
        """
        # Check if exception has error_code attribute for robust classification
        if hasattr(exception, 'error_code'):
            error_code = exception.error_code
            if error_code == 'INVALID_PASSWORD':
                return 'パスワードが正しくありません'
            elif error_code == 'MAX_ATTEMPTS_EXCEEDED':
                return 'パスワード試行回数が上限に達しました'
            elif error_code == 'FILE_CORRUPTED':
                return 'ファイルが破損しています'
            elif error_code == 'FILE_LOAD_FAILED':
                return 'ファイルの読み込みに失敗しました'

        # Fallback to string matching for backward compatibility
        error_msg = str(exception)
        if 'Invalid password' in error_msg:
            return 'パスワードが正しくありません'
        elif 'Maximum password attempts exceeded' in error_msg:
            return 'パスワード試行回数が上限に達しました'
        elif 'File appears to be corrupted' in error_msg:
            return 'ファイルが破損しています'
        elif 'Failed to load file' in error_msg:
            return 'ファイルの読み込みに失敗しました'
        else:
            # Generic fallback for unknown errors
            return f'エラー: {error_msg}'

    def _show_loading_progress(self):
        """Show loading progress and disable user interaction."""
        self.progress_label.config(text='読み込み中...')
        self.load_button.config(state='disabled')
        self.browse_button.config(state='disabled')
        self.dialog.update_idletasks()  # Force UI update

    def _hide_loading_progress(self):
        """Hide loading progress and re-enable user interaction."""
        self.progress_label.config(text='')
        self.load_button.config(state='normal')
        self.browse_button.config(state='normal')

    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        self._set_result(None)
        self.dialog.destroy()

    def show_modal(self) -> Optional[MacroRecording]:
        """
        Show dialog modally and return result.

        Returns:
            MacroRecording object if successful, None if cancelled
        """
        # Wait for dialog to be closed
        self.dialog.wait_window()

        # Ensure type safety - result must be None or MacroRecording
        assert self.result is None or isinstance(self.result, MacroRecording), (
            f'Result must be None or MacroRecording, got {type(self.result)}'
        )

        return self.result

    def _set_result(self, result: Optional[MacroRecording]) -> None:
        """
        Set the dialog result with type validation.

        Args:
            result: MacroRecording object or None
        """
        assert result is None or isinstance(result, MacroRecording), (
            f'Result must be None or MacroRecording, got {type(result)}'
        )

        self.result = result
