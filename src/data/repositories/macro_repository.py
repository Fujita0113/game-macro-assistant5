"""
Abstract base class for macro data repository.

This module defines the repository interface for macro data persistence,
following the Repository pattern for data access abstraction.
"""

from abc import ABC, abstractmethod
from typing import List
from pathlib import Path

from ...core.macro_data import MacroRecording


class MacroRepository(ABC):
    """Abstract base class for macro data repository."""

    @abstractmethod
    def save(self, recording: MacroRecording, file_path: Path, password: str) -> bool:
        """
        Save a macro recording to persistent storage.

        Args:
            recording: MacroRecording instance to save
            file_path: Path where the recording should be saved
            password: Password for encryption

        Returns:
            bool: True if save successful, False otherwise

        Raises:
            RepositoryError: If save operation fails
        """
        pass

    @abstractmethod
    def load(self, file_path: Path, password: str) -> MacroRecording:
        """
        Load a macro recording from persistent storage.

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
        pass

    @abstractmethod
    def exists(self, file_path: Path) -> bool:
        """
        Check if a macro recording file exists.

        Args:
            file_path: Path to check

        Returns:
            bool: True if file exists, False otherwise
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass


class RepositoryError(Exception):
    """Base exception for repository operations."""

    pass


class InvalidPasswordError(RepositoryError):
    """Exception raised when password is incorrect."""

    pass


class CorruptedFileError(RepositoryError):
    """Exception raised when file is corrupted or invalid."""

    pass
