#!/usr/bin/env python3
"""
Enhanced Terminal Snake Game with AI Player
A polished Snake game with improved consistency, smoother controls, AI player with A* pathfinding, and better features.
Use WASD or arrow keys to control the snake, or watch the AI play.
"""

import random
import time
import sys
import os
import heapq
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

def play_human_mode(game, input_handler):
    """Human player game loop with enhanced timing"""
    last_update = time.time()
    
    while game.state not in [GameState.GAME_OVER, GameState.QUIT]:
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

def play_ai_mode(game, input_handler):
    """AI player game loop with enhanced timing"""
    ai_player = AIPlayer(game)
    last_update = time.time()
    
    while game.state not in [GameState.GAME_OVER, GameState.QUIT]:
        current_time = time.time()
        
        # Handle user input (quit or pause)
        key = input_handler.get_key()
        if key:
            if key.upper() == 'Q':
                game.state = GameState.QUIT
                break
            elif key.upper() == 'P' and game.state in [GameState.PLAYING, GameState.PAUSED]:
                game.state = GameState.PAUSED if game.state == GameState.PLAYING else GameState.PLAYING
            elif key.upper() == 'R' and game.state == GameState.GAME_OVER:
                game.reset_game()
        
        # AI makes decision when playing
        if game.state == GameState.PLAYING:
            ai_direction = ai_player.get_next_direction()
            if ai_direction:
                # Convert tuple direction to Direction enum
                direction_map = {
                    (0, -1): Direction.UP,
                    (0, 1): Direction.DOWN,
                    (-1, 0): Direction.LEFT,
                    (1, 0): Direction.RIGHT
                }
                if ai_direction in direction_map:
                    game.change_direction(direction_map[ai_direction])
        
        # Update game at consistent intervals (slightly faster for AI demo)
        ai_speed = max(0.05, game.get_speed() * 0.8)  # 20% faster than human speed
        if current_time - last_update >= ai_speed:
            game.update()
            last_update = current_time
        
        # Render with AI-specific info
        game.draw()
        if game.state == GameState.PLAYING:
            print('🤖 AI Mode - Press P to pause, Q to quit')
        elif game.state == GameState.PAUSED:
            print('🤖 AI PAUSED - Press P to resume, Q to quit')
        
        # Small sleep to prevent excessive CPU usage
        time.sleep(0.01)

def main():
    """Main game entry point with mode selection and enhanced features"""
    print("🐍 Enhanced Snake Game with AI! 🐍")
    print("Choose your mode:")
    print("1. Human Player (Enhanced controls with pause/resume)")
    print("2. AI Player (Watch the AI play with A* pathfinding)")
    print("3. Quit")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            # Human mode
            print("\n🎮 Starting Human Mode...")
            time.sleep(0.5)
            
            game = SnakeGame()
            input_handler = InputHandler()
            
            try:
                play_human_mode(game, input_handler)
                
            except KeyboardInterrupt:
                print("\n\nGame interrupted by user.")
            finally:
                input_handler.cleanup()
                print(f"\n🎮 Final Score: {game.score}")
                print("Returning to menu...\n")
                
        elif choice == '2':
            # AI mode
            print("\n🤖 Starting AI Mode...")
            time.sleep(0.5)
            
            game = SnakeGame()
            input_handler = InputHandler()
            
            try:
                play_ai_mode(game, input_handler)
                
            except KeyboardInterrupt:
                print("\n\nGame interrupted by user.")
            finally:
                input_handler.cleanup()
                print(f"\n🤖 AI Final Score: {game.score}")
                print("Returning to menu...\n")
                
        elif choice == '3':
            print("Thanks for playing Enhanced Snake Game with AI! 🐍🤖")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()