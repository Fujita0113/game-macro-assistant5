"""
Backup management service for macro files.

This module provides automatic backup functionality with generational
backup management (keep last 5 versions) for macro files.
"""

import shutil
import time
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime


class BackupInfo:
    """Information about a backup file."""

    def __init__(self, path: Path, timestamp: float, size: int, created_time: datetime):
        """
        Initialize backup info.

        Args:
            path: Path to the backup file
            timestamp: Creation timestamp
            size: File size in bytes
            created_time: Creation datetime
        """
        self.path = path
        self.timestamp = timestamp
        self.size = size
        self.created_time = created_time

    @property
    def size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.size / (1024 * 1024)

    def __repr__(self) -> str:
        return f'BackupInfo(path={self.path}, created={self.created_time}, size={self.size_mb:.2f}MB)'


class BackupStatistics:
    """Statistics about backups in a directory."""

    def __init__(self, total_backups: int, unique_originals: int, total_size: int):
        """
        Initialize backup statistics.

        Args:
            total_backups: Total number of backup files
            unique_originals: Number of unique original files backed up
            total_size: Total size of all backup files in bytes
        """
        self.total_backups = total_backups
        self.unique_originals = unique_originals
        self.total_size = total_size

    @property
    def total_size_mb(self) -> float:
        """Get total size in megabytes."""
        return self.total_size / (1024 * 1024)

    def __repr__(self) -> str:
        return f'BackupStatistics(backups={self.total_backups}, originals={self.unique_originals}, size={self.total_size_mb:.2f}MB)'


class BackupManager:
    """Manager for creating and maintaining macro file backups."""

    def __init__(self, max_backups: int = 5):
        """
        Initialize backup manager.

        Args:
            max_backups: Maximum number of backup files to keep per macro
        """
        self.max_backups = max_backups
        self.logger = logging.getLogger(__name__)

    def create_backup(self, file_path: Path) -> Optional[Path]:
        """
        Create a backup of the specified file.

        Args:
            file_path: Path to the file to backup

        Returns:
            Optional[Path]: Path to the created backup file, None if failed

        Raises:
            BackupError: If backup creation fails
        """
        try:
            if not file_path.exists():
                raise BackupError(f'Source file does not exist: {file_path}')

            # Generate backup filename with timestamp
            backup_path = self._generate_backup_path(file_path)

            # Ensure backup directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file to backup location
            shutil.copy2(file_path, backup_path)

            self.logger.info(f'Created backup: {backup_path}')

            # Clean up old backups
            self._cleanup_old_backups(file_path)

            return backup_path

        except Exception as e:
            raise BackupError(f'Failed to create backup: {e}') from e

    def restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        """
        Restore a file from backup.

        Args:
            backup_path: Path to the backup file
            target_path: Path where to restore the file

        Returns:
            bool: True if restoration successful

        Raises:
            BackupError: If restoration fails
        """
        try:
            if not backup_path.exists():
                raise BackupError(f'Backup file does not exist: {backup_path}')

            # Create target directory if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy backup to target location
            shutil.copy2(backup_path, target_path)

            self.logger.info(f'Restored backup from {backup_path} to {target_path}')
            return True

        except Exception as e:
            raise BackupError(f'Failed to restore backup: {e}') from e

    def list_backups(self, file_path: Path) -> List[BackupInfo]:
        """
        List all backups for a specific file.

        Args:
            file_path: Path to the original file

        Returns:
            List[BackupInfo]: List of backup information, sorted by creation time (newest first)
        """
        try:
            backup_dir = self._get_backup_directory(file_path)
            if not backup_dir.exists():
                return []

            # Find backup files for this file
            # Extract base name without .gma.json extension
            file_name = file_path.name
            if file_name.endswith('.gma.json'):
                base_name = file_name[:-9]  # Remove .gma.json
            else:
                base_name = file_path.stem
            backup_pattern = f'{base_name}_backup_*.gma.json'
            backup_files = list(backup_dir.glob(backup_pattern))

            # Create backup info objects
            backup_infos = []
            for backup_file in backup_files:
                try:
                    timestamp = self._extract_timestamp_from_backup(backup_file)
                    stat = backup_file.stat()

                    backup_info = BackupInfo(
                        path=backup_file,
                        timestamp=timestamp,
                        size=stat.st_size,
                        created_time=datetime.fromtimestamp(timestamp),
                    )
                    backup_infos.append(backup_info)
                except ValueError as e:
                    # Skip files with invalid timestamp format
                    self.logger.debug(f'Skipping backup file {backup_file}: {e}')
                    continue

            # Sort by timestamp (newest first)
            backup_infos.sort(key=lambda x: x.timestamp, reverse=True)

            return backup_infos

        except Exception as e:
            self.logger.error(f'Failed to list backups: {e}')
            return []

    def delete_backup(self, backup_path: Path) -> bool:
        """
        Delete a specific backup file.

        Args:
            backup_path: Path to the backup file to delete

        Returns:
            bool: True if deletion successful

        Raises:
            BackupError: If deletion fails
        """
        try:
            if backup_path.exists():
                backup_path.unlink()
                self.logger.info(f'Deleted backup: {backup_path}')
            return True

        except Exception as e:
            raise BackupError(f'Failed to delete backup: {e}') from e

    def cleanup_all_backups(self, file_path: Path) -> int:
        """
        Delete all backups for a specific file.

        Args:
            file_path: Path to the original file

        Returns:
            int: Number of backups deleted

        Raises:
            BackupError: If cleanup fails
        """
        try:
            backups = self.list_backups(file_path)
            deleted_count = 0

            for backup in backups:
                try:
                    self.delete_backup(backup.path)
                    deleted_count += 1
                except BackupError:
                    continue

            self.logger.info(f'Cleaned up {deleted_count} backups for {file_path.name}')
            return deleted_count

        except Exception as e:
            raise BackupError(f'Failed to cleanup backups: {e}') from e

    def _generate_backup_path(self, file_path: Path) -> Path:
        """Generate backup file path with timestamp."""
        backup_dir = self._get_backup_directory(file_path)
        timestamp = int(time.time())

        # Extract base name without .gma.json extension
        file_name = file_path.name
        if file_name.endswith('.gma.json'):
            base_name = file_name[:-9]  # Remove .gma.json
        else:
            base_name = file_path.stem
        backup_name = f'{base_name}_backup_{timestamp}.gma.json'

        return backup_dir / backup_name

    def _get_backup_directory(self, file_path: Path) -> Path:
        """Get backup directory for a file."""
        # Create backups directory next to the original file
        return file_path.parent / '.backups'

    def _cleanup_old_backups(self, file_path: Path):
        """Remove old backups, keeping only the latest max_backups."""
        try:
            backups = self.list_backups(file_path)

            if len(backups) > self.max_backups:
                # Keep only the newest max_backups
                backups_to_delete = backups[self.max_backups :]

                for backup in backups_to_delete:
                    try:
                        self.delete_backup(backup.path)
                    except BackupError:
                        continue

                self.logger.info(
                    f'Cleaned up {len(backups_to_delete)} old backups for {file_path.name}'
                )

        except Exception as e:
            self.logger.error(f'Failed to cleanup old backups: {e}')

    def _extract_timestamp_from_backup(self, backup_path: Path) -> float:
        """Extract timestamp from backup filename."""
        try:
            # Format: filename_backup_timestamp.gma.json
            name_parts = backup_path.stem.split('_')
            if len(name_parts) >= 3 and name_parts[-2] == 'backup':
                return float(name_parts[-1])
            else:
                raise ValueError('Invalid backup filename format')
        except (IndexError, ValueError) as e:
            raise ValueError(f'Cannot extract timestamp from {backup_path.name}') from e

    def get_backup_statistics(self, directory: Path) -> BackupStatistics:
        """
        Get backup statistics for a directory.

        Args:
            directory: Directory to analyze

        Returns:
            BackupStatistics: Backup statistics
        """
        try:
            backup_dir = directory / '.backups'
            if not backup_dir.exists():
                return BackupStatistics(0, 0, 0)

            backup_files = list(backup_dir.glob('*_backup_*.gma.json'))
            total_backups = len(backup_files)

            total_size = sum(f.stat().st_size for f in backup_files if f.exists())

            # Count unique original files
            original_files = set()
            for backup_file in backup_files:
                try:
                    # Extract original filename
                    name_parts = backup_file.stem.split('_backup_')
                    if len(name_parts) >= 2:
                        original_files.add(name_parts[0])
                except (ValueError, IndexError):
                    continue

            unique_originals = len(original_files)

            return BackupStatistics(total_backups, unique_originals, total_size)

        except Exception as e:
            self.logger.error(f'Failed to get backup statistics: {e}')
            return BackupStatistics(0, 0, 0)


class BackupInfo:
    """Information about a backup file."""

    def __init__(self, path: Path, timestamp: float, size: int, created_time: datetime):
        """
        Initialize backup info.

        Args:
            path: Path to the backup file
            timestamp: Creation timestamp
            size: File size in bytes
            created_time: Creation datetime
        """
        self.path = path
        self.timestamp = timestamp
        self.size = size
        self.created_time = created_time

    @property
    def size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.size / (1024 * 1024)

    def __repr__(self) -> str:
        return f'BackupInfo(path={self.path}, created={self.created_time}, size={self.size_mb:.2f}MB)'


class BackupStatistics:
    """Statistics about backups in a directory."""

    def __init__(self, total_backups: int, unique_originals: int, total_size: int):
        """
        Initialize backup statistics.

        Args:
            total_backups: Total number of backup files
            unique_originals: Number of unique original files backed up
            total_size: Total size of all backup files in bytes
        """
        self.total_backups = total_backups
        self.unique_originals = unique_originals
        self.total_size = total_size

    @property
    def total_size_mb(self) -> float:
        """Get total size in megabytes."""
        return self.total_size / (1024 * 1024)

    def __repr__(self) -> str:
        return f'BackupStatistics(backups={self.total_backups}, originals={self.unique_originals}, size={self.total_size_mb:.2f}MB)'


class BackupError(Exception):
    """Exception raised for backup operation failures."""

    pass
