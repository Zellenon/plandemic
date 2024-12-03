import pygame
import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Union
from enum import Enum
from collections import deque


class PlanType(Enum):
    STAY = "stay"
    GOTO_ROOM = "goto_room"
    FIND_TOKEN = "find_token"


@dataclass
class Plan:
    type: PlanType
    # Room ID for GOTO_ROOM, Token ID for FIND_TOKEN
    target: Union[str, int, None]
    turns_remaining: int = 0
    visited_rooms: Set[str] = field(default_factory=set)

    def __post_init__(self):
        if self.visited_rooms is None:
            self.visited_rooms = set()


@dataclass
class Token:
    id: int
    x: int
    y: int
    color: Tuple[int, int, int]
    current_room: str
    plan: Optional[Plan] = None
