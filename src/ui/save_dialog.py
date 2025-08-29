"""
Save dialog UI component for saving macro files.

This module provides a modal dialog for saving MacroRecording objects
to encrypted .gma.json files with password protection.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable
from src.core.macro_data import MacroRecording


class SaveDialog:
    """Modal dialog for saving macro files with password protection."""

    def __init__(
        self, parent: tk.Tk, macro_data: MacroRecording, save_callback: Callable
    ):
        """
        Initialize the save dialog.

        Args:
            parent: Parent window
            macro_data: MacroRecording object to save
            save_callback: Callback function for save operation
                         Should accept (filename: str, password: str, macro_data: Dict[str, Any])
        """
        self.root = parent
        self.macro_data = macro_data
        self.save_callback = save_callback

        # Create modal dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title('マクロファイルの保存')
        self.dialog.geometry('400x300')
        self.dialog.resizable(False, False)
        self.dialog.grab_set()  # Make it modal
        self.dialog.focus_set()

        # Center the dialog
        self._center_dialog()

        # Setup UI elements
        self._setup_ui()

    def _center_dialog(self):
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()

        # Get parent window position and size
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()

        # Calculate dialog position
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()

        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)

        self.dialog.geometry(f'+{x}+{y}')

    def _setup_ui(self):
        """Setup the user interface elements."""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding='20')
        main_frame.grid(row=0, column=0, sticky='nsew')

        # Configure grid weights
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame, text='マクロファイルの保存', font=('Arial', 12, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Filename input
        ttk.Label(main_frame, text='ファイル名:').grid(
            row=1, column=0, sticky='w', pady=(0, 10)
        )
        self.filename_entry = ttk.Entry(main_frame, width=30)
        self.filename_entry.grid(row=1, column=1, sticky='ew', pady=(0, 10))

        # Password input
        ttk.Label(main_frame, text='パスワード:').grid(
            row=2, column=0, sticky='w', pady=(0, 10)
        )
        self.password_entry = ttk.Entry(main_frame, show='*', width=30)
        self.password_entry.grid(row=2, column=1, sticky='ew', pady=(0, 10))

        # Confirm password input
        ttk.Label(main_frame, text='パスワード確認:').grid(
            row=3, column=0, sticky='w', pady=(0, 10)
        )
        self.confirm_password_entry = ttk.Entry(main_frame, show='*', width=30)
        self.confirm_password_entry.grid(row=3, column=1, sticky='ew', pady=(0, 10))

        # Message label for success/error messages
        self.message_label = ttk.Label(main_frame, text='', foreground='blue')
        self.message_label.grid(row=4, column=0, columnspan=2, pady=(10, 0))

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0))

        self.save_button = ttk.Button(
            buttons_frame, text='保存', command=self._perform_save
        )
        self.save_button.grid(row=0, column=0, padx=(0, 10))

        self.cancel_button = ttk.Button(
            buttons_frame, text='キャンセル', command=self._cancel
        )
        self.cancel_button.grid(row=0, column=1)

    def _perform_save(self):
        """Perform the save operation with validation."""
        # Get input values
        filename = self.filename_entry.get().strip()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        # Reset message
        self.message_label.config(text='', foreground='blue')

        # Validate inputs
        if not filename:
            self.message_label.config(
                text='ファイル名を入力してください', foreground='red'
            )
            return

        if len(password) < 8:
            self.message_label.config(
                text='パスワードは8文字以上で入力してください', foreground='red'
            )
            return

        if password != confirm_password:
            self.message_label.config(text='パスワードが一致しません', foreground='red')
            return

        # Add .gma.json extension if not present
        if not filename.endswith('.gma.json'):
            filename = filename + '.gma.json'

        try:
            # Call the save callback with MacroRecording.to_dict() data
            result = self.save_callback(
                filename=filename,
                password=password,
                macro_data=self.macro_data.to_dict(),
            )

            if result or result is None:  # Consider None as success for compatibility
                # Success
                self.message_label.config(text='保存に成功しました', foreground='green')
                # Close dialog after a brief delay
                self.dialog.after(1500, self.dialog.destroy)
            else:
                # Failure
                self.message_label.config(text='保存に失敗しました', foreground='red')

        except Exception:
            # Handle any exceptions from the callback
            self.message_label.config(text='保存に失敗しました', foreground='red')

    def _cancel(self):
        """Cancel the save operation and close dialog."""
        self.dialog.destroy()
