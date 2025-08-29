"""
Load dialog for encrypted macro files.

This module provides a dialog interface for loading encrypted .gma.json files
with password protection and error handling.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from typing import Optional, Callable, Dict, Any
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.file_encryption import MacroFileManager, PasswordValidationError


class LoadDialog:
    """Dialog for loading encrypted macro files."""

    def __init__(self, parent: Optional[tk.Tk] = None):
        """Initialize the load dialog."""
        self.parent = parent
        self.root: Optional[tk.Toplevel] = None
        self.result = None
        self.file_manager = MacroFileManager()

        # Callbacks
        self.on_file_loaded: Optional[Callable] = None

    def show(self) -> None:
        """Show the load dialog."""
        if self.parent:
            self.root = tk.Toplevel(self.parent)
        else:
            self.root = tk.Tk()

        self.root.title('マクロファイルを開く')
        self.root.geometry('400x150')
        self.root.resizable(False, False)
        self._setup_ui()

    def open_file(self) -> Optional[str]:
        """Open file selection dialog and return selected file path."""
        filename = filedialog.askopenfilename(
            title='マクロファイルを選択',
            filetypes=[('GameMacroAssistant files', '*.gma.json')],
            defaultextension='.gma.json',
        )
        return filename if filename else None

    def prompt_password(self) -> Optional[str]:
        """Prompt user for password input."""
        password = simpledialog.askstring(
            'パスワード入力', 'ファイルのパスワードを入力してください:', show='*'
        )
        return password

    def load_with_retry(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load file with password retry mechanism (up to 3 attempts)."""
        if not os.path.exists(file_path):
            messagebox.showerror('エラー', 'ファイルが見つかりません')
            return None

        attempts = 0
        max_attempts = 3

        while attempts < max_attempts:
            password = self.prompt_password()
            if not password:  # User cancelled
                return None

            try:
                data = self.file_manager.load_macro_file(file_path, password)
                return data
            except PasswordValidationError:
                attempts += 1
                remaining = max_attempts - attempts

                if remaining > 0:
                    messagebox.showerror(
                        'エラー', f'パスワードが違います。残り試行回数: {remaining}'
                    )
                else:
                    messagebox.showerror('エラー', 'パスワードが違います')
                    return None
            except Exception as e:
                messagebox.showerror(
                    'エラー', f'ファイルの読み込みに失敗しました: {str(e)}'
                )
                return None

        return None

    def _setup_ui(self):
        """Set up the user interface."""
        # Just a placeholder for now
        frame = ttk.Frame(self.root, padding='20')
        frame.pack(fill=tk.BOTH, expand=True)

        label = ttk.Label(frame, text='LoadDialog - Under Development')
        label.pack()
