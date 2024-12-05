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

    def draw(self, board):
        pygame.draw.circle(
            board.screen,
            self.color,
            (
                self.x * board.CELL_SIZE + board.CELL_SIZE // 2,
                self.y * board.CELL_SIZE + board.CELL_SIZE // 2,
            ),
            board.CELL_SIZE // 3,
        )

        # Draw a small indicator of the self's plan
        if self.plan:
            if self.plan.type == PlanType.STAY:
                # Draw an empty box inside the self
                pygame.draw.rect(
                    board.screen,
                    (0, 0, 0),
                    (
                        self.x * board.CELL_SIZE + board.CELL_SIZE // 4,
                        self.y * board.CELL_SIZE + board.CELL_SIZE // 4,
                        board.CELL_SIZE // 2,
                        board.CELL_SIZE // 2,
                    ),
                    1,
                )
            elif self.plan.type == PlanType.GOTO_ROOM:
                # Draw an arrow pointing towards the desired room
                target_room = self.plan.target
                target_x, target_y = next(
                    (
                        (x, y)
                        for x, y in board.rooms[target_room].cells
                        if (x, y) != (self.x, self.y)
                    ),
                    None,
                )
                if target_x is not None and target_y is not None:
                    dx = target_x - self.x
                    dy = target_y - self.y
                    length = (dx**2 + dy**2) ** 0.5
                    if length > 0:
                        angle = math.atan2(dy, dx)
                        end_x = self.x * board.CELL_SIZE + board.CELL_SIZE // 2
                        end_y = self.y * board.CELL_SIZE + board.CELL_SIZE // 2
                        tip_x = end_x + int(board.CELL_SIZE // 2 * dx / length)
                        tip_y = end_y + int(board.CELL_SIZE // 2 * dy / length)
                        pygame.draw.line(
                            board.screen,
                            (0, 0, 0),
                            (
                                self.x * board.CELL_SIZE + board.CELL_SIZE // 2,
                                self.y * board.CELL_SIZE + board.CELL_SIZE // 2,
                            ),
                            (tip_x, tip_y),
                            2,
                        )
                        pygame.draw.line(
                            board.screen,
                            (0, 0, 0),
                            (tip_x, tip_y),
                            (
                                tip_x + int(board.CELL_SIZE // 8 * dx / length),
                                tip_y + int(board.CELL_SIZE // 8 * dy / length),
                            ),
                            2,
                        )
            elif self.plan.type == PlanType.FIND_TOKEN:
                # Draw an arrow pointing towards the desired self
                target_self = board.tokens[self.plan.target]
                target_x, target_y = (
                    target_self.x * board.CELL_SIZE + board.CELL_SIZE // 2,
                    target_self.y * board.CELL_SIZE + board.CELL_SIZE // 2,
                )
                dx = target_x - self.x * board.CELL_SIZE - board.CELL_SIZE // 2
                dy = target_y - self.y * board.CELL_SIZE - board.CELL_SIZE // 2
                length = (dx**2 + dy**2) ** 0.5
                if length > 0:
                    angle = math.atan2(dy, dx)
                    end_x = self.x * board.CELL_SIZE + board.CELL_SIZE // 2
                    end_y = self.y * board.CELL_SIZE + board.CELL_SIZE // 2
                    tip_x = end_x + int(board.CELL_SIZE // 2 * dx / length)
                    tip_y = end_y + int(board.CELL_SIZE // 2 * dy / length)
                    pygame.draw.line(
                        board.screen,
                        (255, 0, 0),
                        (
                            self.x * board.CELL_SIZE + board.CELL_SIZE // 2,
                            self.y * board.CELL_SIZE + board.CELL_SIZE // 2,
                        ),
                        (tip_x, tip_y),
                        2,
                    )
                    pygame.draw.line(
                        board.screen,
                        (255, 0, 0),
                        (tip_x, tip_y),
                        (
                            tip_x + int(board.CELL_SIZE // 8 * dx / length),
                            tip_y + int(board.CELL_SIZE // 8 * dy / length),
                        ),
                        2,
                    )
