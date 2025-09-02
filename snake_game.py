#!/usr/bin/env python3
"""
Enhanced Terminal Snake Game
A polished Snake game with improved consistency, smoother controls, and better features.
Use WASD or arrow keys to control the snake.
"""

import random
import time
import sys
import os
import threading
from collections import deque
from enum import Enum

# For cross-platform input handling
try:
    import msvcrt
except ImportError:
    import termios
    import tty
    import select

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class GameState(Enum):
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    QUIT = "quit"

class SnakeGame:
    def __init__(self, width=30, height=20):
        self.width = width
        self.height = height
        self.reset_game()
        
    def reset_game(self):
        """Reset game to initial state"""
        center_x, center_y = self.width // 2, self.height // 2
        self.snake = deque([(center_x, center_y), (center_x - 1, center_y)])
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.food = self.generate_food()
        self.score = 0
        self.state = GameState.PLAYING
        self.moves_without_food = 0
        self.max_moves_without_food = self.width * self.height
        
    def generate_food(self):
        """Generate food at a random position not occupied by the snake"""
        empty_positions = []
        for x in range(self.width):
            for y in range(self.height):
                if (x, y) not in self.snake:
                    empty_positions.append((x, y))
        
        if not empty_positions:
            # Game won (snake fills entire board)
            self.state = GameState.GAME_OVER
            return None
            
        return random.choice(empty_positions)
    
    def is_valid_direction_change(self, new_direction):
        """Check if direction change is valid (not opposite to current direction)"""
        current = self.direction.value
        new = new_direction.value
        # Prevent moving in opposite direction
        return (current[0] + new[0], current[1] + new[1]) != (0, 0)
    
    def change_direction(self, new_direction):
        """Queue next direction change"""
        if self.is_valid_direction_change(new_direction):
            self.next_direction = new_direction
    
    def update(self):
        """Update game state"""
        if self.state != GameState.PLAYING:
            return
            
        # Apply queued direction change
        if self.is_valid_direction_change(self.next_direction):
            self.direction = self.next_direction
        
        # Calculate new head position
        head = self.snake[0]
        dx, dy = self.direction.value
        new_head = (head[0] + dx, head[1] + dy)
        
        # Check wall collision
        if (new_head[0] < 0 or new_head[0] >= self.width or 
            new_head[1] < 0 or new_head[1] >= self.height):
            self.state = GameState.GAME_OVER
            return
        
        # Check self collision
        if new_head in self.snake:
            self.state = GameState.GAME_OVER
            return
        
        # Add new head
        self.snake.appendleft(new_head)
        
        # Check food consumption
        if new_head == self.food:
            self.score += 1
            self.moves_without_food = 0
            self.food = self.generate_food()
            if self.food is None:  # Board is full
                return
        else:
            # Remove tail if no food eaten
            self.snake.pop()
            self.moves_without_food += 1
            
            # Prevent infinite games
            if self.moves_without_food > self.max_moves_without_food:
                self.state = GameState.GAME_OVER
    
    def get_speed(self):
        """Get game speed based on score (gets faster as score increases)"""
        base_speed = 0.2
        speed_increase = min(0.15, self.score * 0.01)
        return max(0.05, base_speed - speed_increase)
    
    def draw(self):
        """Render the game"""
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Create board
        board = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Place snake
        for i, (x, y) in enumerate(self.snake):
            if i == 0:
                # Snake head with direction indicator
                head_chars = {
                    Direction.UP: '▲',
                    Direction.DOWN: '▼',
                    Direction.LEFT: '◄',
                    Direction.RIGHT: '►'
                }
                board[y][x] = head_chars[self.direction]
            else:
                board[y][x] = '█'
        
        # Place food
        if self.food:
            board[self.food[1]][self.food[0]] = '●'
        
        # Print game title
        print("🐍 SNAKE GAME 🐍")
        print()
        
        # Print top border
        print('╔' + '═' * self.width + '╗')
        
        # Print game board
        for row in board:
            print('║' + ''.join(row) + '║')
        
        # Print bottom border
        print('╚' + '═' * self.width + '╝')
        
        # Game info
        print(f'Score: {self.score}   Length: {len(self.snake)}   Speed: {1/self.get_speed():.1f}')
        
        # Controls and status
        if self.state == GameState.PLAYING:
            print('Controls: WASD/Arrow Keys = Move, P = Pause, Q = Quit')
        elif self.state == GameState.PAUSED:
            print('⏸️  PAUSED - Press P to resume, Q to quit')
        elif self.state == GameState.GAME_OVER:
            if len(self.snake) == self.width * self.height:
                print('🎉 CONGRATULATIONS! YOU WON! 🎉')
            else:
                print('💀 GAME OVER 💀')
            print('Press R to restart, Q to quit')

class InputHandler:
    """Cross-platform keyboard input handler"""
    
    def __init__(self):
        self.is_windows = os.name == 'nt'
        self.key_queue = deque()
        
        if not self.is_windows:
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.cbreak(sys.stdin.fileno())
    
    def get_key_windows(self):
        """Get key on Windows"""
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\xe0':  # Arrow key prefix
                key = msvcrt.getch()
                arrow_keys = {
                    b'H': 'UP',
                    b'P': 'DOWN', 
                    b'K': 'LEFT',
                    b'M': 'RIGHT'
                }
                return arrow_keys.get(key, None)
            else:
                return key.decode('utf-8', errors='ignore').upper()
        return None
    
    def get_key_unix(self):
        """Get key on Unix-like systems"""
        if sys.stdin in select.select([sys.stdin], [], [], 0):
            key = sys.stdin.read(1)
            if key == '\x1b':  # Escape sequence
                if sys.stdin in select.select([sys.stdin], [], [], 0.1):
                    seq = sys.stdin.read(2)
                    if seq == '[A':
                        return 'UP'
                    elif seq == '[B':
                        return 'DOWN'
                    elif seq == '[D':
                        return 'LEFT'
                    elif seq == '[C':
                        return 'RIGHT'
                return 'ESC'
            else:
                return key.upper()
        return None
    
    def get_key(self):
        """Get a single keypress"""
        if self.is_windows:
            return self.get_key_windows()
        else:
            return self.get_key_unix()
    
    def cleanup(self):
        """Restore terminal settings"""
        if not self.is_windows:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

def main():
    """Main game loop with consistent timing"""
    game = SnakeGame()
    input_handler = InputHandler()
    
    print("🐍 Welcome to Enhanced Snake Game! 🐍")
    print("Loading...")
    time.sleep(1)
    
    try:
        last_update = time.time()
        
        while game.state != GameState.QUIT:
            current_time = time.time()
            
            # Handle input
            key = input_handler.get_key()
            if key:
                if key.upper() == 'Q':
                    game.state = GameState.QUIT
                    break
                elif key.upper() == 'P' and game.state in [GameState.PLAYING, GameState.PAUSED]:
                    game.state = GameState.PAUSED if game.state == GameState.PLAYING else GameState.PLAYING
                elif key.upper() == 'R' and game.state == GameState.GAME_OVER:
                    game.reset_game()
                elif game.state == GameState.PLAYING:
                    # Direction controls
                    direction_map = {
                        'W': Direction.UP, 'UP': Direction.UP,
                        'S': Direction.DOWN, 'DOWN': Direction.DOWN,
                        'A': Direction.LEFT, 'LEFT': Direction.LEFT,
                        'D': Direction.RIGHT, 'RIGHT': Direction.RIGHT
                    }
                    if key in direction_map:
                        game.change_direction(direction_map[key])
            
            # Update game at consistent intervals
            if current_time - last_update >= game.get_speed():
                game.update()
                last_update = current_time
            
            # Render
            game.draw()
            
            # Small sleep to prevent excessive CPU usage
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user.")
    finally:
        input_handler.cleanup()
        print(f"\n🎮 Final Score: {game.score}")
        print("Thanks for playing Enhanced Snake!")

if __name__ == "__main__":
    main()