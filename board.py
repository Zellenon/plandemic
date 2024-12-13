import pygame
import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Union
from enum import Enum
from collections import deque
from PIL import Image

from agents import Agent
from plan import Plan, PlanType
from controller import GameController
from conversation_handler import handle_room_conversations
from doors import DoorManager, Door
from roles import Role
from cauldron import Cauldron



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
        
        self.door_manager = DoorManager()
        self.controller = GameController(self)

        # Load and parse the board and doors files
        self.door_manager.load_from_file(doors_file)
        self.load_board(board_file)

        # Calculate window dimensions
        with open(board_file, "r") as f:
            lines = f.readlines()
            self.height = len(lines)
            self.width = len(lines[0].strip())

        # Initialize display
        self.screen = pygame.display.set_mode(
            (self.width * self.CELL_SIZE + 300, self.height * self.CELL_SIZE + 50)
        )

        pygame.display.set_caption("Board Game Framework")

        # Create "Stop" button
        self.stop_button_rect = pygame.Rect(10, self.height * self.CELL_SIZE + 10, 120, 30)


        # Initialize agents
        self.initialize_agents(num_agents)
        
        self.textures = {}
        self.load_textures()
        
        self.cauldron = Cauldron(x=10, y=7)  # Center of a 21x21 board
        
        # List of ingredient names
        self.ingredients_list = ["eye", "shroom", "berry"]  # Add more as needed
        eye_texture = pygame.image.load("assets/ingredients/eye.png").convert_alpha()
        shroom_texture = pygame.image.load("assets/ingredients/shroom.png").convert_alpha()
        berry_texture = pygame.image.load("assets/ingredients/berry.png").convert_alpha()
        self.ingredients_sprites = {
            "eye": pygame.transform.scale(eye_texture, (self.CELL_SIZE, self.CELL_SIZE))    ,
            "shroom": pygame.transform.scale(shroom_texture, (self.CELL_SIZE, self.CELL_SIZE)),
            "berry": pygame.transform.scale(berry_texture, (self.CELL_SIZE, self.CELL_SIZE)),
        }
        
    def load_textures(self):
        """Load all game textures."""
        try:
            # Load the cauldron texture
            cauldron_texture = pygame.image.load('assets/cauldron.png')
            cauldron_texture = pygame.transform.scale(cauldron_texture, (self.CELL_SIZE, self.CELL_SIZE))  # Scale to cell size
            self.textures['cauldron'] = cauldron_texture.convert_alpha()
            
            # Load the stone texture for room 6
            stone_texture = pygame.image.load('assets/stonefloor1.jpg')
            mossy_texture = pygame.image.load('assets/mossyfloor2.jpg')
            wood_texture = pygame.image.load('assets/woodfloor1.jpg')
            wood_texture2 = pygame.image.load('assets/woodfloor2.jpg')
            cobble_texture = pygame.image.load('assets/cobble1.jpg')
            wood_texture3 = pygame.image.load('assets/woodfloor3.jpg')
            grass_texture = pygame.image.load('assets/grass.jpg')
            dirt_texture = pygame.image.load('assets/dirt.jpg')
            water_texture = pygame.image.load('assets/water.jpg')
            
            
            
            # Scale textures to match cell size
            stone_texture = pygame.transform.scale(stone_texture, (self.CELL_SIZE , self.CELL_SIZE))
            mossy_texture = pygame.transform.scale(mossy_texture, (self.CELL_SIZE, self.CELL_SIZE))
            wood_texture = pygame.transform.scale(wood_texture, (self.CELL_SIZE, self.CELL_SIZE))
            wood_texture2 = pygame.transform.scale(wood_texture2, (self.CELL_SIZE, self.CELL_SIZE))
            cobble_texture = pygame.transform.scale(cobble_texture, (self.CELL_SIZE, self.CELL_SIZE))
            wood_texture3 = pygame.transform.scale(wood_texture3, (self.CELL_SIZE, self.CELL_SIZE))
            grass_texture = pygame.transform.scale(grass_texture, (self.CELL_SIZE, self.CELL_SIZE))
            dirt_texture = pygame.transform.scale(dirt_texture, (self.CELL_SIZE, self.CELL_SIZE))
            water_texture = pygame.transform.scale(water_texture, (self.CELL_SIZE, self.CELL_SIZE))


            # Convert the images for faster rendering
            self.textures['1'] = grass_texture.convert_alpha()
            self.textures['2'] = dirt_texture.convert_alpha()
            self.textures['3'] = cobble_texture.convert_alpha()
            self.textures['4'] = water_texture.convert_alpha()
            self.textures['5'] = wood_texture2.convert_alpha()
            self.textures['6'] = stone_texture.convert_alpha()
            self.textures['7'] = mossy_texture.convert_alpha()
            self.textures['8'] = wood_texture.convert_alpha()
            self.textures['9'] = wood_texture2.convert_alpha()
            self.textures['a'] = wood_texture.convert_alpha()
            self.textures['b'] = mossy_texture.convert_alpha()
            self.textures['c'] = wood_texture2.convert_alpha()
            self.textures['d'] = wood_texture3.convert_alpha()
            self.textures['e'] = stone_texture.convert_alpha()
            self.textures['f'] = wood_texture2.convert_alpha()
            self.textures['g'] = wood_texture3.convert_alpha()
            self.textures['h'] = cobble_texture.convert_alpha()
        except pygame.error as e:
            print(f"Could not load texture: {e}")
            for id, texture in self.textures:
                self.textures[id] = None

            
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
                text = font.render(line, True, (255, 255, 255))
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
        """Load and parse the board file."""
        with open(board_file, "r") as f:
            board_lines = [line.strip() for line in f.readlines()]

        # Process each character in the board file
        for y, line in enumerate(board_lines):
            for x, char in enumerate(line):
                if char == " ":
                    continue
                if char not in self.rooms:
                    # Generate a pastel color based on room ID
                    color_seed = sum(ord(c) for c in char)
                    random.seed(color_seed)
                    color = (
                        random.randint(100, 200),
                        random.randint(100, 200),
                        random.randint(100, 200)
                    )
                    random.seed()  # Reset seed
                    
                    self.rooms[char] = Room(
                        id=char,
                        color=color,
                        cells=set(),
                        connected_rooms=set()
                    )
                self.rooms[char].cells.add((x, y))
                connected = self.door_manager.room_connections.get(char, set())
                self.rooms[char].connected_rooms.update(connected)
        
        # Find and store borders
        self.borders = self.find_room_borders(board_lines)

    def initialize_agents(self, num_agents: int):
        """Place agents randomly on the board."""
        room_ids = list(self.rooms.keys())
        self.agents: List[Agent] = []
        personalities = [
            "friendly", 
            "hostile", 
            "neutral", 
            "suspicious", 
            "curious", 
            "aggressive", 
            "cautious", 
            "cheerful", 
            "sarcastic"
        ]

        # Randomly select one impostor
        impostor_index = random.randint(0, num_agents - 1)

        for i in range(num_agents):
            room_id = random.choice(room_ids)
            room = self.rooms[room_id]
            x, y = random.choice(list(room.cells))
            
            # Assign role based on index
            role = Role.IMPOSTOR if i == impostor_index else Role.WITCH
            
            # Set color: red for impostor, random for others
            color = (255, 0, 0) if role == Role.IMPOSTOR else (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )
            
            agent = Agent(
                id=i,
                x=x,
                y=y,
                color=color,  # Use the determined color
                current_room=room_id,
                plan=None,
                personality=random.choice(personalities),  # Assign a random personality
                role=role  # Assign the role
            )
            self.agents.append(agent)

        # Print roles and personalities for verification
        for agent in self.agents:
            print(f"Agent {agent.id} is a {agent.role.value} with personality: {agent.personality}.")

    def find_path_to_room(
        self, start_room: str, target_room: str
    ) -> List[str]:
        """Find path from start_room to target_room using BFS."""
        if start_room == target_room:
            return [start_room]
        
        queue = deque([(start_room, [start_room])])
        visited = {start_room}
        
        while queue:
            current_room, path = queue.popleft()
            connected_rooms = self.door_manager.room_connections[current_room]
            
            for next_room in connected_rooms:
                if next_room == target_room:
                    return path + [next_room]
                if next_room not in visited:
                    visited.add(next_room)
                    queue.append((next_room, path + [next_room]))

        return None

    def get_unvisited_connected_room(self, agent: Agent) -> Optional[str]:
        """Get a random unvisited connected room, or any connected room if all have been visited."""
        connected_rooms = self.door_manager.room_connections.get(agent.current_room, set())
        unvisited = [
            room for room in connected_rooms
            if room not in (agent.plan.visited_rooms if agent.plan else [])
        ]

        if unvisited:
            return random.choice(unvisited)
        return random.choice(list(connected_rooms)) if connected_rooms else None

    def draw_border(
        self, start: Tuple[int, int], end: Tuple[int, int], room1: str, room2: str
    ):
        """Draw a border line segment."""
        start_pixel = (start[0] * self.CELL_SIZE, start[1] * self.CELL_SIZE)
        end_pixel = (end[0] * self.CELL_SIZE, end[1] * self.CELL_SIZE)

        # Check if rooms are connected by a door
        is_door = room2 in self.door_manager.room_connections.get(room1, set())

        if not is_door:
            # Only draw solid line for non-door borders
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


    def execute_plan(self, agent):
        """Execute the agent's current plan."""
        if agent.plan.type == PlanType.GO_TO_CAULDRON:
            # Set target to cauldron position
            agent.set_target(self.cauldron.x, self.cauldron.y, self)
            if (agent.x, agent.y) == (self.cauldron.x, self.cauldron.y):
                # Logic for depositing the ingredient
                
                if agent.role == Role.WITCH:
                    self.cauldron.deposit_ingredient()  # Update cauldron state
                    print(f"Agent {agent.id} has deposited their ingredient at the cauldron.")
                else:
                    print(f"Agent {agent.id} is not a witch, cannot deposit ingredient.")
                agent.plan = None  # Clear the plan after depositing
        else:
            # If agent reached current target and has more waypoints
            if (agent.target_x is None and agent.target_y is None and agent.waypoints):
                next_waypoint = agent.waypoints[0]
                agent.set_target(next_waypoint[0], next_waypoint[1], self)
                if agent.target_x is not None:  # Only remove waypoint if target was set successfully
                    agent.waypoints = agent.waypoints[1:]

            agent.ensure_plan(self)

            if agent.plan.type == PlanType.STAY:
                agent.plan.turns_remaining -= 1
                if agent.plan.turns_remaining <= 0:
                    agent.plan = None

            elif agent.plan.type == PlanType.GOTO_ROOM:
                # Set the current ingredient when starting to go to a room
                if agent.current_ingredient is None:
                    agent.current_ingredient = random.choice(self.ingredients_list)  # Choose a random ingredient

                # Update room if agent has moved to a new one
                new_room = self.get_room_at_position(agent.x, agent.y, agent.current_room)
                if new_room and new_room != agent.current_room:
                    agent.current_room = new_room
                    if agent.plan:
                        agent.plan.visited_rooms.add(new_room)

                # Check if we've reached our target room and have no more movement to do
                if (agent.current_room == agent.plan.target and 
                    not agent.waypoints and 
                    agent.target_x is None and 
                    agent.target_y is None):
                    # After reaching the target room, set the plan to go to the cauldron
                    print(f"Agent {agent.id} reached {agent.plan.target}, heading to cauldron.")
                    agent.set_target(self.cauldron.x, self.cauldron.y, self)
                    agent.plan = Plan(
                        type=PlanType.GO_TO_CAULDRON,
                        target="cauldron"
                    )
                    agent.current_ingredient = None  # Clear the ingredient after reaching the room

            agent.update_position(self)

    def move_agents(self):
        """Move all agents according to their plans."""
        for agent in self.agents:
            self.execute_plan(agent)
            
        self.handle_conversations()


    def draw_rooms(self):
        """Draw all rooms with textures where available."""
        # Fill the screen with black first to clear any background
        self.screen.fill((0, 0, 0))
        
        # Draw each room
        for room_id, room in self.rooms.items():
            # Get room bounds
            for x, y in room.cells:
                if room_id in self.textures and self.textures[room_id]:
                    # Draw texture only for rooms that have textures
                    texture = self.textures[room_id]
                    self.screen.blit(
                        texture,
                        (x * self.CELL_SIZE, y * self.CELL_SIZE)
                    )
                else:
                    # Draw solid color for rooms without textures
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

    def draw_door(self, door: Door):
        """Draw a door as a line between rooms."""
        start_pos = (door.x1 * self.CELL_SIZE, door.y1 * self.CELL_SIZE)
        end_pos = (door.x2 * self.CELL_SIZE, door.y2 * self.CELL_SIZE)
        
        pygame.draw.line(
            self.screen,
            (255, 255, 0),  # Yellow color
            start_pos,
            end_pos,
            3  # Line width
        )

 

    def draw(self):
        """Draw the game state."""
        # Draw rooms and walls first
        self.draw_rooms()
        
        # Draw doors as lines
        for door in self.door_manager.doors:
            self.draw_door(door)
        
        # Draw agents
        self.draw_agents()
        
        # Draw the cauldron
        self.draw_cauldron()
        
        # Draw ingredients
        
        # Draw target positions for debugging
        for agent in self.agents:
            if agent.target_x is not None and agent.target_y is not None:
                if agent.plan and agent.plan.type == PlanType.GOTO_ROOM:
                    if agent.current_ingredient:  # Only render if there's a current ingredient
                        ingredient_sprite = self.ingredients_sprites[agent.current_ingredient]
                        self.screen.blit(ingredient_sprite, (
                            agent.target_x * self.CELL_SIZE,
                            agent.target_y * self.CELL_SIZE
                        ))
                else:
                    pygame.draw.circle(
                        self.screen,
                        (255, 0, 0),  # Red target indicator
                        (
                            agent.target_x * self.CELL_SIZE + self.CELL_SIZE // 2,
                            agent.target_y * self.CELL_SIZE + self.CELL_SIZE // 2
                        ),
                        2
                    )
                
    async def voting_phase(self, agents):
        """Conduct the voting phase where agents assess suspicion and vote."""
        votes = {}
        
        for agent in agents:
            vote_target = await agent.vote(agents)  # Await the vote method
            if vote_target is not None:
                if vote_target in votes:
                    votes[vote_target] += 1
                else:
                    votes[vote_target] = 1

        # Determine the agent with the most votes
        if votes:
            most_voted_agent = max(votes, key=votes.get)
            print(f"Agent {most_voted_agent} has been accused with {votes[most_voted_agent]} votes.")
            
            # Handle the outcome of the vote
            self.handle_vote_outcome(most_voted_agent)
        else:
            print("No votes were cast.")

    def handle_vote_outcome(self, agent_id):
        """Handle the outcome of the voting phase."""
        # Logic to remove or mark the agent as out
        agent_to_remove = next((agent for agent in self.agents if agent.id == agent_id), None)
        if agent_to_remove:
            print(f"Agent {agent_to_remove.id} has been voted out of the game.")
            self.agents.remove(agent_to_remove)  # Remove the agent from the game
            # Additional logic to handle the game state after an agent is removed

    async def run(self):
        """Main game loop."""
        running = True
        clock = pygame.time.Clock()
        voting_phase_occurred = False  # Flag to track if voting phase has occurred
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.stop_button_rect.collidepoint(event.pos):
                        self.paused = not self.paused
                    else:
                        self.handle_agent_click(event)

            # Only update game state if not paused
            if not self.paused:
                self.update()
                self.controller.handle_events()
                await handle_room_conversations(self.agents, self.controller.turn)

                # Check if the cauldron has enough ingredients and voting phase hasn't occurred
                if self.cauldron.has_enough_ingredients(3) and not voting_phase_occurred:
                    await self.voting_phase(self.agents)  # Trigger the voting phase
                    print("Resetting cauldron ingredients to 0.")  # Debugging statement
                    self.cauldron.ingredients = 0  # Reset the counter
                    voting_phase_occurred = True  # Set the flag to indicate voting has occurred
                else:
                    voting_phase_occurred = False  # Reset the flag if not enough ingredients

            # Draw everything (even when paused)
            self.screen.fill((0, 0, 0))
            self.draw()
            self.draw_buttons()  # Make sure buttons are drawn
            self.draw_sidebar()
            pygame.display.flip()

            # Cap the frame rate
            clock.tick(30)

    def update(self):
        """Main update loop."""
        for agent in self.agents:
            # Update agent position
            target_reached = agent.update_position(self)
            
            # If target reached and no new target set, need new plan
            if target_reached and agent.needs_new_target():
                self.choose_new_plan(agent)

    def choose_new_plan(self, agent):
        """Choose and set up a new plan for the agent."""
        if agent.plan is None or agent.plan.type == PlanType.STAY:
            # Choose a random room to go to
            available_rooms = list(set(self.rooms.keys()) - {agent.current_room})
            if available_rooms:
                target_room = random.choice(available_rooms)
                target_pos = random.choice(list(self.rooms[target_room].cells))
                agent.set_target(target_pos[0], target_pos[1], self)
                agent.plan = Plan(
                    type=PlanType.GOTO_ROOM,
                    target=target_room,
                    visited_rooms={agent.current_room}
                )
            else:
                # If no rooms are available, go to the cauldron
                print(f"No rooms available for agent {agent.id}, going to cauldron")
                agent.set_target(self.cauldron.x, self.cauldron.y, self)
                agent.plan = Plan(
                    type=PlanType.GO_TO_CAULDRON,
                    target="cauldron"
                )

    def get_room_at_position(self, x: float, y: float, current_room: Optional[str] = None) -> Optional[str]:
        cell_x, cell_y = int(x), int(y)
        
        # If we have a current room, first check if we're at a door
        if current_room:
            # Get all doors connected to current room
            doors = self.door_manager.get_doors_for_room(current_room)
            for door in doors:
                door_pos = self.door_manager.get_door_position(door.room1, door.room2)
                if door_pos and (cell_x, cell_y) == door_pos:
                    # print(f"  Found door position between {door.room1} and {door.room2}")
                    # Get the other room
                    other_room = door.room2 if current_room == door.room1 else door.room1
                    
                    # When exactly at door position, allow transition to next room in path
                    if door.connects_rooms(current_room, other_room):
                        return other_room
                    
        # If not at a door, stay in current room if position is valid
        if current_room and (cell_x, cell_y) in self.rooms[current_room].cells:
            return current_room
            
        # If no current room or position not in current room, find containing room
        for room_id, room in self.rooms.items():
            if (cell_x, cell_y) in room.cells:
                # print(f"  Position found in room: {room_id}")
                return room_id
        
        print("  ERROR: Position not found in any room!")
        return None
    def find_path_through_doors(self, agent: Agent, target_x: int, target_y: int) -> List[Tuple[float, float]]:
        """Find a path from agent's position to target that goes through doors."""

        target_room = self.get_room_at_position(target_x, target_y)
        # print(f"  Target room: {target_room}")
        
        if not target_room:
            print("  ERROR: No target room found!")
            return []
        
        if agent.current_room == target_room:
            # print("  Same room - using direct path")
            if (agent.x, agent.y) == (target_x, target_y):
                return []
            return [(target_x, target_y)]
        
        room_path = self.find_path_to_room(agent.current_room, target_room)
        # print(f"  Room path: {room_path}")
        
        if not room_path:
            print("  ERROR: No room path found!")
            return []
        
        waypoints = []
        for i in range(len(room_path) - 1):
            current_room = room_path[i]
            next_room = room_path[i + 1]
            door_pos = self.door_manager.get_door_position(current_room, next_room)
            if door_pos:
                waypoints.append(door_pos)
                # print(f"  Added door waypoint: {door_pos} between {current_room}->{next_room}")
            # else:
                # print(f"  ERROR: No door found between {current_room} and {next_room}")
        
        waypoints.append((target_x, target_y))
        # print(f"  Final waypoints: {waypoints}")
        return waypoints
    
    def draw_agent_conversation(self, agent):
        font = pygame.font.SysFont(None, 24)
        x_offset = 10
        y_offset = 10

        panel_width = 300
        panel_height = 200
        panel_rect = pygame.Rect(x_offset, y_offset, panel_width, panel_height)
        
        # Draw a dark background panel for readability
        pygame.draw.rect(self.screen, (50, 50, 50), panel_rect)
        # Draw a white border
        pygame.draw.rect(self.screen, (255, 255, 255), panel_rect, 2)

        # Small margin inside the panel
        text_x = x_offset + 10
        text_y = y_offset + 10

        header_text = font.render(f"Agent {agent.id}'s Conversation:", True, (255, 255, 255))
        self.screen.blit(header_text, (text_x, text_y))
        text_y += 30

        # Render each line of the agent's memory
        for line in agent.memory:
            line_text = font.render(line, True, (200, 200, 200))
            self.screen.blit(line_text, (text_x, text_y))
            text_y += 30
            # Stop if we run out of space (optional)
            if text_y > y_offset + panel_height - 30:
                break
            
    def draw_sidebar(self):
        """Draw a sidebar to display conversation history."""
        sidebar_width = 300  # Width of the sidebar
        sidebar_x = self.width * self.CELL_SIZE  # Sidebar starts after the game grid
        sidebar_y = 0
        sidebar_height = self.height * self.CELL_SIZE  # Match the game grid height

        # Draw the sidebar background
        pygame.draw.rect(
            self.screen,
            (50, 50, 50),  # Dark gray
            (sidebar_x, sidebar_y, sidebar_width, sidebar_height),
        )

        # If an agent is selected, draw their conversation history
        if self.selected_agent:
            font = pygame.font.Font(None, 24)
            y_offset = 20  # Start drawing text with some margin
            x_offset = sidebar_x + 10  # Add padding inside the sidebar

            # Draw header
            header_text = font.render(f"Agent {self.selected_agent.id}'s History:", True, (255, 255, 255))  # White text
            self.screen.blit(header_text, (x_offset, y_offset))
            y_offset += 40  # Add space after the header

            # Draw the last 5 lines of conversation with wrapping
            history = self.selected_agent.memory[-5:]  # Show the last 5 lines
            for line in history:
                wrapped_lines = self.wrap_text(line, font, sidebar_width - 20)  # Wrap text to fit the sidebar
                for wrapped_line in wrapped_lines:
                    text = font.render(wrapped_line, True, (200, 200, 200))  # Light gray text
                    self.screen.blit(text, (x_offset, y_offset))
                    y_offset += 30  # Add spacing between lines
                    if y_offset > sidebar_height - 30:
                        break  # Stop drawing if the text goes out of bounds

    @staticmethod
    def wrap_text(text, font, max_width):
        """Split text into lines that fit within a given width."""
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            # Render the current line to check its width
            if font.size(' '.join(current_line))[0] > max_width:
                # If too wide, remove the last word and finalize the current line
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]

        # Add the last line
        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def draw_cauldron(self):
        cauldron_x = self.cauldron.x * self.CELL_SIZE
        cauldron_y = self.cauldron.y * self.CELL_SIZE
        self.screen.blit(self.textures['cauldron'], (cauldron_x, cauldron_y))
