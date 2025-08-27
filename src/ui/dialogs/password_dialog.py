"""
Password input and setup dialogs for macro file security.

This module provides dialogs for password input and initial password setup
with validation and attempt tracking.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional


class PasswordDialog:
    """Dialog for entering password to open encrypted macro files."""

    def __init__(self, parent: tk.Widget, max_attempts: int = 3):
        """
        Initialize password input dialog.

        Args:
            parent: Parent widget
            max_attempts: Maximum number of password attempts allowed
        """
        self.parent = parent
        self.max_attempts = max_attempts
        self.attempts = 0
        self.password = None
        self.dialog = None

    def show(self, file_name: str = '') -> Optional[str]:
        """
        Show password input dialog.

        Args:
            file_name: Name of the file being opened (for display)

        Returns:
            Optional[str]: Password if successful, None if cancelled or max attempts reached
        """
        self.password = None
        self.attempts = 0

        # Create dialog window
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title('パスワード入力')
        self.dialog.geometry('350x200')
        self.dialog.resizable(False, False)

        # Make modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Center on parent
        self._center_dialog()

        self._setup_ui(file_name)

        # Focus on password entry
        self.password_entry.focus()

        # Wait for dialog to close
        self.dialog.wait_window()

        return self.password

    def _setup_ui(self, file_name: str):
        """Set up the dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding='20')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_text = 'マクロファイルを開くためのパスワードを入力してください。'
        if file_name:
            header_text = (
                f'ファイル "{file_name}" を開くためのパスワードを入力してください。'
            )

        header_label = ttk.Label(
            main_frame, text=header_text, wraplength=300, justify=tk.LEFT
        )
        header_label.pack(anchor=tk.W, pady=(0, 15))

        # Password input
        password_frame = ttk.Frame(main_frame)
        password_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(password_frame, text='パスワード:').pack(anchor=tk.W)

        self.password_entry = ttk.Entry(password_frame, show='*', font=('Arial', 10))
        self.password_entry.pack(fill=tk.X, pady=(5, 0))

        # Bind Enter key
        self.password_entry.bind('<Return>', lambda e: self._on_ok())

        # Show password checkbox
        self.show_password_var = tk.BooleanVar()
        show_password_cb = ttk.Checkbutton(
            main_frame,
            text='パスワードを表示',
            variable=self.show_password_var,
            command=self._toggle_password_visibility,
        )
        show_password_cb.pack(anchor=tk.W, pady=(0, 15))

        # Attempts info
        if self.attempts > 0:
            attempts_text = f'試行回数: {self.attempts}/{self.max_attempts}'
            if self.attempts >= self.max_attempts - 1:
                attempts_text += ' (最後の試行)'

            self.attempts_label = ttk.Label(
                main_frame, text=attempts_text, foreground='red'
            )
            self.attempts_label.pack(anchor=tk.W, pady=(0, 10))

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        # Buttons
        ttk.Button(button_frame, text='キャンセル', command=self._on_cancel).pack(
            side=tk.RIGHT, padx=(10, 0)
        )

        ttk.Button(button_frame, text='OK', command=self._on_ok).pack(side=tk.RIGHT)

    def _toggle_password_visibility(self):
        """Toggle password visibility."""
        if self.show_password_var.get():
            self.password_entry.config(show='')
        else:
            self.password_entry.config(show='*')

    def _on_ok(self):
        """Handle OK button click."""
        password = self.password_entry.get()

        if not password:
            messagebox.showerror(
                'エラー', 'パスワードを入力してください。', parent=self.dialog
            )
            return

        self.password = password
        self.dialog.destroy()

    def _on_cancel(self):
        """Handle Cancel button click."""
        self.password = None
        self.dialog.destroy()

    def _center_dialog(self):
        """Center dialog on parent window."""
        self.dialog.update_idletasks()

        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()

        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.dialog.geometry(f'{dialog_width}x{dialog_height}+{x}+{y}')

    def increment_attempts(self):
        """Increment attempt counter for retry scenario."""
        self.attempts += 1

    def is_max_attempts_reached(self) -> bool:
        """Check if maximum attempts have been reached."""
        return self.attempts >= self.max_attempts


class PasswordSetupDialog:
    """Dialog for setting up password for new macro files."""

    def __init__(self, parent: tk.Widget):
        """
        Initialize password setup dialog.

        Args:
            parent: Parent widget
        """
        self.parent = parent
        self.password = None
        self.dialog = None

    def show(self, file_name: str = '') -> Optional[str]:
        """
        Show password setup dialog.

        Args:
            file_name: Name of the file being saved (for display)

        Returns:
            Optional[str]: Password if successful, None if cancelled
        """
        self.password = None

        # Create dialog window
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title('パスワード設定')
        self.dialog.geometry('400x300')
        self.dialog.resizable(False, False)

        # Make modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Center on parent
        self._center_dialog()

        self._setup_ui(file_name)

        # Focus on password entry
        self.password_entry.focus()

        # Wait for dialog to close
        self.dialog.wait_window()

        return self.password

    def _setup_ui(self, file_name: str):
        """Set up the dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding='20')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_text = 'マクロファイルを暗号化するためのパスワードを設定してください。'
        if file_name:
            header_text = f'ファイル "{file_name}" を暗号化するためのパスワードを設定してください。'

        header_label = ttk.Label(
            main_frame, text=header_text, wraplength=350, justify=tk.LEFT
        )
        header_label.pack(anchor=tk.W, pady=(0, 15))

        # Password requirements
        requirements_text = '• 8文字以上で入力してください\n• 安全のため、推測されにくいパスワードを使用してください'
        requirements_label = ttk.Label(
            main_frame, text=requirements_text, foreground='gray', justify=tk.LEFT
        )
        requirements_label.pack(anchor=tk.W, pady=(0, 15))

        # Password input
        password_frame = ttk.Frame(main_frame)
        password_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(password_frame, text='パスワード:').pack(anchor=tk.W)

        self.password_entry = ttk.Entry(password_frame, show='*', font=('Arial', 10))
        self.password_entry.pack(fill=tk.X, pady=(5, 0))

        # Password confirmation
        confirm_frame = ttk.Frame(main_frame)
        confirm_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(confirm_frame, text='パスワード確認:').pack(anchor=tk.W)

        self.confirm_entry = ttk.Entry(confirm_frame, show='*', font=('Arial', 10))
        self.confirm_entry.pack(fill=tk.X, pady=(5, 0))

        # Bind Enter key
        self.confirm_entry.bind('<Return>', lambda e: self._on_ok())

        # Show password checkbox
        self.show_password_var = tk.BooleanVar()
        show_password_cb = ttk.Checkbutton(
            main_frame,
            text='パスワードを表示',
            variable=self.show_password_var,
            command=self._toggle_password_visibility,
        )
        show_password_cb.pack(anchor=tk.W, pady=(0, 15))

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        # Buttons
        ttk.Button(button_frame, text='キャンセル', command=self._on_cancel).pack(
            side=tk.RIGHT, padx=(10, 0)
        )

        ttk.Button(button_frame, text='OK', command=self._on_ok).pack(side=tk.RIGHT)

    def _toggle_password_visibility(self):
        """Toggle password visibility."""
        if self.show_password_var.get():
            self.password_entry.config(show='')
            self.confirm_entry.config(show='')
        else:
            self.password_entry.config(show='*')
            self.confirm_entry.config(show='*')

    def _on_ok(self):
        """Handle OK button click."""
        password = self.password_entry.get()
        confirm_password = self.confirm_entry.get()

        # Validate password
        validation_error = self._validate_password(password, confirm_password)
        if validation_error:
            messagebox.showerror('エラー', validation_error, parent=self.dialog)
            return

        self.password = password
        self.dialog.destroy()

    def _validate_password(self, password: str, confirm_password: str) -> Optional[str]:
        """
        Validate password input.

        Returns:
            Optional[str]: Error message if validation fails, None if valid
        """
        if not password:
            return 'パスワードを入力してください。'

        if len(password) < 8:
            return 'パスワードは8文字以上である必要があります。'

        if password != confirm_password:
            return 'パスワードと確認パスワードが一致しません。'

        return None

    def _on_cancel(self):
        """Handle Cancel button click."""
        self.password = None
        self.dialog.destroy()

    def _center_dialog(self):
        """Center dialog on parent window."""
        self.dialog.update_idletasks()

        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()

        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.dialog.geometry(f'{dialog_width}x{dialog_height}+{x}+{y}')
