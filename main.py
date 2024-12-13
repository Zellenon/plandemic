import asyncio
import pygame
from board import BoardGame

# Example usage
if __name__ == "__main__":
    # Initialize Pygame
    pygame.init()
    pygame.mixer.init()  # Initialize the mixer for audio
    pygame.mixer.music.set_volume(0.5)

    # Load the music file
    music_file_path = "assets/soundtrack/Mystical Elixirs.mp3"
    pygame.mixer.music.load(music_file_path)

    # Play the music
    pygame.mixer.music.play(-1)  # Loop indefinitely

    game = BoardGame("board.txt", "doors.txt", num_agents=6)
    asyncio.run(game.run())

    # Stop the music before quitting
    pygame.mixer.music.stop()
    pygame.quit()

