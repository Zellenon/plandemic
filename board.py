import pygame
import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Union
from enum import Enum
from collections import deque

from agents import Agent, Plan, PlanType
from controller import GameController
from conversation_handler import handle_room_conversations



@dataclass
class Room:
    id: str
    cells: Set[Tuple[int, int]]
    connected_rooms: Set[str]
    color: Tuple[int, int, int]


class BoardGame:
    def __init__(self, board_file: str, doors_file: str, num_agents: int):
        pygame.init()
        self.paused = False
        self.selected_agent = None
        self.CELL_SIZE = 40
        self.rooms: Dict[str, Room] = {}
        self.agents: List[Agent] = []
        self.doors: Dict[str, Set[str]] = {}

        self.controller = GameController(self)

        # Load and parse the board and doors files
        self.load_doors(doors_file)
        self.load_board(board_file)

        # Calculate window dimensions
        with open(board_file, "r") as f:
            lines = f.readlines()
            self.height = len(lines)
            self.width = len(lines[0].strip())

        # Initialize display
        self.screen = pygame.display.set_mode(
            (self.width * self.CELL_SIZE, self.height * self.CELL_SIZE + 50)
        )
        pygame.display.set_caption("Board Game Framework")

        # Create "Stop" button
        self.stop_button_rect = pygame.Rect(10, self.height * self.CELL_SIZE + 10, 120, 30)


        # Initialize agents
        self.initialize_agents(num_agents)
        
    def draw_buttons(self):
        """Draw the pause/resume button."""
        color = (200, 50, 50) if not self.paused else (50, 200, 50)  # Red for running, green for paused
        pygame.draw.rect(self.screen, color, self.stop_button_rect)
        font = pygame.font.Font(None, 24)
        text = "Pause" if not self.paused else "Resume"
        text_render = font.render(text, True, (255, 255, 255))
        self.screen.blit(text_render, text_render.get_rect(center=self.stop_button_rect.center))
        
    def draw_agent_info(self):
        """Draw conversation history for the selected agent."""
        if self.selected_agent:
            font = pygame.font.Font(None, 24)
            y_offset = self.height * self.CELL_SIZE + 10  # Start below the board
            x_offset = 10
            history = self.selected_agent.memory[-5:]  # Show last 5 conversations
            for line in history:
                text = font.render(line, True, (0, 0, 0))
                self.screen.blit(text, (x_offset, y_offset))
                y_offset += 20

        
    def handle_button_click(self, event):
        """Handle mouse click events for the stop button."""
        if self.stop_button_rect.collidepoint(event.pos):
            self.paused = not self.paused  # Toggle pause state
            print("Simulation paused." if self.paused else "Simulation resumed.")
            
    def handle_agent_click(self, event):
        """Handle mouse clicks on agents to select their conversation history."""
        for agent in self.agents:
            # Define the clickable area for the agent
            agent_rect = pygame.Rect(
                agent.x * self.CELL_SIZE,
                agent.y * self.CELL_SIZE,
                self.CELL_SIZE,
                self.CELL_SIZE,
            )
            if agent_rect.collidepoint(event.pos):
                self.selected_agent = agent
                print(f"Selected Agent {agent.id}'s conversation history:")
                for line in agent.memory:
                    print(line)
                break
        else:
            self.selected_agent = None  # Deselect if no agent clicked




    def load_doors(self, doors_file: str):
        """Load door connections from file."""
        self.doors = {}
        with open(doors_file, "r") as f:
            for line in f:
                room1, room2 = line.strip()
                if room1 not in self.doors:
                    self.doors[room1] = set()
                if room2 not in self.doors:
                    self.doors[room2] = set()
                self.doors[room1].add(room2)
                self.doors[room2].add(room1)

    def find_room_borders(
        self, board_lines: List[str]
    ) -> List[Tuple[Tuple[int, int], Tuple[int, int], str, str]]:
        """Find borders between rooms. Returns list of (start, end, room1_id, room2_id)."""
        borders = []
        height = len(board_lines)
        width = len(board_lines[0])

        # Helper function to create a border key
        def make_border_key(p1, p2):
            return tuple(sorted([p1, p2]))

        # Keep track of borders we've already added to avoid duplicates
        added_borders = set()

        # Check horizontal borders
        for y in range(height):
            for x in range(width - 1):
                room1 = board_lines[y][x]
                room2 = board_lines[y][x + 1]
                if room1 != room2:
                    border = ((x + 1, y), (x + 1, y + 1))
                    border_key = make_border_key(border[0], border[1])
                    if border_key not in added_borders:
                        borders.append((*border, room1, room2))
                        added_borders.add(border_key)

        # Check vertical borders
        for x in range(width):
            for y in range(height - 1):
                room1 = board_lines[y][x]
                room2 = board_lines[y + 1][x]
                if room1 != room2:
                    border = ((x, y + 1), (x + 1, y + 1))
                    border_key = make_border_key(border[0], border[1])
                    if border_key not in added_borders:
                        borders.append((*border, room1, room2))
                        added_borders.add(border_key)

        return borders

    def load_board(self, board_file: str):
        """Load and parse the board layout from a text file."""
        with open(board_file, "r") as f:
            lines = [line.strip() for line in f.readlines()]

        # Collect cells for each room
        room_cells: Dict[str, Set[Tuple[int, int]]] = {}
        for y, line in enumerate(lines):
            for x, cell in enumerate(line):
                if cell not in room_cells:
                    room_cells[cell] = set()
                room_cells[cell].add((x, y))

        # Generate random colors for rooms
        colors = {
            room_id: (
                random.randint(50, 200),
                random.randint(50, 200),
                random.randint(50, 200),
            )
            for room_id in room_cells.keys()
        }

        # Create rooms
        for room_id, cells in room_cells.items():
            connected = self.doors.get(room_id, set())
            self.rooms[room_id] = Room(
                id=room_id,
                cells=cells,
                connected_rooms=connected,
                color=colors[room_id],
            )

        # Store borders for drawing
        self.borders = self.find_room_borders(lines)

    def initialize_agents(self, num_agents: int):
        """Place agents randomly on the board."""
        room_ids = list(self.rooms.keys())
        self.agents: List[Agent] = []
        personalities = ["friendly", "hostile", "neutral"]  # Define personality types


        for i in range(num_agents):
            room_id = random.choice(room_ids)
            room = self.rooms[room_id]
            x, y = random.choice(list(room.cells))
            agent = Agent(
                id=i,
                x=x,
                y=y,
                color=(
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                ),
                current_room=room_id,
                plan=None,
                personality=random.choice(personalities)  # Assign a random personality

            )
            self.agents.append(agent)

    def find_path_to_room(
        self, start_room: str, target_room: str
    ) -> Optional[List[str]]:
        """Find the shortest path between two rooms using BFS."""
        if start_room == target_room:
            return [start_room]

        queue = deque([(start_room, [start_room])])
        visited = {start_room}

        while queue:
            current_room, path = queue.popleft()
            for next_room in self.rooms[current_room].connected_rooms:
                if next_room == target_room:
                    return path + [next_room]
                if next_room not in visited:
                    visited.add(next_room)
                    queue.append((next_room, path + [next_room]))

        return None

    def get_unvisited_connected_room(self, agent: Agent) -> Optional[str]:
        """Get a random unvisited connected room, or any connected room if all have been visited."""
        current_room = self.rooms[agent.current_room]
        unvisited = [
            room
            for room in current_room.connected_rooms
            if room not in (agent.plan.visited_rooms if agent.plan else [])
        ]

        if unvisited:
            return random.choice(unvisited)
        return (
            random.choice(list(current_room.connected_rooms))
            if current_room.connected_rooms
            else None
        )

    def draw_border(
        self, start: Tuple[int, int], end: Tuple[int, int], room1: str, room2: str
    ):
        """Draw a border line segment, either solid or dotted."""
        start_pixel = (start[0] * self.CELL_SIZE, start[1] * self.CELL_SIZE)
        end_pixel = (end[0] * self.CELL_SIZE, end[1] * self.CELL_SIZE)

        # Check if rooms are connected by a door
        is_door = room2 in self.doors.get(room1, set())

        if is_door:
            # Draw dotted line
            length = (
                (end_pixel[0] - start_pixel[0]) ** 2
                + (end_pixel[1] - start_pixel[1]) ** 2
            ) ** 0.5
            dash_length = 5
            num_dashes = int(length / (dash_length * 2))

            for i in range(num_dashes):
                t1 = i / num_dashes
                t2 = (i + 0.5) / num_dashes
                x1 = start_pixel[0] + (end_pixel[0] - start_pixel[0]) * t1
                y1 = start_pixel[1] + (end_pixel[1] - start_pixel[1]) * t1
                x2 = start_pixel[0] + (end_pixel[0] - start_pixel[0]) * t2
                y2 = start_pixel[1] + (end_pixel[1] - start_pixel[1]) * t2
                pygame.draw.line(self.screen, (0, 0, 0), (x1, y1), (x2, y2), 2)
        else:
            # Draw solid line
            pygame.draw.line(self.screen, (0, 0, 0), start_pixel, end_pixel, 2)
    
    
    def draw_agents(self):
        for agent in self.agents:
            color = (255, 255, 0) if agent == self.selected_agent else agent.color
            pygame.draw.circle(
                self.screen,
                color,
                (
                    agent.x * self.CELL_SIZE + self.CELL_SIZE // 2,
                    agent.y * self.CELL_SIZE + self.CELL_SIZE // 2,
                ),
                self.CELL_SIZE // 3,
            )


    def execute_plan(self, agent: Agent):
        """Execute the agent's current plan."""
        agent.ensure_plan(self)

        if agent.plan.type == PlanType.STAY:
            agent.plan.turns_remaining -= 1
            if agent.plan.turns_remaining <= 0:
                agent.plan = None

        elif agent.plan.type == PlanType.GOTO_ROOM:
            path = self.find_path_to_room(agent.current_room, agent.plan.target)
            if path and len(path) > 1:
                # Move to next room in path
                next_room = path[1]
                new_pos = random.choice(list(self.rooms[next_room].cells))
                agent.x, agent.y = new_pos
                agent.current_room = next_room
            else:
                # Either reached target or no path exists
                agent.plan = None

        elif agent.plan.type == PlanType.FIND_AGENT:
            target_agent = self.agents[agent.plan.target]
            if agent.current_room == target_agent.current_room:
                # Found the target agent
                agent.plan = None

            else:
                # Try to move to an unvisited connected room
                next_room = self.get_unvisited_connected_room(agent)
                if next_room:
                    agent.plan.visited_rooms.add(next_room)
                    new_pos = random.choice(list(self.rooms[next_room].cells))
                    agent.x, agent.y = new_pos
                    agent.current_room = next_room
                else:
                    # No more rooms to explore
                    agent.plan = None

        agent.ensure_plan(self)

    def move_agents(self):
        """Move all agents according to their plans."""
        for agent in self.agents:
            self.execute_plan(agent)
            
        self.handle_conversations()


    def draw_rooms(self):
        for room in self.rooms.values():
            for x, y in room.cells:
                pygame.draw.rect(
                    self.screen,
                    room.color,
                    (
                        x * self.CELL_SIZE,
                        y * self.CELL_SIZE,
                        self.CELL_SIZE,
                        self.CELL_SIZE,
                    ),
                )

        for start, end, room1, room2 in self.borders:
            self.draw_border(start, end, room1, room2)

    def draw(self):
        """Draw the current game state."""
        self.screen.fill((255, 255, 255))

        # Draw rooms
        self.draw_rooms()
        
        self.draw_agents()

    def run(self):
        """Main game loop."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_button_click(event)  # Check for button click
                    self.handle_agent_click(event)  # Handle agent clicks

            if not self.paused:
                self.controller.handle_events()
                handle_room_conversations(self.agents, self.controller.turn)

                
                # self.move_agents()              # Move agents
            
            self.draw()
            self.draw_buttons()
            self.draw_agent_info() 
            pygame.display.flip()

        pygame.quit()
