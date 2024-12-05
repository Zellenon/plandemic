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

    def ensure_plan(self, board):
        """Ensures the token has a plan by generating a new one if current plan is None"""
        if not self.plan:
            self.choose_random_plan(board)

    def choose_random_plan(self, board):
        """Choose a random new plan for a token."""
        plan_type = random.choice(list(PlanType))
        new_plan = None

        if plan_type == PlanType.STAY:
            new_plan = Plan(
                type=PlanType.STAY, target=None, turns_remaining=random.randint(1, 4)
            )

        elif plan_type == PlanType.GOTO_ROOM:
            # Choose a random room that's not the current room
            available_rooms = {room_id for room_id in board.rooms.keys()} - {
                self.current_room
            }
            target_room = random.choice(list(available_rooms))
            new_plan = Plan(
                type=PlanType.GOTO_ROOM,
                target=target_room,
                visited_rooms={self.current_room},
            )

        else:  # FIND_TOKEN
            # Choose a random token that's not this one
            available_tokens = {t.id for t in board.tokens} - {self.id}
            target_token = random.choice(list(available_tokens))
            new_plan = Plan(
                type=PlanType.FIND_TOKEN,
                target=target_token,
                visited_rooms={self.current_room},
            )

        self.plan = new_plan
