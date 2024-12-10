import pygame
import random
from enum import Enum


class GameEvent(Enum):
    AGENT_EXECUTE_PLAN = "agent, execute plan"
    # Add more event types here as needed


class GameController:
    def __init__(self, board_game, tick_rate_ms=600):
        self.board_game = board_game
        self.tick_rate_ms = tick_rate_ms
        self.last_tick = 0
        self.turn = 0  # Add a turn counter

    def handle_events(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_tick >= self.tick_rate_ms:
            self.last_tick = current_time
            self.tick_rate_ms = random.randint(250, 750)
            self.send_event(GameEvent.AGENT_EXECUTE_PLAN)
            self.increment_turn()  # Increment the turn after handling events

    def increment_turn(self):
        """Increment the turn counter."""
        self.turn += 1

    def send_event(self, event_type: GameEvent, **kwargs):
        if event_type == GameEvent.AGENT_EXECUTE_PLAN:
            agent = random.choice(self.board_game.agents)
            self.board_game.execute_plan(agent)

