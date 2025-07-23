"""
Scribbo Game Engine
Core game logic and utilities for the Scribbo drawing game.
"""

import math
from typing import List, Tuple, Optional, Dict
from protocol import DrawingPoint, MessageProtocol

class GameEngine:
    """Core game engine for Scribbo game logic"""
    
    def __init__(self):
        self.board_size = MessageProtocol.BOARD_SIZE
        self.min_coverage = MessageProtocol.MIN_COVERAGE_PERCENTAGE
    
    def calculate_coverage_percentage(self, drawing_points: List[DrawingPoint], 
                                    square_size: float = 1.0) -> float:
        """
        Calculate the coverage percentage of a square based on drawing points.
        This is a simplified algorithm - in a real implementation with graphics,
        you would use actual pixel coverage calculation.
        """
        if not drawing_points:
            return 0.0
        
        # Create a simple grid to estimate coverage
        grid_resolution = 20  # 20x20 grid for coverage estimation
        grid = [[False for _ in range(grid_resolution)] for _ in range(grid_resolution)]
        
        # Mark grid cells that are covered by drawing points
        for point in drawing_points:
            grid_x = int(point.x * grid_resolution)
            grid_y = int(point.y * grid_resolution)
            
            # Ensure coordinates are within bounds
            grid_x = max(0, min(grid_resolution - 1, grid_x))
            grid_y = max(0, min(grid_resolution - 1, grid_y))
            
            # Mark this cell and adjacent cells (simulating pen thickness)
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    nx, ny = grid_x + dx, grid_y + dy
                    if 0 <= nx < grid_resolution and 0 <= ny < grid_resolution:
                        grid[ny][nx] = True
        
        # Calculate coverage percentage
        covered_cells = sum(sum(row) for row in grid)
        total_cells = grid_resolution * grid_resolution
        
        return (covered_cells / total_cells) * 100.0
    
    def is_valid_move(self, row: int, col: int, board: List[List[Optional[int]]], 
                     active_squares: Dict[Tuple[int, int], int], 
                     player_id: int) -> Tuple[bool, str]:
        """
        Check if a move is valid for the given player.
        Returns (is_valid, error_message)
        """
        # Check coordinates
        if not MessageProtocol.validate_coordinates(row, col):
            return False, "Invalid square coordinates"
        
        # Check if square is already owned
        if board[row][col] is not None:
            return False, "Square is already owned"
        
        # Check if square is currently being drawn on by another player
        if (row, col) in active_squares:
            current_player = active_squares[(row, col)]
            if current_player != player_id:
                return False, "Square is currently being drawn on by another player"
        
        return True, ""
    
    def calculate_winner(self, players: Dict[int, Dict]) -> Tuple[Optional[int], List[int], int]:
        """
        Calculate the winner(s) of the game.
        Returns (single_winner_id, all_winners_list, max_score)
        """
        if not players:
            return None, [], 0
        
        # Find maximum score
        max_score = max(player['score'] for player in players.values())
        
        # Find all players with maximum score
        winners = [pid for pid, player in players.items() if player['score'] == max_score]
        
        # Return single winner if no tie, otherwise None for single winner
        single_winner = winners[0] if len(winners) == 1 else None
        
        return single_winner, winners, max_score
    
    def is_game_complete(self, board: List[List[Optional[int]]]) -> bool:
        """Check if all squares on the board have been captured"""
        for row in board:
            for cell in row:
                if cell is None:
                    return False
        return True
    
    def get_board_statistics(self, board: List[List[Optional[int]]], 
                           players: Dict[int, Dict]) -> Dict:
        """Get statistics about the current board state"""
        stats = {
            'total_squares': self.board_size * self.board_size,
            'captured_squares': 0,
            'empty_squares': 0,
            'player_counts': {}
        }
        
        # Initialize player counts
        for player_id in players:
            stats['player_counts'][player_id] = 0
        
        # Count squares
        for row in board:
            for cell in row:
                if cell is None:
                    stats['empty_squares'] += 1
                else:
                    stats['captured_squares'] += 1
                    if cell in stats['player_counts']:
                        stats['player_counts'][cell] += 1
        
        # Calculate percentages
        total = stats['total_squares']
        stats['completion_percentage'] = (stats['captured_squares'] / total) * 100.0
        
        for player_id in stats['player_counts']:
            count = stats['player_counts'][player_id]
            stats['player_counts'][player_id] = {
                'count': count,
                'percentage': (count / total) * 100.0
            }
        
        return stats
    
    def simulate_drawing_path(self, start_x: float, start_y: float, 
                            end_x: float, end_y: float, 
                            num_points: int = 10) -> List[DrawingPoint]:
        """
        Simulate a drawing path between two points.
        Useful for testing or creating demo drawing data.
        """
        import time
        
        points = []
        current_time = time.time()
        
        for i in range(num_points):
            t = i / (num_points - 1) if num_points > 1 else 0
            
            # Linear interpolation
            x = start_x + t * (end_x - start_x)
            y = start_y + t * (end_y - start_y)
            
            # Add some randomness to make it more realistic
            import random
            x += (random.random() - 0.5) * 0.05  # Small random offset
            y += (random.random() - 0.5) * 0.05
            
            # Clamp to square bounds
            x = max(0.0, min(1.0, x))
            y = max(0.0, min(1.0, y))
            
            points.append(DrawingPoint(x, y, current_time + i * 0.1))
        
        return points
    
    def create_test_drawing(self, pattern: str = "diagonal") -> List[DrawingPoint]:
        """
        Create test drawing patterns for simulation purposes.
        Patterns: "diagonal", "circle", "square", "cross", "random"
        """
        import time
        import random
        
        points = []
        current_time = time.time()
        
        if pattern == "diagonal":
            # Draw diagonal line
            for i in range(20):
                t = i / 19
                points.append(DrawingPoint(t, t, current_time + i * 0.05))
        
        elif pattern == "circle":
            # Draw circle
            center_x, center_y = 0.5, 0.5
            radius = 0.3
            for i in range(30):
                angle = (i / 30) * 2 * math.pi
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                points.append(DrawingPoint(x, y, current_time + i * 0.033))
        
        elif pattern == "square":
            # Draw square outline
            corners = [(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8), (0.2, 0.2)]
            for i, (x, y) in enumerate(corners):
                points.append(DrawingPoint(x, y, current_time + i * 0.1))
        
        elif pattern == "cross":
            # Draw cross pattern
            # Horizontal line
            for i in range(10):
                t = i / 9
                points.append(DrawingPoint(t, 0.5, current_time + i * 0.05))
            # Vertical line
            for i in range(10):
                t = i / 9
                points.append(DrawingPoint(0.5, t, current_time + (10 + i) * 0.05))
        
        elif pattern == "random":
            # Random scribble
            for i in range(25):
                x = random.random()
                y = random.random()
                points.append(DrawingPoint(x, y, current_time + i * 0.04))
        
        return points
    
    def estimate_drawing_time(self, drawing_points: List[DrawingPoint]) -> float:
        """Estimate the time it took to create a drawing"""
        if len(drawing_points) < 2:
            return 0.0
        
        return drawing_points[-1].timestamp - drawing_points[0].timestamp
    
    def validate_drawing_points(self, drawing_points: List[DrawingPoint]) -> bool:
        """Validate that drawing points are within valid ranges"""
        for point in drawing_points:
            if not (0.0 <= point.x <= 1.0) or not (0.0 <= point.y <= 1.0):
                return False
            if point.timestamp < 0:
                return False
        
        return True

class GameValidator:
    """Validates game state and moves"""
    
    @staticmethod
    def validate_board_state(board: List[List[Optional[int]]]) -> bool:
        """Validate that the board state is consistent"""
        if len(board) != MessageProtocol.BOARD_SIZE:
            return False
        
        for row in board:
            if len(row) != MessageProtocol.BOARD_SIZE:
                return False
            
            for cell in row:
                if cell is not None and not isinstance(cell, int):
                    return False
        
        return True
    
    @staticmethod
    def validate_player_data(players: Dict[int, Dict]) -> bool:
        """Validate player data structure"""
        for player_id, player_data in players.items():
            if not isinstance(player_id, int):
                return False
            
            required_fields = ['name', 'color', 'score']
            for field in required_fields:
                if field not in player_data:
                    return False
            
            if not isinstance(player_data['score'], int) or player_data['score'] < 0:
                return False
        
        return True
    
    @staticmethod
    def validate_active_squares(active_squares: Dict, players: Dict[int, Dict]) -> bool:
        """Validate active squares data"""
        valid_player_ids = set(players.keys())
        
        for square_key, player_id in active_squares.items():
            # Validate key format
            if not isinstance(square_key, tuple) or len(square_key) != 2:
                return False
            
            row, col = square_key
            if not MessageProtocol.validate_coordinates(row, col):
                return False
            
            # Validate player ID
            if player_id not in valid_player_ids:
                return False
        
        return True
