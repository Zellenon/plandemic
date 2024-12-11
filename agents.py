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
    x: float
    y: float
    color: Tuple[int, int, int]
    current_room: str
    plan: Optional[Plan] = None
    personality: str = "neutral"
    memory: List[str] = field(default_factory=list)
    last_conversation_turn: int = -1
    stuck: bool = False
    
    # Movement properties
    speed: float = 0.1  # Cells per frame
    target_x: Optional[float] = None
    target_y: Optional[float] = None
    waypoints: List[Tuple[float, float]] = field(default_factory=list)
    
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
            if self.id == 0:
                print(f"Agent {self.id} set target to ({self.target_x}, {self.target_y})")
                print(f"Remaining waypoints: {self.waypoints}")
        else:
            if self.id == 0:
                print(f"Agent {self.id} could not find valid path to ({x}, {y})")
            return
    
    def update_position(self, board) -> bool:
        """Update position using cardinal movement."""
        if self.target_x is None or self.target_y is None:
            if self.waypoints:
                next_waypoint = self.waypoints[0]
                current_room = board.get_room_at_position(next_waypoint[0], next_waypoint[1])
                
                if current_room != self.current_room:
                    # We need to go through a door
                    door = board.door_manager.get_door_between_rooms(self.current_room, current_room)
                    if door:
                        door_pos = board.door_manager.get_door_position(door.room1, door.room2)
                        # Check if we've crossed the threshold
                        if door.is_horizontal():
                            crossed = (self.current_room == door.room1 and self.y > door_pos[1]) or \
                                    (self.current_room == door.room2 and self.y < door_pos[1])
                        else:  # vertical door
                            crossed = (self.current_room == door.room1 and self.x > door_pos[0]) or \
                                    (self.current_room == door.room2 and self.x < door_pos[0])
                        
                        if crossed:
                            # We've crossed the threshold, update room and proceed
                            self.current_room = current_room
                            self.waypoints.pop(0)
                            self.target_x, self.target_y = next_waypoint
                        else:
                            # Calculate position just inside the next room
                            if door.is_horizontal():
                                # Move one cell above/below the door
                                entry_y = door_pos[1] + (1 if self.current_room == door.room1 else -1)
                                entry_pos = (door_pos[0], entry_y)
                            else:  # vertical door
                                # Move one cell left/right of the door
                                entry_x = door_pos[0] + (1 if self.current_room == door.room1 else -1)
                                entry_pos = (entry_x, door_pos[1])
                                
                            if (self.x, self.y) == entry_pos:
                                # We're fully through the door, proceed to next waypoint
                                self.current_room = current_room
                                self.waypoints.pop(0)
                                self.target_x, self.target_y = next_waypoint
                            else:
                                # Move to entry position first
                                self.target_x, self.target_y = entry_pos
                            return False
                
                # If in same room or no door needed, proceed to waypoint
                self.waypoints.pop(0)
                self.target_x, self.target_y = next_waypoint
                if self.id == 0:
                    print(f"Agent {self.id} moving to next waypoint: ({self.target_x}, {self.target_y})")
                return False
            
            self.ensure_plan(board)
            return True

        # Decide whether to move horizontally first, then vertically
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        
        # If we're very close to target, snap to it
        if abs(dx) < self.speed and abs(dy) < self.speed:
            self.x = self.target_x
            self.y = self.target_y
            self.target_x = None
            self.target_y = None
            if self.id == 0:
                print(f"Agent {self.id} reached target: ({self.x}, {self.y})")
            return self.update_position(board)  # Check for next waypoint
            
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
        self.memory.append(f"With {other_id}: {dialogue}")
        # Limit memory to the last 10 conversations
        if len(self.memory) > 10:
            self.memory.pop(0)


    def ensure_plan(self, board):
        """Ensures the agent has a plan by generating a new one if current plan is None"""
        if not self.plan:
            self.choose_random_plan(board)

    def choose_random_plan(self, board):
        """Choose a random new plan for an agent."""
        if self.stuck:
            # If agent is stuck, force a GOTO_ROOM plan
            plan_type = PlanType.GOTO_ROOM
        else:
            plan_type = random.choice([PlanType.STAY, PlanType.GOTO_ROOM])
        
        new_plan = None

        if plan_type == PlanType.STAY:
            new_plan = Plan(
                type=PlanType.STAY, 
                target=None, 
                turns_remaining=random.randint(1, 4)
            )
            self.stuck = False  # Reset stuck flag when choosing to stay

        elif plan_type == PlanType.GOTO_ROOM:
            # Choose a random room that's not the current room
            available_rooms = {room_id for room_id in board.rooms.keys()} - {self.current_room}
            if not available_rooms:
                return None  # No available rooms to move to
            
            target_room = random.choice(list(available_rooms))
            
            # Get all possible positions except current position
            possible_positions = [
                pos for pos in board.rooms[target_room].cells 
                if pos != (int(self.x), int(self.y))
            ]
            
            if possible_positions:  # Only proceed if we have valid positions
                target_pos = random.choice(possible_positions)
                if self.id == 0:
                    print(f"Agent {self.id} selected target room: {target_room}, position: {target_pos}")
                
                self.set_target(target_pos[0], target_pos[1], board)
                new_plan = Plan(
                    type=PlanType.GOTO_ROOM,
                    target=target_room,
                    visited_rooms={self.current_room},
                )
                self.stuck = False  # Reset stuck flag when successfully setting new target
            else:
                self.stuck = True
                print(f"Agent {self.id} is stuck in room {self.current_room} - no valid positions available")
                return None

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
