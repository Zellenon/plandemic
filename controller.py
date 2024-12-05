import pygame
import random
from enum import Enum


class GameEvent(Enum):
    TOKEN_EXECUTE_PLAN = "token, execute plan"
    # Add more event types here as needed


class GameController:
    def __init__(self, board_game, tick_rate_ms=600):
        self.board_game = board_game
        self.tick_rate_ms = tick_rate_ms
        self.last_tick = 0

    def handle_events(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_tick >= self.tick_rate_ms:
            self.last_tick = current_time
            self.tick_rate_ms = random.randint(250, 750)
            self.send_event(GameEvent.TOKEN_EXECUTE_PLAN)

    def send_event(self, event_type: GameEvent, **kwargs):
        if event_type == GameEvent.TOKEN_EXECUTE_PLAN:
            token = random.choice(self.board_game.tokens)
            self.board_game.execute_plan(token)
