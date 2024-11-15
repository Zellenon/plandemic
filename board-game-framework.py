import pygame
import random
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
import os

@dataclass
class Room:
    id: str
    cells: Set[Tuple[int, int]]
    connected_rooms: Set[str]
    color: Tuple[int, int, int]

@dataclass
class Token:
    x: int
    y: int
    color: Tuple[int, int, int]
    current_room: str

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
        with open(board_file, 'r') as f:
            lines = f.readlines()
            self.height = len(lines)
            self.width = len(lines[0].strip())
        
        # Initialize display
        self.screen = pygame.display.set_mode((
            self.width * self.CELL_SIZE,
            self.height * self.CELL_SIZE + 50
        ))
        pygame.display.set_caption("Board Game Framework")
        
        # Create "Next Turn" button
        self.button_rect = pygame.Rect(
            10,
            self.height * self.CELL_SIZE + 10,
            120,
            30
        )
        
        # Initialize tokens
        self.initialize_tokens(num_tokens)

    def load_doors(self, doors_file: str):
        """Load door connections from file."""
        self.doors = {}
        with open(doors_file, 'r') as f:
            for line in f:
                room1, room2 = line.strip()
                if room1 not in self.doors:
                    self.doors[room1] = set()
                if room2 not in self.doors:
                    self.doors[room2] = set()
                self.doors[room1].add(room2)
                self.doors[room2].add(room1)

    def find_room_borders(self, board_lines: List[str]) -> List[Tuple[Tuple[int, int], Tuple[int, int], str, str]]:
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
        with open(board_file, 'r') as f:
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
                random.randint(50, 200)
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
                color=colors[room_id]
            )
        
        # Store borders for drawing
        self.borders = self.find_room_borders(lines)

    def initialize_tokens(self, num_tokens: int):
        """Place tokens randomly on the board."""
        room_ids = list(self.rooms.keys())
        for i in range(num_tokens):
            room_id = random.choice(room_ids)
            room = self.rooms[room_id]
            x, y = random.choice(list(room.cells))
            token = Token(
                x=x,
                y=y,
                color=(
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255)
                ),
                current_room=room_id
            )
            self.tokens.append(token)

    def move_tokens(self):
        """Move all tokens to random connected rooms."""
        for token in self.tokens:
            current_room = self.rooms[token.current_room]
            if current_room.connected_rooms:
                next_room_id = random.choice(list(current_room.connected_rooms))
                next_room = self.rooms[next_room_id]
                new_pos = random.choice(list(next_room.cells))
                token.x, token.y = new_pos
                token.current_room = next_room_id

    def draw_border(self, start: Tuple[int, int], end: Tuple[int, int], room1: str, room2: str):
        """Draw a border line segment, either solid or dotted."""
        start_pixel = (start[0] * self.CELL_SIZE, start[1] * self.CELL_SIZE)
        end_pixel = (end[0] * self.CELL_SIZE, end[1] * self.CELL_SIZE)
        
        # Check if rooms are connected by a door
        is_door = room2 in self.doors.get(room1, set())
        
        if is_door:
            # Draw dotted line
            length = ((end_pixel[0] - start_pixel[0])**2 + 
                     (end_pixel[1] - start_pixel[1])**2)**0.5
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

    def draw(self):
        """Draw the current game state."""
        self.screen.fill((255, 255, 255))
        
        # Draw rooms
        for room in self.rooms.values():
            for x, y in room.cells:
                pygame.draw.rect(
                    self.screen,
                    room.color,
                    (x * self.CELL_SIZE,
                     y * self.CELL_SIZE,
                     self.CELL_SIZE,
                     self.CELL_SIZE)
                )
        
        # Draw borders
        for start, end, room1, room2 in self.borders:
            self.draw_border(start, end, room1, room2)
        
        # Draw tokens
        for token in self.tokens:
            pygame.draw.circle(
                self.screen,
                token.color,
                (token.x * self.CELL_SIZE + self.CELL_SIZE // 2,
                 token.y * self.CELL_SIZE + self.CELL_SIZE // 2),
                self.CELL_SIZE // 3
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
