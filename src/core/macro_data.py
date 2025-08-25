"""
Data structures for macro operations and recording data.

This module defines the core data structures used to represent recorded
operations and macro blocks for the GameMacroAssistant.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
import time


class OperationType(Enum):
    """Types of operations that can be recorded."""

    MOUSE_CLICK = 'mouse_click'
    MOUSE_MOVE = 'mouse_move'
    KEY_PRESS = 'key_press'
    KEY_RELEASE = 'key_release'
    WAIT = 'wait'
    SCREEN_CONDITION = 'screen_condition'


class MouseButton(Enum):
    """Mouse button types."""

    LEFT = 'left'
    RIGHT = 'right'
    MIDDLE = 'middle'


@dataclass
class Position:
    """Represents a 2D position."""

    x: int
    y: int

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary representation."""
        return {'x': self.x, 'y': self.y}

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'Position':
        """Create Position from dictionary."""
        return cls(x=data['x'], y=data['y'])


@dataclass
class MouseOperation:
    """Represents a mouse operation."""

    button: MouseButton
    position: Position
    action: str  # "press", "release", "click", "move"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'button': self.button.value,
            'position': self.position.to_dict(),
            'action': self.action,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MouseOperation':
        """Create MouseOperation from dictionary."""
        return cls(
            button=MouseButton(data['button']),
            position=Position.from_dict(data['position']),
            action=data['action'],
        )


@dataclass
class KeyboardOperation:
    """Represents a keyboard operation."""

    key: str
    action: str  # "press", "release"
    modifiers: List[str]  # ["ctrl", "shift", "alt"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {'key': self.key, 'action': self.action, 'modifiers': self.modifiers}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeyboardOperation':
        """Create KeyboardOperation from dictionary."""
        return cls(
            key=data['key'], action=data['action'], modifiers=data.get('modifiers', [])
        )


@dataclass
class ScreenCondition:
    """Represents a screen matching condition."""

    image_data: bytes  # Screenshot image data
    region: Optional[Tuple[int, int, int, int]]  # (x, y, width, height)
    threshold: float = 0.8  # Matching threshold
    timeout: float = 5.0  # Timeout in seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'image_data': self.image_data.hex() if self.image_data else None,
            'region': self.region,
            'threshold': self.threshold,
            'timeout': self.timeout,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScreenCondition':
        """Create ScreenCondition from dictionary."""
        image_data = (
            bytes.fromhex(data['image_data']) if data.get('image_data') else b''
        )
        return cls(
            image_data=image_data,
            region=data.get('region'),
            threshold=data.get('threshold', 0.8),
            timeout=data.get('timeout', 5.0),
        )


@dataclass
class OperationBlock:
    """Represents a single operation block in a macro."""

    id: str
    operation_type: OperationType
    timestamp: float
    mouse_op: Optional[MouseOperation] = None
    keyboard_op: Optional[KeyboardOperation] = None
    screen_condition: Optional[ScreenCondition] = None
    delay_after: float = 0.0  # Delay after this operation in seconds

    def __post_init__(self):
        """Validate operation data consistency."""
        if self.operation_type in [OperationType.MOUSE_CLICK, OperationType.MOUSE_MOVE]:
            if self.mouse_op is None:
                raise ValueError(f'MouseOperation required for {self.operation_type}')
        elif self.operation_type in [
            OperationType.KEY_PRESS,
            OperationType.KEY_RELEASE,
        ]:
            if self.keyboard_op is None:
                raise ValueError(
                    f'KeyboardOperation required for {self.operation_type}'
                )
        elif self.operation_type == OperationType.SCREEN_CONDITION:
            if self.screen_condition is None:
                raise ValueError('ScreenCondition required for SCREEN_CONDITION')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        data = {
            'id': self.id,
            'operation_type': self.operation_type.value,
            'timestamp': self.timestamp,
            'delay_after': self.delay_after,
        }

        if self.mouse_op:
            data['mouse_op'] = self.mouse_op.to_dict()
        if self.keyboard_op:
            data['keyboard_op'] = self.keyboard_op.to_dict()
        if self.screen_condition:
            data['screen_condition'] = self.screen_condition.to_dict()

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OperationBlock':
        """Create OperationBlock from dictionary."""
        mouse_op = (
            MouseOperation.from_dict(data['mouse_op']) if 'mouse_op' in data else None
        )
        keyboard_op = (
            KeyboardOperation.from_dict(data['keyboard_op'])
            if 'keyboard_op' in data
            else None
        )
        screen_condition = (
            ScreenCondition.from_dict(data['screen_condition'])
            if 'screen_condition' in data
            else None
        )

        return cls(
            id=data['id'],
            operation_type=OperationType(data['operation_type']),
            timestamp=data['timestamp'],
            mouse_op=mouse_op,
            keyboard_op=keyboard_op,
            screen_condition=screen_condition,
            delay_after=data.get('delay_after', 0.0),
        )


@dataclass
class MacroRecording:
    """Represents a complete macro recording session."""

    name: str
    created_at: float
    operations: List[OperationBlock]
    metadata: Dict[str, Any]

    def __post_init__(self):
        """Initialize with current timestamp if not provided."""
        if self.created_at == 0:
            self.created_at = time.time()

        if not self.metadata:
            self.metadata = {}

    @property
    def operation_count(self) -> int:
        """Get the number of operations in this recording."""
        return len(self.operations)

    @property
    def duration(self) -> float:
        """Get the total duration of the recording in seconds."""
        if not self.operations:
            return 0.0

        first_timestamp = self.operations[0].timestamp
        last_timestamp = self.operations[-1].timestamp
        return last_timestamp - first_timestamp

    def add_operation(self, operation: OperationBlock):
        """Add an operation to the recording."""
        self.operations.append(operation)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'created_at': self.created_at,
            'operations': [op.to_dict() for op in self.operations],
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MacroRecording':
        """Create MacroRecording from dictionary."""
        operations = [
            OperationBlock.from_dict(op_data) for op_data in data.get('operations', [])
        ]

        return cls(
            name=data['name'],
            created_at=data['created_at'],
            operations=operations,
            metadata=data.get('metadata', {}),
        )


def create_mouse_click_operation(
    button: MouseButton, position: Position, timestamp: Optional[float] = None
) -> OperationBlock:
    """
    Create a mouse click operation block.

    Args:
        button: Mouse button that was clicked
        position: Click position
        timestamp: Operation timestamp (current time if None)

    Returns:
        OperationBlock for mouse click
    """
    if timestamp is None:
        timestamp = time.time()

    mouse_op = MouseOperation(button=button, position=position, action='click')

    return OperationBlock(
        id=f'mouse_click_{int(timestamp * 1000)}',
        operation_type=OperationType.MOUSE_CLICK,
        timestamp=timestamp,
        mouse_op=mouse_op,
    )


def create_key_operation(
    key: str,
    action: str,
    modifiers: Optional[List[str]] = None,
    timestamp: Optional[float] = None,
) -> OperationBlock:
    """
    Create a keyboard operation block.

    Args:
        key: Key that was pressed/released
        action: "press" or "release"
        modifiers: List of modifier keys
        timestamp: Operation timestamp (current time if None)

    Returns:
        OperationBlock for keyboard operation
    """
    if timestamp is None:
        timestamp = time.time()
    if modifiers is None:
        modifiers = []

    keyboard_op = KeyboardOperation(key=key, action=action, modifiers=modifiers)

    operation_type = (
        OperationType.KEY_PRESS if action == 'press' else OperationType.KEY_RELEASE
    )

    return OperationBlock(
        id=f'key_{action}_{int(timestamp * 1000)}',
        operation_type=operation_type,
        timestamp=timestamp,
        keyboard_op=keyboard_op,
    )
