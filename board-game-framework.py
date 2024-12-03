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
class Room:
    id: str
    cells: Set[Tuple[int, int]]
    connected_rooms: Set[str]
    color: Tuple[int, int, int]


@dataclass
class Token:
    id: int
    x: int
    y: int
    color: Tuple[int, int, int]
    current_room: str
    plan: Optional[Plan] = None


class BoardGame:
    def __init__(self, board_file: str, doors_file: str, num_tokens: int):
        pygame.init()
        self.CELL_SIZE = 40
        self.rooms: Dict[str, Room] = {}
        self.tokens: List[Token] = []
        self.doors: Dict[str, Set[str]] = {}

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

        # Create "Next Turn" button
        self.button_rect = pygame.Rect(10, self.height * self.CELL_SIZE + 10, 120, 30)

        # Initialize tokens
        self.initialize_tokens(num_tokens)

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

    def initialize_tokens(self, num_tokens: int):
        """Place tokens randomly on the board."""
        room_ids = list(self.rooms.keys())
        self.tokens: List[Token] = []

        for i in range(num_tokens):
            room_id = random.choice(room_ids)
            room = self.rooms[room_id]
            x, y = random.choice(list(room.cells))
            token = Token(
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
            )
            self.tokens.append(token)

    def choose_new_plan(self, token: Token) -> Plan:
        """Choose a random new plan for a token."""
        plan_type = random.choice(list(PlanType))

        if plan_type == PlanType.STAY:
            return Plan(
                type=PlanType.STAY, target=None, turns_remaining=random.randint(1, 4)
            )

        elif plan_type == PlanType.GOTO_ROOM:
            # Choose a random room that's not the current room
            available_rooms = [
                room_id
                for room_id in self.rooms.keys()
                if room_id != token.current_room
            ]
            target_room = random.choice(available_rooms)
            return Plan(
                type=PlanType.GOTO_ROOM,
                target=target_room,
                visited_rooms={token.current_room},
            )

        else:  # FIND_TOKEN
            # Choose a random token that's not this one
            available_tokens = [t.id for t in self.tokens if t.id != token.id]
            target_token = random.choice(available_tokens)
            return Plan(
                type=PlanType.FIND_TOKEN,
                target=target_token,
                visited_rooms={token.current_room},
            )

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

    def get_unvisited_connected_room(self, token: Token) -> Optional[str]:
        """Get a random unvisited connected room, or any connected room if all have been visited."""
        current_room = self.rooms[token.current_room]
        unvisited = [
            room
            for room in current_room.connected_rooms
            if room not in (token.plan.visited_rooms if token.plan else [])
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

    def execute_plan(self, token: Token):
        """Execute the token's current plan."""
        if token.plan is None:
            token.plan = self.choose_new_plan(token)
            return

        if token.plan.type == PlanType.STAY:
            token.plan.turns_remaining -= 1
            if token.plan.turns_remaining <= 0:
                token.plan = None
            return

        elif token.plan.type == PlanType.GOTO_ROOM:
            path = self.find_path_to_room(token.current_room, token.plan.target)
            if path and len(path) > 1:
                # Move to next room in path
                next_room = path[1]
                new_pos = random.choice(list(self.rooms[next_room].cells))
                token.x, token.y = new_pos
                token.current_room = next_room
            else:
                # Either reached target or no path exists
                token.plan = None
            return

        elif token.plan.type == PlanType.FIND_TOKEN:
            target_token = self.tokens[token.plan.target]
            if token.current_room == target_token.current_room:
                # Found the target token
                token.plan = None
                return

            # Try to move to an unvisited connected room
            next_room = self.get_unvisited_connected_room(token)
            if next_room:
                token.plan.visited_rooms.add(next_room)
                new_pos = random.choice(list(self.rooms[next_room].cells))
                token.x, token.y = new_pos
                token.current_room = next_room
            else:
                # No more rooms to explore
                token.plan = None

    def move_tokens(self):
        """Move all tokens according to their plans."""
        for token in self.tokens:
            self.execute_plan(token)

    def draw(self):
        """Draw the current game state."""
        self.screen.fill((255, 255, 255))

        # Draw rooms
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

        # Draw borders
        for start, end, room1, room2 in self.borders:
            self.draw_border(start, end, room1, room2)

        # Draw tokens with their plan types indicated
        for token in self.tokens:
            # Draw the token
            pygame.draw.circle(
                self.screen,
                token.color,
                (
                    token.x * self.CELL_SIZE + self.CELL_SIZE // 2,
                    token.y * self.CELL_SIZE + self.CELL_SIZE // 2,
                ),
                self.CELL_SIZE // 3,
            )

            # Draw a small indicator of the token's plan
            if token.plan:
                if token.plan.type == PlanType.STAY:
                    # Draw an empty box inside the token
                    pygame.draw.rect(
                        self.screen,
                        (0, 0, 0),
                        (
                            token.x * self.CELL_SIZE + self.CELL_SIZE // 4,
                            token.y * self.CELL_SIZE + self.CELL_SIZE // 4,
                            self.CELL_SIZE // 2,
                            self.CELL_SIZE // 2,
                        ),
                        1,
                    )
                elif token.plan.type == PlanType.GOTO_ROOM:
                    # Draw an arrow pointing towards the desired room
                    target_room = token.plan.target
                    target_x, target_y = next(
                        (
                            (x, y)
                            for x, y in self.rooms[target_room].cells
                            if (x, y) != (token.x, token.y)
                        ),
                        None,
                    )
                    if target_x is not None and target_y is not None:
                        dx = target_x - token.x
                        dy = target_y - token.y
                        length = (dx**2 + dy**2) ** 0.5
                        if length > 0:
                            angle = math.atan2(dy, dx)
                            end_x = token.x * self.CELL_SIZE + self.CELL_SIZE // 2
                            end_y = token.y * self.CELL_SIZE + self.CELL_SIZE // 2
                            tip_x = end_x + int(self.CELL_SIZE // 2 * dx / length)
                            tip_y = end_y + int(self.CELL_SIZE // 2 * dy / length)
                            pygame.draw.line(
                                self.screen,
                                (0, 0, 0),
                                (
                                    token.x * self.CELL_SIZE + self.CELL_SIZE // 2,
                                    token.y * self.CELL_SIZE + self.CELL_SIZE // 2,
                                ),
                                (tip_x, tip_y),
                                2,
                            )
                            pygame.draw.line(
                                self.screen,
                                (0, 0, 0),
                                (tip_x, tip_y),
                                (
                                    tip_x + int(self.CELL_SIZE // 8 * dx / length),
                                    tip_y + int(self.CELL_SIZE // 8 * dy / length),
                                ),
                                2,
                            )
                elif token.plan.type == PlanType.FIND_TOKEN:
                    # Draw an arrow pointing towards the desired token
                    target_token = self.tokens[token.plan.target]
                    target_x, target_y = (
                        target_token.x * self.CELL_SIZE + self.CELL_SIZE // 2,
                        target_token.y * self.CELL_SIZE + self.CELL_SIZE // 2,
                    )
                    dx = target_x - token.x * self.CELL_SIZE - self.CELL_SIZE // 2
                    dy = target_y - token.y * self.CELL_SIZE - self.CELL_SIZE // 2
                    length = (dx**2 + dy**2) ** 0.5
                    if length > 0:
                        angle = math.atan2(dy, dx)
                        end_x = token.x * self.CELL_SIZE + self.CELL_SIZE // 2
                        end_y = token.y * self.CELL_SIZE + self.CELL_SIZE // 2
                        tip_x = end_x + int(self.CELL_SIZE // 2 * dx / length)
                        tip_y = end_y + int(self.CELL_SIZE // 2 * dy / length)
                        pygame.draw.line(
                            self.screen,
                            (255, 0, 0),
                            (
                                token.x * self.CELL_SIZE + self.CELL_SIZE // 2,
                                token.y * self.CELL_SIZE + self.CELL_SIZE // 2,
                            ),
                            (tip_x, tip_y),
                            2,
                        )
                        pygame.draw.line(
                            self.screen,
                            (255, 0, 0),
                            (tip_x, tip_y),
                            (
                                tip_x + int(self.CELL_SIZE // 8 * dx / length),
                                tip_y + int(self.CELL_SIZE // 8 * dy / length),
                            ),
                            2,
                        )

        # Draw button
        pygame.draw.rect(self.screen, (200, 200, 200), self.button_rect)
        font = pygame.font.Font(None, 36)
        text = font.render("Next Turn", True, (0, 0, 0))
        text_rect = text.get_rect(center=self.button_rect.center)
        self.screen.blit(text, text_rect)

    def run(self):
        """Main game loop."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.button_rect.collidepoint(event.pos):
                        self.move_tokens()

            self.draw()
            pygame.display.flip()

        pygame.quit()


# Example usage
if __name__ == "__main__":
    game = BoardGame("board.txt", "doors.txt", num_tokens=5)
    game.run()
