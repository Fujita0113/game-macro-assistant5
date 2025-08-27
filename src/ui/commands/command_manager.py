"""
Command manager for undo/redo functionality.

This module provides a centralized manager for executing commands and
maintaining undo/redo stacks with proper memory management.
"""

from typing import List, Optional, Dict, Any, Callable
from collections import deque
import time

from .operation_reorder_command import Command


class CommandManagerConfig:
    """Configuration for command manager behavior."""

    def __init__(
        self,
        max_history_size: int = 100,
        command_merge_timeout: float = 2.0,
        enable_compression: bool = True,
        auto_cleanup_threshold: int = 150,
    ):
        """
        Initialize command manager configuration.

        Args:
            max_history_size: Maximum number of commands to keep in history
            command_merge_timeout: Time window for merging similar commands (seconds)
            enable_compression: Whether to compress/merge similar commands
            auto_cleanup_threshold: Trigger cleanup when history exceeds this size
        """
        self.max_history_size = max_history_size
        self.command_merge_timeout = command_merge_timeout
        self.enable_compression = enable_compression
        self.auto_cleanup_threshold = auto_cleanup_threshold


class CommandManager:
    """
    Manages command execution and undo/redo functionality.

    This class maintains separate stacks for undo and redo operations,
    supports command merging for better user experience, and provides
    memory management for long-running sessions.
    """

    def __init__(
        self,
        config: Optional[CommandManagerConfig] = None,
        on_state_change: Optional[Callable[[bool, bool], None]] = None,
    ):
        """
        Initialize command manager.

        Args:
            config: Configuration for manager behavior
            on_state_change: Callback for undo/redo availability changes
        """
        self.config = config or CommandManagerConfig()
        self.on_state_change = on_state_change

        # Command stacks
        self.undo_stack: deque[Command] = deque(maxlen=self.config.max_history_size)
        self.redo_stack: deque[Command] = deque(maxlen=self.config.max_history_size)

        # State tracking
        self.is_executing = False
        self.last_command_time = 0.0

        # Statistics
        self.stats = {
            'commands_executed': 0,
            'commands_undone': 0,
            'commands_redone': 0,
            'commands_merged': 0,
        }

    def execute_command(self, command: Command) -> bool:
        """
        Execute a command and add it to the undo stack.

        Args:
            command: Command to execute

        Returns:
            True if command executed successfully, False otherwise
        """
        if self.is_executing:
            return False

        self.is_executing = True

        try:
            # Attempt to merge with last command if enabled
            if (
                self.config.enable_compression
                and self.undo_stack
                and self._should_merge_command(command)
            ):
                last_command = self.undo_stack[-1]
                if last_command.can_merge_with(command):
                    if hasattr(last_command, 'merge_with') and last_command.merge_with(
                        command
                    ):
                        # Update statistics
                        self.stats['commands_merged'] += 1
                        self.last_command_time = time.time()
                        return True

            # Execute the command
            if command.execute():
                # Clear redo stack when new command is executed
                self.redo_stack.clear()

                # Add to undo stack
                self.undo_stack.append(command)

                # Trigger cleanup if needed
                if len(self.undo_stack) > self.config.auto_cleanup_threshold:
                    self._cleanup_history()

                # Update statistics and timing
                self.stats['commands_executed'] += 1
                self.last_command_time = time.time()

                # Notify state change
                self._notify_state_change()

                return True
            else:
                return False

        finally:
            self.is_executing = False

    def undo(self) -> bool:
        """
        Undo the last executed command.

        Returns:
            True if undo was successful, False otherwise
        """
        if not self.can_undo() or self.is_executing:
            return False

        self.is_executing = True

        try:
            command = self.undo_stack.pop()

            if command.undo():
                # Move to redo stack
                self.redo_stack.append(command)

                # Update statistics
                self.stats['commands_undone'] += 1

                # Notify state change
                self._notify_state_change()

                return True
            else:
                # Put command back if undo failed
                self.undo_stack.append(command)
                return False

        finally:
            self.is_executing = False

    def redo(self) -> bool:
        """
        Redo the last undone command.

        Returns:
            True if redo was successful, False otherwise
        """
        if not self.can_redo() or self.is_executing:
            return False

        self.is_executing = True

        try:
            command = self.redo_stack.pop()

            if command.execute():
                # Move back to undo stack
                self.undo_stack.append(command)

                # Update statistics
                self.stats['commands_redone'] += 1

                # Notify state change
                self._notify_state_change()

                return True
            else:
                # Put command back if redo failed
                self.redo_stack.append(command)
                return False

        finally:
            self.is_executing = False

    def can_undo(self) -> bool:
        """
        Check if undo operation is available.

        Returns:
            True if undo is available, False otherwise
        """
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """
        Check if redo operation is available.

        Returns:
            True if redo is available, False otherwise
        """
        return len(self.redo_stack) > 0

    def get_undo_description(self) -> Optional[str]:
        """
        Get description of the command that would be undone.

        Returns:
            Description string or None if no undo available
        """
        if self.can_undo():
            return self.undo_stack[-1].get_description()
        return None

    def get_redo_description(self) -> Optional[str]:
        """
        Get description of the command that would be redone.

        Returns:
            Description string or None if no redo available
        """
        if self.can_redo():
            return self.redo_stack[-1].get_description()
        return None

    def clear_history(self) -> None:
        """Clear all command history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._notify_state_change()

    def get_history_info(self) -> Dict[str, Any]:
        """
        Get information about command history.

        Returns:
            Dictionary with history information
        """
        return {
            'undo_count': len(self.undo_stack),
            'redo_count': len(self.redo_stack),
            'max_history_size': self.config.max_history_size,
            'can_undo': self.can_undo(),
            'can_redo': self.can_redo(),
            'is_executing': self.is_executing,
            'statistics': self.stats.copy(),
        }

    def get_command_history(self, include_redo: bool = False) -> List[str]:
        """
        Get list of command descriptions in history.

        Args:
            include_redo: Whether to include redo stack in results

        Returns:
            List of command descriptions
        """
        history = []

        # Add undo stack (most recent first)
        for command in reversed(self.undo_stack):
            history.append(f'[Undo] {command.get_description()}')

        if include_redo and self.redo_stack:
            history.append('--- Redo Stack ---')
            for command in reversed(self.redo_stack):
                history.append(f'[Redo] {command.get_description()}')

        return history

    def _should_merge_command(self, command: Command) -> bool:
        """
        Check if command should be merged with the last command.

        Args:
            command: Command to check for merging

        Returns:
            True if command should be merged, False otherwise
        """
        if not self.undo_stack:
            return False

        # Check time window
        current_time = time.time()
        time_since_last = current_time - self.last_command_time

        return time_since_last <= self.config.command_merge_timeout

    def _cleanup_history(self) -> None:
        """Clean up old commands from history to manage memory."""
        # Remove oldest commands if we exceed the threshold
        while len(self.undo_stack) > self.config.max_history_size:
            self.undo_stack.popleft()

        while len(self.redo_stack) > self.config.max_history_size:
            self.redo_stack.popleft()

    def _notify_state_change(self) -> None:
        """Notify listeners of undo/redo state changes."""
        if self.on_state_change:
            self.on_state_change(self.can_undo(), self.can_redo())

    def set_state_change_callback(
        self, callback: Optional[Callable[[bool, bool], None]]
    ) -> None:
        """
        Set callback for undo/redo state changes.

        Args:
            callback: Callback function that receives (can_undo, can_redo)
        """
        self.on_state_change = callback

    def create_checkpoint(self) -> Dict[str, Any]:
        """
        Create a checkpoint of current state for debugging/restoration.

        Returns:
            Dictionary containing state information
        """
        return {
            'undo_count': len(self.undo_stack),
            'redo_count': len(self.redo_stack),
            'timestamp': time.time(),
            'statistics': self.stats.copy(),
            'last_command_time': self.last_command_time,
        }

    def get_memory_usage_estimate(self) -> Dict[str, int]:
        """
        Get rough estimate of memory usage.

        Returns:
            Dictionary with memory usage estimates
        """
        # This is a rough estimate - actual usage depends on command implementations
        undo_size = len(self.undo_stack)
        redo_size = len(self.redo_stack)

        return {
            'undo_stack_size': undo_size,
            'redo_stack_size': redo_size,
            'total_commands': undo_size + redo_size,
            'estimated_memory_kb': (undo_size + redo_size) * 2,  # Very rough estimate
        }
