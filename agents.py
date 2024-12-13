import pygame
import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Union
from enum import Enum
from collections import deque
from plan import Plan, PlanType
from roles import Role
from dialogue import assess_suspicion


@dataclass
class Agent:
    id: int
    x: float
    y: float
    color: Tuple[int, int, int]
    current_room: str
    plan: Optional[Plan] = None
    personality: str = "neutral"
    memory: List[str] = field(default_factory=list)
    last_conversation_turn: int = -1
    stuck: bool = False
    role: Role = Role.WITCH
    
    # Movement properties
    speed: float = 0.1  # Cells per frame
    target_x: Optional[float] = None
    target_y: Optional[float] = None
    waypoints: List[Tuple[float, float]] = field(default_factory=list)
    current_ingredient: Optional[str] = None  # Track the ingredient being targeted
    
    def set_target(self, x: float, y: float, board):
        """Set a new movement target with pathfinding."""
        if (self.x, self.y) == (x, y):
            return

        # Always use pathfinding to validate movement
        waypoints = board.find_path_through_doors(self, int(x), int(y))
        if waypoints:
            # Set first waypoint as immediate target
            self.target_x, self.target_y = waypoints[0]
            self.waypoints = waypoints[1:]  # Store remaining waypoints
        else:
            return
        

    
    def update_position(self, board) -> bool:
        """Update position using cardinal movement."""
        # If no target, get next waypoint
        if self.target_x is None or self.target_y is None:
            if not self.waypoints:
                self.stuck = True
                return True
            next_waypoint = self.waypoints[0]
            self.target_x, self.target_y = next_waypoint
            self.waypoints.pop(0)
            return False
        
        # Calculate movement
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        
        # If we're very close to target, snap to it
        if abs(dx) < self.speed and abs(dy) < self.speed:
            self.x = self.target_x
            self.y = self.target_y
            self.target_x = None
            self.target_y = None
            # Don't recursively call update_position, let the next frame handle it
            return not bool(self.waypoints)
            
        # Move horizontally first, then vertically
        if abs(dx) > self.speed:
            self.x += self.speed if dx > 0 else -self.speed
        elif abs(dy) > self.speed:
            self.y += self.speed if dy > 0 else -self.speed
            
        return False

    def needs_new_target(self) -> bool:
        """Check if agent needs a new target."""
        return self.target_x is None and self.target_y is None

    def remember_conversation(self, other_id: int, dialogue: str):
        """Store a conversation in the agent's memory."""
        self.memory.append(f"{other_id}: {dialogue}")
        # Limit memory to the last 10 conversations
        if len(self.memory) > 10:
            self.memory.pop(0)


    def ensure_plan(self, board):
        """Ensures the agent has a plan by generating a new one if current plan is None"""
        if not self.plan:
            self.choose_random_plan(board)

    def choose_random_plan(self, board):
        """Choose a random new plan for an agent."""
        attempts = 0
        max_attempts = 5  # Prevent infinite loops
        
        while attempts < max_attempts:
            if self.stuck:
                plan_type = PlanType.GOTO_ROOM
            else:
                plan_type = random.choice([PlanType.STAY, PlanType.GOTO_ROOM])
            
            if plan_type == PlanType.STAY:
                new_plan = Plan(
                    type=PlanType.STAY, 
                    target=None, 
                    turns_remaining=random.randint(1, 4)
                )
                self.stuck = False
                self.plan = new_plan
                return

            elif plan_type == PlanType.GOTO_ROOM:
                # Choose a random room that's not the current room
                available_rooms = {room_id for room_id in board.rooms.keys()} - {self.current_room}
                if not available_rooms:
                    attempts += 1
                    continue
                
                target_room = random.choice(list(available_rooms))
                possible_positions = [
                    pos for pos in board.rooms[target_room].cells 
                    if pos != (int(self.x), int(self.y))
                ]
                
                if possible_positions:
                    target_pos = random.choice(possible_positions)
                    self.set_target(target_pos[0], target_pos[1], board)
                    if self.target_x is not None:  # Only create plan if pathfinding succeeded
                        new_plan = Plan(
                            type=PlanType.GOTO_ROOM,
                            target=target_room,
                            visited_rooms={self.current_room}
                        )
                        self.stuck = False
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
    
    async def vote(self, agents):
        """Agent votes based on suspicions from their memory."""
        suspicion_scores = {}
        dialogues = []

        # Gather dialogues for each conversation in memory
        for memory_entry in self.memory:
            other_id, dialogue = memory_entry.split(": ", 1)  # This should work now
            other_agent = next((a for a in agents if a.id == int(other_id)), None)

            if other_agent:
                dialogues.append(dialogue)  # Collect dialogues for batching

        # Assess suspicion for all dialogues in one call
        if dialogues:
            suspicion_levels = await assess_suspicion(dialogues)  # Call the modified function

            # Map suspicion levels to agents
            for i, memory_entry in enumerate(self.memory):
                other_id = int(memory_entry.split(": ")[0])  # This should also work now
                if i < len(suspicion_levels):  # Check if index is within bounds
                    suspicion_score = suspicion_levels[i]
                    if suspicion_score > 0:  # Check if there is any suspicion
                        suspicion_scores[other_id] = suspicion_scores.get(other_id, 0) + suspicion_score
                # else:
                    # print(f"Warning: No suspicion level for dialogue index {i}.")  # Optional: log a warning

        # Determine the target based on the highest suspicion score
        if suspicion_scores:
            target = max(suspicion_scores, key=suspicion_scores.get)
            print(f"Agent {self.id} votes to accuse Agent {target} based on suspicion.")
            return target
        return None
