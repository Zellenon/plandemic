from dataclasses import dataclass
from typing import Set, Dict, List, Tuple

@dataclass
class Door:
    room1: str
    room2: str
    x1: int
    y1: int
    x2: int
    y2: int
    
    def __hash__(self):
        """Make Door hashable for sets."""
        return hash((self.room1, self.room2, self.x1, self.y1, self.x2, self.y2))
        
    def connects_rooms(self, room1: str, room2: str) -> bool:
        """Check if this door connects the given rooms."""
        return (self.room1 == room1 and self.room2 == room2) or \
               (self.room1 == room2 and self.room2 == room1)
               
    def get_other_room(self, room: str) -> str:
        """Get the room on the other side of the door."""
        if room == self.room1:
            return self.room2
        elif room == self.room2:
            return self.room1
        raise ValueError(f"Room {room} is not connected to this door")

    def is_horizontal(self) -> bool:
        """Return True if this is a horizontal door (same y coordinates)."""
        return self.y1 == self.y2

    def is_vertical(self) -> bool:
        """Return True if this is a vertical door (same x coordinates)."""
        return self.x1 == self.x2

class DoorManager:
    def __init__(self):
        self.doors: List[Door] = []
        self.room_connections: Dict[str, Set[str]] = {}
        
    def load_from_file(self, doors_file: str) -> None:
        """Load doors with their positions from file."""
        with open(doors_file, "r") as f:
            for line in f:
                # Skip empty lines and comments
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                # Parse room1 room2 x1 y1 x2 y2 format
                parts = line.split()
                if len(parts) != 6:
                    continue
                    
                room1, room2, x1, y1, x2, y2 = parts
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                
                # Add to room connections dict
                if room1 not in self.room_connections:
                    self.room_connections[room1] = set()
                if room2 not in self.room_connections:
                    self.room_connections[room2] = set()
                self.room_connections[room1].add(room2)
                self.room_connections[room2].add(room1)
                
                # Create door object with positions
                self.doors.append(Door(room1, room2, x1, y1, x2, y2))
    
    def get_door_position(self, room1: str, room2: str) -> Tuple[int, int]:
        """Get the position of the door between two rooms."""
        for door in self.doors:
            if door.connects_rooms(room1, room2):
                # Return midpoint of the door
                return ((door.x1 + door.x2) // 2, (door.y1 + door.y2) // 2)
        return None
        
    def get_doors_for_room(self, room: str) -> List[Door]:
        """Get all doors connected to a room."""
        return [door for door in self.doors if room in (door.room1, door.room2)]
        
    def get_door_between_rooms(self, room1: str, room2: str) -> Door:
        """Get the door connecting two specific rooms."""
        for door in self.doors:
            if door.connects_rooms(room1, room2):
                return door
        return None 