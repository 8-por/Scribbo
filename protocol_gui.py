"""
Scribbo Game Protocol Definition
Defines the message format and protocol for client-server communication.
"""

from enum import Enum
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

class MessageType(Enum):
    # Client to Server
    JOIN = "join"
    START_DRAWING = "start_drawing"
    DRAWING_DATA = "drawing_data"
    FINISH_DRAWING = "finish_drawing"
    GET_GAME_STATE = "get_game_state"
    NEW_PLAYER = "new_player"
    START_DRAWING_GUI = "start_drawing_gui"
    FILLED_DRAWING_GUI = "filled_drawing_gui"
    STOP_DRAWING_GUI = "stop_drawing_gui"
    
    # Server to Client
    JOIN_SUCCESS = "join_success"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    SQUARE_LOCKED = "square_locked"
    DRAWING_UPDATE = "drawing_update"
    SQUARE_CAPTURED = "square_captured"
    SQUARE_FAILED = "square_failed"
    GAME_STATE = "game_state"
    ERROR = "error"
    PLAYER_ADDED = "player_adder"
    ADD_SUCCESS = "add_success"
    PLAYER_LEAVE = "player_leave"
    SQUARE_LOCK_ON = "square_lock_on"
    BOARD_STATE = "board_state"
    WINNER = "winner"

@dataclass
class DrawingPoint:
    """Represents a single drawing point"""
    x: float  # Relative x coordinate within square (0.0 to 1.0)
    y: float  # Relative y coordinate within square (0.0 to 1.0)
    timestamp: float  # Unix timestamp

@dataclass
class Player:
    """Represents a player in the game"""
    id: int
    name: str
    color: str
    score: int

@dataclass
class GameState:
    """Represents the complete game state"""
    board: List[List[Optional[int]]]  # 8x8 grid, None = empty, int = player_id
    active_squares: Dict[str, int]  # "row,col" -> player_id
    players: Dict[int, Player]
    game_started: bool
    game_ended: bool
    winner: Optional[int]

class MessageProtocol:
    """Protocol definition for Scribbo messages"""
    
    # Maximum message size (in bytes)
    MAX_MESSAGE_SIZE = 4096
    
    # Game constants
    BOARD_SIZE = 8
    SQUARE_SIZE = 50
    MIN_COVERAGE_PERCENTAGE = 0.2 # [0, 1]
    MAX_PLAYERS = 4
    
    # Available colors for players
    PLAYER_COLORS = [
        'red', 'blue', 'green', 'yellow'
    ]
    
    @staticmethod
    def create_join_message(player_name: str) -> Dict:
        """Create a join game message"""
        return {
            'type': MessageType.JOIN.value,
            'name': player_name
        }
    
    @staticmethod
    def create_new_player_message(color: str) -> Dict:
        """Create a new player message"""
        return {
            type: MessageType.NEW_PLAYER.value,
            'color': color
        }
    
    @staticmethod
    def create_start_drawing_message(row: int, col: int) -> Dict:
        """Create a start drawing message"""
        return {
            'type': MessageType.START_DRAWING.value,
            'row': row,
            'col': col
        }
    
    @staticmethod
    def create_start_drawing_gui_message(x: int, y: int) -> Dict:
        return {
            'type': MessageType.START_DRAWING_GUI,
            'x': x,
            'y': y
        }
    
    @staticmethod
    def create_filled_drawing_gui_message(x: int, y: int) -> Dict:
        return {
            'type': MessageType.FILLED_DRAWING_GUI,
            'x': x,
            'y': y
        }
    
    @staticmethod
    def create_stop_drawing_gui_message(x: int, y: int) -> Dict:
        return {
            'type': MessageType.STOP_DRAWING_GUI,
            'x': x,
            'y': y
        }


    @staticmethod
    def create_drawing_data_message(row: int, col: int, points: List[DrawingPoint]) -> Dict:
        """Create a drawing data message"""
        return {
            'type': MessageType.DRAWING_DATA.value,
            'row': row,
            'col': col,
            'data': [{'x': p.x, 'y': p.y, 'timestamp': p.timestamp} for p in points]
        }
    
    @staticmethod
    def create_finish_drawing_message(row: int, col: int, coverage: float) -> Dict:
        """Create a finish drawing message"""
        return {
            'type': MessageType.FINISH_DRAWING.value,
            'row': row,
            'col': col,
            'coverage': coverage
        }
    
    @staticmethod
    def create_get_game_state_message() -> Dict:
        """Create a get game state message"""
        return {
            'type': MessageType.GET_GAME_STATE.value
        }
    
    @staticmethod
    def create_join_success_message(player_id: int, color: str, game_state: Dict) -> Dict:
        """Create a join success response"""
        return {
            'type': MessageType.JOIN_SUCCESS.value,
            'player_id': player_id,
            'color': color,
            'game_state': game_state
        }
    
    @staticmethod
    def create_add_success_message(player_id: int, color: str, game_state: Dict) -> Dict:
        """Create a add success response"""
        return {
            'type': MessageType.ADD_SUCCESS.value,
            'player_id': player_id,
            'color': color,
        }

    @staticmethod
    def create_player_joined_message(player_id: int, name: str, color: str, total_players: int) -> Dict:
        """Create a player joined notification"""
        return {
            'type': MessageType.PLAYER_JOINED.value,
            'player_id': player_id,
            'name': name,
            'color': color,
            'total_players': total_players
        }
    def create_player_added_message(player_id: int, color: str, total_players: int) -> Dict:
        """Create a player added notification"""
        return {
            'type': MessageType.PLAYER_ADDED.value,
            'player_id': player_id,
            'color': color,
            'total_players': total_players
        }

    @staticmethod
    def create_player_left_message(player_id: int, name: str, squares_freed: List[tuple]) -> Dict:
        """Create a player left notification"""
        return {
            'type': MessageType.PLAYER_LEFT.value,
            'player_id': player_id,
            'name': name,
            'squares_freed': squares_freed
        }
    
    @staticmethod
    def create_player_leave_message(player_id: int, player_color: str) -> Dict:
        """Create a player left notification used in gui version"""
        return {
            'type': MessageType.PLAYER_LEFT.value,
            'player_id': player_id,
            'player_color': player_color
        }
    
    @staticmethod
    def create_square_locked_message(row: int, col: int, player_id: int) -> Dict:
        """Create a square locked notification"""
        return {
            'type': MessageType.SQUARE_LOCKED.value,
            'row': row,
            'col': col,
            'player_id': player_id
        }
    
    @staticmethod
    def create_square_lock_on_message() -> Dict:
        return {
            'type' : MessageType.SQUARE_LOCK_ON.value
        }
    
    @staticmethod
    def create_drawing_update_message(row: int, col: int, player_id: int, points: List[Dict]) -> Dict:
        """Create a drawing update notification"""
        return {
            'type': MessageType.DRAWING_UPDATE.value,
            'row': row,
            'col': col,
            'player_id': player_id,
            'data': points
        }
    
    @staticmethod
    def create_square_captured_message(row: int, col: int, player_id: int, coverage: float, 
                                     game_over: bool = False, winner_id: Optional[int] = None, 
                                     final_scores: Optional[Dict] = None) -> Dict:
        """Create a square captured notification"""
        message = {
            'type': MessageType.SQUARE_CAPTURED.value,
            'row': row,
            'col': col,
            'player_id': player_id,
            'coverage': coverage,
            'game_over': game_over
        }
        
        if game_over:
            message['winner_id'] = winner_id
            message['final_scores'] = final_scores or {}
        
        return message
    
    @staticmethod
    def create_square_failed_message(row: int, col: int, player_id: int, coverage: float) -> Dict:
        """Create a square capture failed notification"""
        return {
            'type': MessageType.SQUARE_FAILED.value,
            'row': row,
            'col': col,
            'player_id': player_id,
            'coverage': coverage
        }
    
    @staticmethod
    def create_game_state_message(game_state: Dict) -> Dict:
        """Create a game state response"""
        return {
            'type': MessageType.GAME_STATE.value,
            'state': game_state
        }
    
    @staticmethod
    def create_error_message(error_msg: str) -> Dict:
        """Create an error message"""
        return {
            'type': MessageType.ERROR.value,
            'message': error_msg
        }
    
    @staticmethod
    def validate_coordinates(row: int, col: int) -> bool:
        """Validate board coordinates"""
        return 0 <= row < MessageProtocol.BOARD_SIZE and 0 <= col < MessageProtocol.BOARD_SIZE
    
    @staticmethod
    def validate_coverage(coverage: float) -> bool:
        """Validate coverage percentage"""
        return 0.0 <= coverage <= 100.0
    
    @staticmethod
    def is_successful_capture(coverage: float) -> bool:
        """Check if coverage is sufficient for square capture"""
        return coverage >= MessageProtocol.MIN_COVERAGE_PERCENTAGE
    
    @staticmethod
    def create_board_state_message(board_state: List[List[str]]) -> Dict:
        return {
            'type': MessageType.BOARD_STATE.value,
            'board_state': board_state
        }

    @staticmethod
    def create_winner_message(winner_text: str) -> Dict:
        return {
            'type': MessageType.WINNER.value,
            'winner_text': winner_text
        }