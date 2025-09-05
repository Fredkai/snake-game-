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
import heapq
from collections import deque

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
        
        if self.game_over:
            print('\n🎮 GAME OVER! 🎮')
            print('Press any key to exit...')

class AIPlayer:
    """AI player that uses A* pathfinding to play Snake automatically"""
    
    def __init__(self, game):
        self.game = game
        
    def get_neighbors(self, pos):
        """Get valid neighboring positions"""
        x, y = pos
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < self.game.width and 0 <= ny < self.game.height and 
                (nx, ny) not in self.game.snake):
                neighbors.append((nx, ny))
        return neighbors
    
    def manhattan_distance(self, pos1, pos2):
        """Calculate Manhattan distance between two positions"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def a_star_pathfind(self, start, goal):
        """A* pathfinding algorithm to find optimal path to food"""
        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.manhattan_distance(start, goal)}
        
        while open_set:
            current = heapq.heappop(open_set)[1]
            
            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]  # Return reversed path
            
            for neighbor in self.get_neighbors(current):
                tentative_g_score = g_score[current] + 1
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.manhattan_distance(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return []  # No path found
    
    def get_safe_direction(self):
        """Find a safe direction when no path to food exists"""
        head = self.game.snake[0]
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # Up, Down, Left, Right
        
        # Try each direction and pick the one that gives most space
        best_direction = None
        max_space = -1
        
        for direction in directions:
            new_head = (head[0] + direction[0], head[1] + direction[1])
            
            # Check if this direction is valid
            if (0 <= new_head[0] < self.game.width and 
                0 <= new_head[1] < self.game.height and 
                new_head not in self.game.snake):
                
                # Count accessible spaces using BFS
                accessible_spaces = self.count_accessible_spaces(new_head)
                if accessible_spaces > max_space:
                    max_space = accessible_spaces
                    best_direction = direction
        
        return best_direction
    
    def count_accessible_spaces(self, start_pos):
        """Count how many spaces are accessible from a given position"""
        visited = set()
        queue = deque([start_pos])
        visited.add(start_pos)
        
        while queue:
            pos = queue.popleft()
            for neighbor in self.get_neighbors(pos):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return len(visited)
    
    def get_next_direction(self):
        """Get the next direction for the AI to move"""
        head = self.game.snake[0]
        
        # Try to find path to food
        path = self.a_star_pathfind(head, self.game.food)
        
        if path:
            # Follow the path to food
            next_pos = path[0]
            direction = (next_pos[0] - head[0], next_pos[1] - head[1])
            return direction
        else:
            # No path to food, find safe direction
            return self.get_safe_direction()

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

def play_human_mode(game, input_handler):
    """Human player game loop"""
    while not game.game_over:
        # Draw the game
        game.draw_game()
        print('Controls: WASD or Arrow Keys to move, Q to quit')
        
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

def play_ai_mode(game, input_handler):
    """AI player game loop"""
    ai_player = AIPlayer(game)
    
    while not game.game_over:
        # Draw the game
        game.draw_game()
        print('🤖 AI Mode - Press Q to quit, any other key to pause')
        
        # Check for user input (quit or pause)
        key = input_handler.get_key()
        if key and key.upper() == 'Q':
            break
        elif key:
            print('Paused. Press any key to continue...')
            input_handler.get_key()
        
        # AI makes decision
        ai_direction = ai_player.get_next_direction()
        if ai_direction:
            game.change_direction(ai_direction)
        
        # Move snake
        game.move_snake()
        
        # AI game speed (slightly faster for demo)
        time.sleep(0.08)

def main():
    """Main game entry point with mode selection"""
    print("🐍 Welcome to Snake Game! 🐍")
    print("Choose your mode:")
    print("1. Human Player (WASD/Arrow Keys)")
    print("2. AI Player (Watch the AI play)")
    print("3. Quit")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            # Human mode
            game = SnakeGame()
            input_handler = InputHandler()
            
            try:
                play_human_mode(game, input_handler)
                
                # Final screen if game over
                if game.game_over:
                    game.draw_game()
                    print('Press any key to return to menu...')
                    input_handler.get_key()
                    
            except KeyboardInterrupt:
                print("\n\nGame interrupted by user.")
            finally:
                input_handler.cleanup()
                print(f"\nFinal Score: {game.score}")
                print("Returning to menu...\n")
                
        elif choice == '2':
            # AI mode
            game = SnakeGame()
            input_handler = InputHandler()
            
            try:
                play_ai_mode(game, input_handler)
                
                # Final screen if game over
                if game.game_over:
                    game.draw_game()
                    print('AI finished! Press any key to return to menu...')
                    input_handler.get_key()
                    
            except KeyboardInterrupt:
                print("\n\nGame interrupted by user.")
            finally:
                input_handler.cleanup()
                print(f"\n🤖 AI Final Score: {game.score}")
                print("Returning to menu...\n")
                
        elif choice == '3':
            print("Thanks for playing Snake Game! 🐍")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
