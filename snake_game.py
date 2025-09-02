#!/usr/bin/env python3
"""
Terminal Snake Game
A classic Snake game that runs in the terminal using keyboard controls.
Use WASD or arrow keys to control the snake.
"""

import random
import time
import sys
import os

# For Windows console input
try:
    import msvcrt
except ImportError:
    # For Unix-like systems
    import termios
    import tty

class SnakeGame:
    def __init__(self, width=40, height=20):
        self.width = width
        self.height = height
        self.snake = [(self.width // 2, self.height // 2)]
        self.direction = (1, 0)  # Start moving right
        self.food = self.generate_food()
        self.score = 0
        self.game_over = False
        
    def generate_food(self):
        """Generate food at a random position not occupied by the snake"""
        while True:
            food = (random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            if food not in self.snake:
                return food
    
    def move_snake(self):
        """Move the snake in the current direction"""
        head = self.snake[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])
        
        # Check for wall collision
        if (new_head[0] < 0 or new_head[0] >= self.width or 
            new_head[1] < 0 or new_head[1] >= self.height):
            self.game_over = True
            return
        
        # Check for self collision
        if new_head in self.snake:
            self.game_over = True
            return
        
        self.snake.insert(0, new_head)
        
        # Check if food is eaten
        if new_head == self.food:
            self.score += 1
            self.food = self.generate_food()
        else:
            # Remove tail if no food eaten
            self.snake.pop()
    
    def change_direction(self, new_direction):
        """Change snake direction, preventing reverse movement"""
        # Prevent moving in opposite direction
        if (new_direction[0] * -1, new_direction[1] * -1) != self.direction:
            self.direction = new_direction
    
    def draw_game(self):
        """Draw the game board"""
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Create game board
        board = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Place snake
        for i, (x, y) in enumerate(self.snake):
            if i == 0:
                board[y][x] = '●'  # Head
            else:
                board[y][x] = '○'  # Body
        
        # Place food
        board[self.food[1]][self.food[0]] = '★'
        
        # Print top border
        print('┌' + '─' * self.width + '┐')
        
        # Print game board
        for row in board:
            print('│' + ''.join(row) + '│')
        
        # Print bottom border
        print('└' + '─' * self.width + '┘')
        
        # Print score and controls
        print(f'Score: {self.score}')
        print('Controls: WASD or Arrow Keys to move, Q to quit')
        
        if self.game_over:
            print('\n🎮 GAME OVER! 🎮')
            print('Press any key to exit...')

class InputHandler:
    """Handle keyboard input for different operating systems"""
    
    def __init__(self):
        self.is_windows = os.name == 'nt'
        if not self.is_windows:
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.cbreak(sys.stdin.fileno())
    
    def get_key(self):
        """Get a single keypress"""
        if self.is_windows:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'\xe0':  # Arrow key prefix on Windows
                    key = msvcrt.getch()
                    if key == b'H':  # Up arrow
                        return 'UP'
                    elif key == b'P':  # Down arrow
                        return 'DOWN'
                    elif key == b'K':  # Left arrow
                        return 'LEFT'
                    elif key == b'M':  # Right arrow
                        return 'RIGHT'
                else:
                    return key.decode('utf-8', errors='ignore').upper()
        else:
            # Unix-like systems
            if sys.stdin in select.select([sys.stdin], [], [], 0):
                key = sys.stdin.read(1)
                if key == '\x1b':  # Escape sequence
                    key += sys.stdin.read(2)
                    if key == '\x1b[A':  # Up arrow
                        return 'UP'
                    elif key == '\x1b[B':  # Down arrow
                        return 'DOWN'
                    elif key == '\x1b[D':  # Left arrow
                        return 'LEFT'
                    elif key == '\x1b[C':  # Right arrow
                        return 'RIGHT'
                else:
                    return key.upper()
        return None
    
    def cleanup(self):
        """Restore terminal settings"""
        if not self.is_windows:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

def main():
    """Main game loop"""
    # Initialize game
    game = SnakeGame()
    input_handler = InputHandler()
    
    try:
        while not game.game_over:
            # Draw the game
            game.draw_game()
            
            # Get input
            key = input_handler.get_key()
            
            # Process input
            if key:
                if key.upper() == 'Q':
                    break
                elif key in ['W', 'UP']:
                    game.change_direction((0, -1))
                elif key in ['S', 'DOWN']:
                    game.change_direction((0, 1))
                elif key in ['A', 'LEFT']:
                    game.change_direction((-1, 0))
                elif key in ['D', 'RIGHT']:
                    game.change_direction((1, 0))
            
            # Move snake
            game.move_snake()
            
            # Game speed (adjust as needed)
            time.sleep(0.15)
        
        # Final screen if game over
        if game.game_over:
            game.draw_game()
            
        # Wait for final keypress
        if game.game_over:
            input_handler.get_key()
            
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user.")
    finally:
        input_handler.cleanup()
        print(f"\nFinal Score: {game.score}")
        print("Thanks for playing!")

if __name__ == "__main__":
    main()
