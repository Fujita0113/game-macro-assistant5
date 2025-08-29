"""
Save dialog UI for GameMacroAssistant.

Provides a dialog for saving macro recordings with password protection.
"""

import tkinter as tk
from tkinter import ttk


class SaveDialog:
    """Dialog for saving macro recordings with password protection."""

    def __init__(self, parent, macro_recording):
        """
        Initialize the save dialog.

        Args:
            parent: Parent tkinter window
            macro_recording: The MacroRecording to save
        """
        self.parent = parent
        self.macro_recording = macro_recording
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title('マクロを保存')
        self.dialog.geometry('400x300')
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self._center_dialog()

        # Set up UI
        self._setup_ui()

    def _center_dialog(self):
        """Center the dialog on parent window."""
        self.dialog.update_idletasks()
        x = (
            self.parent.winfo_x()
            + (self.parent.winfo_width() // 2)
            - (self.dialog.winfo_width() // 2)
        )
        y = (
            self.parent.winfo_y()
            + (self.parent.winfo_height() // 2)
            - (self.dialog.winfo_height() // 2)
        )
        self.dialog.geometry(f'+{x}+{y}')

    def _setup_ui(self):
        """Set up the dialog UI elements."""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding='20')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # File name field
        ttk.Label(main_frame, text='ファイル名:').pack(anchor='w', pady=(0, 5))
        self.filename_entry = ttk.Entry(main_frame, width=40)
        self.filename_entry.pack(fill='x', pady=(0, 15))

        # Password field
        ttk.Label(main_frame, text='パスワード (8文字以上):').pack(
            anchor='w', pady=(0, 5)
        )
        self.password_entry = ttk.Entry(main_frame, width=40, show='*')
        self.password_entry.pack(fill='x', pady=(0, 15))

        # Password confirmation field
        ttk.Label(main_frame, text='パスワード確認:').pack(anchor='w', pady=(0, 5))
        self.password_confirm_entry = ttk.Entry(main_frame, width=40, show='*')
        self.password_confirm_entry.pack(fill='x', pady=(0, 15))

        # Error message label
        self.error_label = ttk.Label(main_frame, text='', foreground='red')
        self.error_label.pack(pady=(0, 15))

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))

        # Buttons
        ttk.Button(button_frame, text='キャンセル', command=self._on_cancel).pack(
            side='right', padx=(10, 0)
        )
        ttk.Button(button_frame, text='保存', command=self._on_save).pack(side='right')

    def _on_save(self):
        """Handle save button click."""
        # Clear previous error messages
        self.error_label.config(text='')

        # Get input values
        filename = self.filename_entry.get().strip()
        password = self.password_entry.get()
        password_confirm = self.password_confirm_entry.get()

        # Validate filename
        if not filename:
            self.error_label.config(text='ファイル名を入力してください')
            return

        # Validate password length
        if len(password) < 8:
            self.error_label.config(text='パスワードは8文字以上で入力してください')
            return

        # Validate password confirmation
        if password != password_confirm:
            self.error_label.config(text='パスワードが一致しません')
            return

        # All validations passed - save the file
        self.result = 'saved'
        self.dialog.destroy()

    def _on_cancel(self):
        """Handle cancel button click."""
        self.result = 'cancelled'
        self.dialog.destroy()
