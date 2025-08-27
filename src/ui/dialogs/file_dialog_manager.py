"""
File dialog manager for macro file operations.

This module provides centralized management of file dialogs for saving
and loading encrypted macro files with proper validation and error handling.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from typing import Optional
import logging

from ...core.macro_data import MacroRecording
from ...data.repositories.file_system_macro_repository import FileSystemMacroRepository
from ...data.repositories.macro_repository import (
    RepositoryError,
    InvalidPasswordError,
    CorruptedFileError,
)
from ...data.backup.backup_manager import BackupManager, BackupError
from .password_dialog import PasswordDialog, PasswordSetupDialog


class FileDialogManager:
    """Manager for file save/load operations with dialogs."""

    def __init__(self, parent: tk.Widget):
        """
        Initialize file dialog manager.

        Args:
            parent: Parent widget for dialogs
        """
        self.parent = parent
        self.repository = FileSystemMacroRepository()
        self.backup_manager = BackupManager()
        self.logger = logging.getLogger(__name__)

    def save_macro(self, recording: MacroRecording, initial_filename: str = '') -> bool:
        """
        Show save dialog and save macro with password protection.

        Args:
            recording: MacroRecording to save
            initial_filename: Initial filename suggestion

        Returns:
            bool: True if save successful, False if cancelled or failed
        """
        try:
            # Show file save dialog
            file_path = self._show_save_dialog(initial_filename)
            if not file_path:
                return False  # User cancelled

            # Show password setup dialog
            password_dialog = PasswordSetupDialog(self.parent)
            password = password_dialog.show(file_path.name)
            if not password:
                return False  # User cancelled

            # Create backup if file exists
            if file_path.exists():
                try:
                    self.backup_manager.create_backup(file_path)
                except BackupError as e:
                    self.logger.warning(f'Failed to create backup: {e}')
                    # Continue with save even if backup fails

            # Save the macro
            success = self.repository.save(recording, file_path, password)
            if success:
                messagebox.showinfo(
                    '保存完了',
                    f'マクロファイルが正常に保存されました。\n\nファイル: {file_path.name}',
                    parent=self.parent,
                )
                return True
            else:
                messagebox.showerror(
                    '保存エラー',
                    'マクロファイルの保存に失敗しました。',
                    parent=self.parent,
                )
                return False

        except RepositoryError as e:
            messagebox.showerror(
                '保存エラー',
                f'マクロファイルの保存に失敗しました。\n\nエラー: {e}',
                parent=self.parent,
            )
            return False
        except Exception as e:
            self.logger.error(f'Unexpected error during save: {e}')
            messagebox.showerror(
                '予期しないエラー',
                f'保存中に予期しないエラーが発生しました。\n\nエラー: {e}',
                parent=self.parent,
            )
            return False

    def load_macro(self) -> Optional[MacroRecording]:
        """
        Show load dialog and load macro with password input.

        Returns:
            Optional[MacroRecording]: Loaded macro recording, None if cancelled or failed
        """
        try:
            # Show file open dialog
            file_path = self._show_open_dialog()
            if not file_path:
                return None  # User cancelled

            # Show password input dialog with retry logic
            password_dialog = PasswordDialog(self.parent, max_attempts=3)

            while not password_dialog.is_max_attempts_reached():
                password = password_dialog.show(file_path.name)
                if not password:
                    return None  # User cancelled

                try:
                    # Try to load the macro
                    recording = self.repository.load(file_path, password)

                    messagebox.showinfo(
                        '読み込み完了',
                        f'マクロファイルが正常に読み込まれました。\n\nファイル: {file_path.name}\n操作数: {recording.operation_count}',
                        parent=self.parent,
                    )
                    return recording

                except InvalidPasswordError:
                    password_dialog.increment_attempts()

                    if password_dialog.is_max_attempts_reached():
                        messagebox.showerror(
                            'アクセス拒否',
                            'パスワードが3回連続で間違いました。\nファイルの読み込みを中止します。',
                            parent=self.parent,
                        )
                        return None
                    else:
                        messagebox.showerror(
                            'パスワードエラー',
                            f'パスワードが間違っています。\n\n残り試行回数: {password_dialog.max_attempts - password_dialog.attempts}',
                            parent=self.parent,
                        )
                        continue

            return None

        except FileNotFoundError:
            messagebox.showerror(
                'ファイルエラー',
                '指定されたファイルが見つかりません。',
                parent=self.parent,
            )
            return None
        except CorruptedFileError as e:
            messagebox.showerror(
                'ファイル破損エラー',
                f'ファイルが破損しているか、無効な形式です。\n\nエラー: {e}',
                parent=self.parent,
            )
            return None
        except RepositoryError as e:
            messagebox.showerror(
                '読み込みエラー',
                f'マクロファイルの読み込みに失敗しました。\n\nエラー: {e}',
                parent=self.parent,
            )
            return None
        except Exception as e:
            self.logger.error(f'Unexpected error during load: {e}')
            messagebox.showerror(
                '予期しないエラー',
                f'読み込み中に予期しないエラーが発生しました。\n\nエラー: {e}',
                parent=self.parent,
            )
            return None

    def _show_save_dialog(self, initial_filename: str = '') -> Optional[Path]:
        """Show file save dialog."""
        # Default to user's Documents folder
        initial_dir = Path.home() / 'Documents'

        # If initial filename doesn't have extension, add it
        if initial_filename and not initial_filename.endswith('.gma.json'):
            initial_filename += '.gma.json'

        file_path = filedialog.asksaveasfilename(
            parent=self.parent,
            title='マクロファイルを保存',
            defaultextension='.gma.json',
            filetypes=[
                ('GameMacroAssistant ファイル', '*.gma.json'),
                ('すべてのファイル', '*.*'),
            ],
            initialdir=str(initial_dir),
            initialfile=initial_filename,
        )

        return Path(file_path) if file_path else None

    def _show_open_dialog(self) -> Optional[Path]:
        """Show file open dialog."""
        # Default to user's Documents folder
        initial_dir = Path.home() / 'Documents'

        file_path = filedialog.askopenfilename(
            parent=self.parent,
            title='マクロファイルを開く',
            filetypes=[
                ('GameMacroAssistant ファイル', '*.gma.json'),
                ('すべてのファイル', '*.*'),
            ],
            initialdir=str(initial_dir),
        )

        return Path(file_path) if file_path else None

    def show_backup_management_dialog(self, file_path: Path):
        """
        Show backup management dialog for a specific file.

        Args:
            file_path: Path to the macro file
        """
        try:
            backups = self.backup_manager.list_backups(file_path)

            if not backups:
                messagebox.showinfo(
                    'バックアップ管理',
                    f'"{file_path.name}" のバックアップファイルは見つかりませんでした。',
                    parent=self.parent,
                )
                return

            # Create backup management dialog
            backup_dialog = BackupManagementDialog(
                self.parent, file_path, backups, self.backup_manager
            )
            backup_dialog.show()

        except Exception as e:
            self.logger.error(f'Error showing backup dialog: {e}')
            messagebox.showerror(
                'エラー',
                f'バックアップ管理ダイアログの表示に失敗しました。\n\nエラー: {e}',
                parent=self.parent,
            )

    def get_file_statistics(self, directory_path: Path) -> dict:
        """
        Get statistics about macro files in a directory.

        Args:
            directory_path: Directory to analyze

        Returns:
            dict: Statistics information
        """
        try:
            # Get macro files
            macro_files = self.repository.list_recordings(directory_path)

            # Get backup statistics
            backup_stats = self.backup_manager.get_backup_statistics(directory_path)

            return {
                'macro_files_count': len(macro_files),
                'backup_files_count': backup_stats.total_backups,
                'total_backup_size_mb': backup_stats.total_size_mb,
                'unique_backups': backup_stats.unique_originals,
            }

        except Exception as e:
            self.logger.error(f'Error getting file statistics: {e}')
            return {
                'macro_files_count': 0,
                'backup_files_count': 0,
                'total_backup_size_mb': 0,
                'unique_backups': 0,
            }


class BackupManagementDialog:
    """Dialog for managing backup files."""

    def __init__(
        self,
        parent: tk.Widget,
        file_path: Path,
        backups: list,
        backup_manager: BackupManager,
    ):
        """
        Initialize backup management dialog.

        Args:
            parent: Parent widget
            file_path: Original file path
            backups: List of backup information
            backup_manager: Backup manager instance
        """
        self.parent = parent
        self.file_path = file_path
        self.backups = backups
        self.backup_manager = backup_manager
        self.dialog = None

    def show(self):
        """Show the backup management dialog."""
        # Create dialog window
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f'バックアップ管理 - {self.file_path.name}')
        self.dialog.geometry('500x400')
        self.dialog.resizable(True, True)

        # Make modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        self._setup_ui()

        # Center on parent
        self._center_dialog()

    def _setup_ui(self):
        """Set up the dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding='10')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_label = ttk.Label(
            main_frame,
            text=f'ファイル: {self.file_path.name}\nバックアップ数: {len(self.backups)}',
            justify=tk.LEFT,
        )
        header_label.pack(anchor=tk.W, pady=(0, 10))

        # Backup list frame
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Create treeview for backup list
        columns = ('created', 'size')
        self.backup_tree = ttk.Treeview(
            list_frame, columns=columns, show='tree headings'
        )

        # Configure columns
        self.backup_tree.heading('#0', text='バックアップファイル')
        self.backup_tree.heading('created', text='作成日時')
        self.backup_tree.heading('size', text='サイズ')

        self.backup_tree.column('#0', width=200)
        self.backup_tree.column('created', width=150)
        self.backup_tree.column('size', width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.backup_tree.yview
        )
        self.backup_tree.configure(yscrollcommand=scrollbar.set)

        # Pack treeview and scrollbar
        self.backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Populate backup list
        self._populate_backup_list()

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # Buttons
        ttk.Button(
            button_frame, text='復元', command=self._restore_selected_backup
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            button_frame, text='削除', command=self._delete_selected_backup
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            button_frame, text='すべて削除', command=self._delete_all_backups
        ).pack(side=tk.LEFT)

        ttk.Button(button_frame, text='閉じる', command=self._close_dialog).pack(
            side=tk.RIGHT
        )

    def _populate_backup_list(self):
        """Populate the backup list."""
        for backup in self.backups:
            created_str = backup.created_time.strftime('%Y-%m-%d %H:%M:%S')
            size_str = f'{backup.size_mb:.2f} MB'

            self.backup_tree.insert(
                '',
                'end',
                text=backup.path.name,
                values=(created_str, size_str),
                tags=(str(backup.path),),
            )

    def _restore_selected_backup(self):
        """Restore the selected backup."""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning(
                '選択エラー',
                '復元するバックアップを選択してください。',
                parent=self.dialog,
            )
            return

        item = selection[0]
        backup_path_str = self.backup_tree.item(item, 'tags')[0]
        backup_path = Path(backup_path_str)

        # Confirm restoration
        result = messagebox.askyesno(
            '復元確認',
            f'選択したバックアップから復元しますか？\n\n現在のファイルは上書きされます。\nバックアップ: {backup_path.name}',
            parent=self.dialog,
        )

        if result:
            try:
                self.backup_manager.restore_backup(backup_path, self.file_path)
                messagebox.showinfo(
                    '復元完了',
                    'バックアップファイルから正常に復元されました。',
                    parent=self.dialog,
                )
            except BackupError as e:
                messagebox.showerror(
                    '復元エラー',
                    f'バックアップの復元に失敗しました。\n\nエラー: {e}',
                    parent=self.dialog,
                )

    def _delete_selected_backup(self):
        """Delete the selected backup."""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning(
                '選択エラー',
                '削除するバックアップを選択してください。',
                parent=self.dialog,
            )
            return

        item = selection[0]
        backup_path_str = self.backup_tree.item(item, 'tags')[0]
        backup_path = Path(backup_path_str)

        # Confirm deletion
        result = messagebox.askyesno(
            '削除確認',
            f'選択したバックアップファイルを削除しますか？\n\n{backup_path.name}',
            parent=self.dialog,
        )

        if result:
            try:
                self.backup_manager.delete_backup(backup_path)
                # Remove from tree
                self.backup_tree.delete(item)
                messagebox.showinfo(
                    '削除完了',
                    'バックアップファイルが削除されました。',
                    parent=self.dialog,
                )
            except BackupError as e:
                messagebox.showerror(
                    '削除エラー',
                    f'バックアップファイルの削除に失敗しました。\n\nエラー: {e}',
                    parent=self.dialog,
                )

    def _delete_all_backups(self):
        """Delete all backups."""
        if not self.backups:
            return

        # Confirm deletion
        result = messagebox.askyesno(
            '全削除確認',
            f'すべてのバックアップファイル（{len(self.backups)}個）を削除しますか？\n\nこの操作は元に戻せません。',
            parent=self.dialog,
        )

        if result:
            try:
                deleted_count = self.backup_manager.cleanup_all_backups(self.file_path)
                # Clear tree
                self.backup_tree.delete(*self.backup_tree.get_children())
                messagebox.showinfo(
                    '削除完了',
                    f'{deleted_count}個のバックアップファイルが削除されました。',
                    parent=self.dialog,
                )
            except BackupError as e:
                messagebox.showerror(
                    '削除エラー',
                    f'バックアップファイルの削除に失敗しました。\n\nエラー: {e}',
                    parent=self.dialog,
                )

    def _close_dialog(self):
        """Close the dialog."""
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
