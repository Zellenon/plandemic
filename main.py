import pygame
import math
import random

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Union
from enum import Enum
from collections import deque
from board import BoardGame



# Example usage
if __name__ == "__main__":
    game = BoardGame("board.txt", "doors.txt", num_agents=5)
    game.run()
