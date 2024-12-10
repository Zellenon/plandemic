import pygame
import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Union
from enum import Enum
from collections import deque
from plan import Plan, PlanType



class PlanType(Enum):
    STAY = "stay"
    GOTO_ROOM = "goto_room"
    FIND_AGENT = "find_agent"

@dataclass
class Agent:
    id: int
    x: int
    y: int
    color: Tuple[int, int, int]
    current_room: str
    memory: List[str] = field(default_factory=list)  # Stores conversation history
    last_conversation_turn: int = -1  # Tracks the last turn the agent conversed
    plan: Optional[Plan] = None  # Current goal or action plan
    personality: str = field(default_factory=lambda: random.choice(["friendly", "hostile", "neutral"]))
    target_x: Optional[int] = None  # Target x-coordinate for movement
    target_y: Optional[int] = None  # Target y-coordinate for movement
    move_speed: float = 0.025        # Speed of movement (fraction of a grid cell per frame)
    

    def remember_conversation(self, other_id: int, dialogue: str):
        """Store a conversation in the agent's memory."""
        self.memory.append(f"With {other_id}: {dialogue}")
        # Limit memory to the last 10 conversations
        if len(self.memory) > 10:
            self.memory.pop(0)


    def ensure_plan(self, board):
        """Ensures the agent has a plan by generating a new one if current plan is None"""
        if not self.plan:
            self.choose_random_plan(board)

    def choose_random_plan(self, board):
        """Choose a random new plan for a agent."""
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

        else:  # FIND_AGENT
            # Choose a random agent that's not this one
            available_agents = {t.id for t in board.agents} - {self.id}
            target_agent = random.choice(list(available_agents))
            new_plan = Plan(
                type=PlanType.FIND_AGENT,
                target=target_agent,
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
            elif self.plan.type == PlanType.FIND_AGENT:
                # Draw an arrow pointing towards the desired self
                target_self = board.agents[self.plan.target]
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

    def is_close(agent1, agent2, distance_threshold=5.0):
        """Check if two agents are within a specified distance threshold."""
        distance = math.sqrt((agent1.x - agent2.x)**2 + (agent1.y - agent2.y)**2)
        return distance <= distance_threshold
    
    def move_toward_target(self, board):
        """Move the agent incrementally toward the target position."""
        if self.target_x is None or self.target_y is None:
            return

        # Calculate the direction vector
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = (dx**2 + dy**2)**0.5

        # If the agent is already close enough, snap to the target
        if distance < self.move_speed:
            self.x = self.target_x
            self.y = self.target_y
            self.target_x = None
            self.target_y = None
            return

        # Normalize the direction vector and scale by move_speed
        if distance > 0:
            self.x += (dx / distance) * self.move_speed
            self.y += (dy / distance) * self.move_speed


    def set_target(self, target_room_id, board):
        """Set a new target position, ensuring agents use doors to move between rooms."""
        if self.current_room == target_room_id:
            # Target is within the same room
            target_cell = random.choice(list(board.rooms[self.current_room].cells))
            self.target_x, self.target_y = target_cell
        else:
            # Find all doors connecting to the target room
            doors_to_target = [
                door for door in board.rooms[self.current_room].doors
                if target_room_id in board.doors[self.current_room]
            ]
            if doors_to_target:
                # Pick the first door as the target (or use logic to pick the closest door)
                self.target_x, self.target_y = doors_to_target[0]


