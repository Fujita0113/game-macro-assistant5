from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Union


class EventType(Enum):
    MOUSE_CLICK = "mouse_click"
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"


class MouseButton(Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


@dataclass
class MouseEvent:
    type: EventType
    x: int
    y: int
    button: MouseButton
    timestamp: datetime
    
    def to_dict(self):
        return {
            "type": self.type.value,
            "x": self.x,
            "y": self.y,
            "button": self.button.value,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class KeyboardEvent:
    type: EventType
    key: str
    timestamp: datetime
    char: Optional[str] = None
    
    def to_dict(self):
        return {
            "type": self.type.value,
            "key": self.key,
            "timestamp": self.timestamp.isoformat(),
            "char": self.char
        }


InputEvent = Union[MouseEvent, KeyboardEvent]