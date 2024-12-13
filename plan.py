from dataclasses import dataclass, field
from enum import Enum
from typing import Union, Set

class PlanType(Enum):
    STAY = "stay"
    GOTO_ROOM = "goto_room"
    FIND_AGENT = "find_agent"
    GO_TO_CAULDRON = "go_to_cauldron"

@dataclass
class Plan:
    type: PlanType
    target: Union[str, int, None]  # Room ID or Agent ID
    turns_remaining: int = 0
    visited_rooms: Set[str] = field(default_factory=set)