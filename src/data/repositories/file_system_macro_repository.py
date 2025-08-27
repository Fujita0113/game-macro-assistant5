"""
File system-based implementation of macro repository.

This module provides concrete implementation of MacroRepository using
the local file system with AES encryption.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from ...core.macro_data import MacroRecording
from ..encryption.encryption_service import (
    EncryptionService,
    EncryptionError,
    InvalidPasswordError,
)
from .macro_repository import (
    MacroRepository,
    RepositoryError,
    InvalidPasswordError as RepoInvalidPasswordError,
    CorruptedFileError,
)


class FileSystemMacroRepository(MacroRepository):
    """File system-based macro repository with encryption."""

    def __init__(self, encryption_service: Optional[EncryptionService] = None):
        """
        Initialize the file system repository.

        Args:
            encryption_service: Encryption service instance (creates new if None)
        """
        self.encryption_service = encryption_service or EncryptionService()
        self.logger = logging.getLogger(__name__)

    def save(self, recording: MacroRecording, file_path: Path, password: str) -> bool:
        """
        Save a macro recording to an encrypted file.

        Args:
            recording: MacroRecording instance to save
            file_path: Path where the recording should be saved
            password: Password for encryption

        Returns:
            bool: True if save successful, False otherwise

        Raises:
            RepositoryError: If save operation fails
        """
        try:
            # Validate password
            self.encryption_service.validate_password(password)

            # Convert recording to dictionary
            recording_data = recording.to_dict()

            # Add metadata
            recording_data['_metadata'] = {
                'format_version': '1.0',
                'encryption': 'AES-256-GCM',
            }

            # Encrypt the data
            encrypted_data = self.encryption_service.encrypt_data(
                recording_data, password
            )

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write encrypted data to file
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)

            self.logger.info(f'Successfully saved macro recording to {file_path}')
            return True

        except EncryptionError as e:
            raise RepositoryError(f'Encryption failed: {e}') from e
        except OSError as e:
            raise RepositoryError(f'File system error: {e}') from e
        except Exception as e:
            raise RepositoryError(f'Unexpected error during save: {e}') from e

    def load(self, file_path: Path, password: str) -> MacroRecording:
        """
        Load a macro recording from an encrypted file.

        Args:
            file_path: Path to the recording file
            password: Password for decryption

        Returns:
            MacroRecording: Loaded recording instance

        Raises:
            RepositoryError: If load operation fails
            InvalidPasswordError: If password is incorrect
            FileNotFoundError: If file doesn't exist
        """
        try:
            # Check if file exists
            if not file_path.exists():
                raise FileNotFoundError(f'Macro file not found: {file_path}')

            # Read encrypted data from file
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()

            # Decrypt the data
            try:
                recording_data = self.encryption_service.decrypt_data(
                    encrypted_data, password
                )
            except InvalidPasswordError as e:
                raise RepoInvalidPasswordError('Incorrect password') from e

            # Validate format
            if '_metadata' not in recording_data:
                self.logger.warning(f'Loading legacy format file: {file_path}')
            else:
                metadata = recording_data['_metadata']
                if metadata.get('format_version') != '1.0':
                    self.logger.warning(
                        f'Unknown format version: {metadata.get("format_version")}'
                    )

            # Remove metadata before creating recording
            if '_metadata' in recording_data:
                del recording_data['_metadata']

            # Create MacroRecording from data
            recording = MacroRecording.from_dict(recording_data)

            self.logger.info(f'Successfully loaded macro recording from {file_path}')
            return recording

        except FileNotFoundError:
            raise  # Re-raise FileNotFoundError as-is
        except RepoInvalidPasswordError:
            raise  # Re-raise InvalidPasswordError as-is
        except EncryptionError as e:
            raise CorruptedFileError(
                f'Failed to decrypt file (may be corrupted): {e}'
            ) from e
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise CorruptedFileError(f'Invalid macro file format: {e}') from e
        except OSError as e:
            raise RepositoryError(f'File system error: {e}') from e
        except Exception as e:
            raise RepositoryError(f'Unexpected error during load: {e}') from e

    def exists(self, file_path: Path) -> bool:
        """
        Check if a macro recording file exists.

        Args:
            file_path: Path to check

        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            return file_path.exists() and file_path.is_file()
        except OSError:
            return False

    def delete(self, file_path: Path) -> bool:
        """
        Delete a macro recording file.

        Args:
            file_path: Path to the file to delete

        Returns:
            bool: True if deletion successful, False otherwise

        Raises:
            RepositoryError: If delete operation fails
        """
        try:
            if not file_path.exists():
                return True  # Already deleted

            file_path.unlink()
            self.logger.info(f'Successfully deleted macro file: {file_path}')
            return True

        except OSError as e:
            raise RepositoryError(f'Failed to delete file: {e}') from e
        except Exception as e:
            raise RepositoryError(f'Unexpected error during deletion: {e}') from e

    def list_recordings(self, directory: Path) -> List[Path]:
        """
        List all macro recording files in a directory.

        Args:
            directory: Directory to search for recordings

        Returns:
            List[Path]: List of recording file paths

        Raises:
            RepositoryError: If listing operation fails
        """
        try:
            if not directory.exists() or not directory.is_dir():
                return []

            # Find all .gma.json files
            recording_files = list(directory.glob('*.gma.json'))

            # Sort by modification time (newest first)
            recording_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            self.logger.info(f'Found {len(recording_files)} macro files in {directory}')
            return recording_files

        except OSError as e:
            raise RepositoryError(f'Failed to list directory: {e}') from e
        except Exception as e:
            raise RepositoryError(f'Unexpected error during listing: {e}') from e

    def get_file_info(self, file_path: Path) -> dict:
        """
        Get information about a macro file without decrypting it.

        Args:
            file_path: Path to the macro file

        Returns:
            dict: File information (size, modified time, etc.)

        Raises:
            RepositoryError: If unable to get file info
        """
        try:
            if not file_path.exists():
                raise FileNotFoundError(f'File not found: {file_path}')

            stat = file_path.stat()
            return {
                'name': file_path.name,
                'size': stat.st_size,
                'modified_time': stat.st_mtime,
                'created_time': stat.st_ctime,
                'is_encrypted': True,  # All files are encrypted
            }

        except OSError as e:
            raise RepositoryError(f'Failed to get file info: {e}') from e
