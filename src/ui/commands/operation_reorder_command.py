"""
Command for reordering operation blocks.

This module implements the Command pattern for undo/redo functionality
when reordering operation blocks in macros.
"""

from typing import List, Optional, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
import time

from ...core.macro_data import MacroRecording, OperationBlock


class Command(ABC):
    """Abstract base class for all commands that support undo/redo."""

    @abstractmethod
    def execute(self) -> bool:
        """
        Execute the command.

        Returns:
            True if command executed successfully, False otherwise
        """
        pass

    @abstractmethod
    def undo(self) -> bool:
        """
        Undo the command.

        Returns:
            True if command was undone successfully, False otherwise
        """
        pass

    @abstractmethod
    def can_merge_with(self, other: 'Command') -> bool:
        """
        Check if this command can be merged with another command.

        Args:
            other: Another command to potentially merge with

        Returns:
            True if commands can be merged, False otherwise
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """
        Get human-readable description of the command.

        Returns:
            Description string for UI display
        """
        pass


@dataclass
class ReorderOperation:
    """Data structure representing a reorder operation."""

    source_index: int
    target_index: int
    timestamp: float

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp == 0:
            self.timestamp = time.time()


class OperationReorderCommand(Command):
    """
    Command for reordering operation blocks within a macro recording.

    This command supports undo/redo functionality and can merge consecutive
    reorder operations on the same element.
    """

    def __init__(
        self,
        macro_recording: MacroRecording,
        source_index: int,
        target_index: int,
        on_update: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize reorder command.

        Args:
            macro_recording: Macro recording to modify
            source_index: Original index of the operation block
            target_index: Target index for the operation block
            on_update: Callback to notify UI of changes
        """
        self.macro_recording = macro_recording
        self.source_index = source_index
        self.target_index = target_index
        self.on_update = on_update
        self.executed = False

        # Store the operation that will be moved for validation
        self.moved_operation: Optional[OperationBlock] = None

        # Validate indices
        self._validate_indices()

        # Track operation history for merging
        self.operations: List[ReorderOperation] = [
            ReorderOperation(source_index, target_index, 0)
        ]

    def _validate_indices(self) -> None:
        """Validate that source and target indices are valid."""
        operation_count = len(self.macro_recording.operations)

        if not 0 <= self.source_index < operation_count:
            raise ValueError(
                f'Source index {self.source_index} out of range [0, {operation_count})'
            )

        if not 0 <= self.target_index < operation_count:
            raise ValueError(
                f'Target index {self.target_index} out of range [0, {operation_count})'
            )

        if self.source_index == self.target_index:
            raise ValueError('Source and target indices cannot be the same')

    def execute(self) -> bool:
        """
        Execute the reorder operation.

        Returns:
            True if operation executed successfully, False otherwise
        """
        try:
            # Store reference to operation being moved
            self.moved_operation = self.macro_recording.operations[self.source_index]

            # Perform the reorder
            operations = self.macro_recording.operations
            moved_op = operations.pop(self.source_index)

            # Adjust target index if necessary (when source < target)
            actual_target = self.target_index
            if self.source_index < self.target_index:
                actual_target -= 1

            operations.insert(actual_target, moved_op)

            self.executed = True

            # Notify UI of changes
            if self.on_update:
                self.on_update()

            return True

        except (IndexError, ValueError) as e:
            print(f'Error executing reorder command: {e}')
            return False

    def undo(self) -> bool:
        """
        Undo the reorder operation.

        Returns:
            True if operation was undone successfully, False otherwise
        """
        if not self.executed or not self.moved_operation:
            return False

        try:
            # Find current position of the moved operation
            current_index = None
            for i, op in enumerate(self.macro_recording.operations):
                if op is self.moved_operation:
                    current_index = i
                    break

            if current_index is None:
                return False

            # Move back to original position
            operations = self.macro_recording.operations
            moved_op = operations.pop(current_index)
            operations.insert(self.source_index, moved_op)

            self.executed = False

            # Notify UI of changes
            if self.on_update:
                self.on_update()

            return True

        except (IndexError, ValueError) as e:
            print(f'Error undoing reorder command: {e}')
            return False

    def can_merge_with(self, other: 'Command') -> bool:
        """
        Check if this command can be merged with another reorder command.

        Two reorder commands can be merged if:
        1. They operate on the same macro recording
        2. They move the same operation block
        3. The commands were executed within a short time window

        Args:
            other: Another command to potentially merge with

        Returns:
            True if commands can be merged, False otherwise
        """
        if not isinstance(other, OperationReorderCommand):
            return False

        if other.macro_recording is not self.macro_recording:
            return False

        if other.moved_operation is not self.moved_operation:
            return False

        # Check time window (within 2 seconds)
        if self.operations and other.operations:
            time_diff = abs(
                self.operations[-1].timestamp - other.operations[0].timestamp
            )
            return time_diff <= 2.0

        return False

    def merge_with(self, other: 'OperationReorderCommand') -> bool:
        """
        Merge another reorder command with this one.

        Args:
            other: Command to merge

        Returns:
            True if merge was successful, False otherwise
        """
        if not self.can_merge_with(other):
            return False

        # Add the other command's operations to our history
        self.operations.extend(other.operations)

        # Update our target to the final target of the merged command
        self.target_index = other.target_index

        return True

    def get_description(self) -> str:
        """
        Get human-readable description of the command.

        Returns:
            Description string for UI display
        """
        if len(self.operations) == 1:
            return f'操作ブロックを位置 {self.source_index + 1} から {self.target_index + 1} に移動'
        else:
            return f'操作ブロックを移動 ({len(self.operations)} 回の操作)'

    def get_final_positions(self) -> tuple[int, int]:
        """
        Get the final source and target positions after all operations.

        Returns:
            Tuple of (final_source_index, final_target_index)
        """
        if not self.operations:
            return self.source_index, self.target_index

        first_op = self.operations[0]
        last_op = self.operations[-1]

        return first_op.source_index, last_op.target_index


class BatchReorderCommand(Command):
    """
    Command for performing multiple reorder operations as a single unit.

    This is useful for complex reordering scenarios that need to be treated
    as a single undo/redo operation.
    """

    def __init__(
        self,
        macro_recording: MacroRecording,
        reorder_commands: List[OperationReorderCommand],
        description: Optional[str] = None,
    ):
        """
        Initialize batch reorder command.

        Args:
            macro_recording: Macro recording to modify
            reorder_commands: List of individual reorder commands
            description: Optional custom description
        """
        self.macro_recording = macro_recording
        self.reorder_commands = reorder_commands
        self.custom_description = description
        self.executed = False

    def execute(self) -> bool:
        """
        Execute all reorder commands in sequence.

        Returns:
            True if all commands executed successfully, False otherwise
        """
        if self.executed:
            return True

        executed_commands = []

        try:
            for command in self.reorder_commands:
                if command.execute():
                    executed_commands.append(command)
                else:
                    # Rollback executed commands if any command fails
                    for rollback_cmd in reversed(executed_commands):
                        rollback_cmd.undo()
                    return False

            self.executed = True
            return True

        except Exception as e:
            # Rollback on any error
            for rollback_cmd in reversed(executed_commands):
                rollback_cmd.undo()
            print(f'Error executing batch reorder command: {e}')
            return False

    def undo(self) -> bool:
        """
        Undo all reorder commands in reverse order.

        Returns:
            True if all commands were undone successfully, False otherwise
        """
        if not self.executed:
            return False

        try:
            # Undo in reverse order
            for command in reversed(self.reorder_commands):
                if not command.undo():
                    return False

            self.executed = False
            return True

        except Exception as e:
            print(f'Error undoing batch reorder command: {e}')
            return False

    def can_merge_with(self, other: 'Command') -> bool:
        """
        Batch commands generally cannot be merged.

        Args:
            other: Another command

        Returns:
            False - batch commands don't support merging
        """
        return False

    def get_description(self) -> str:
        """
        Get human-readable description of the batch command.

        Returns:
            Description string for UI display
        """
        if self.custom_description:
            return self.custom_description

        if len(self.reorder_commands) == 1:
            return self.reorder_commands[0].get_description()
        else:
            return f'複数の操作ブロックを移動 ({len(self.reorder_commands)} 個)'
