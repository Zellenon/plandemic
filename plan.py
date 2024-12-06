from dataclasses import dataclass, field
from enum import Enum
from typing import Union, Set

class PlanType(Enum):
    STAY = "stay"
    GOTO_ROOM = "goto_room"
    FIND_TOKEN = "find_token"

@dataclass
class Plan:
    type: PlanType
    target: Union[str, int, None]  # Room ID or Token ID
    turns_remaining: int = 0
    visited_rooms: Set[str] = field(default_factory=set)