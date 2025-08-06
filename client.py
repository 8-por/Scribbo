"""
Scribbo Game Client
Connects to the Scribbo server and handles user interaction for the drawing game.
"""

import socket
import threading
import json
import queue
import time
import uuid
from typing import Dict, List, Optional, Tuple
from utils import send_message_frame, recv_message_frame

class ScribboClient:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.player_id = None
        self.player_color = None
        self.game_state = None
        self.drawing_active = False
        self.current_square = None
        self.drawing_data = []
        self.receive_thread = None

        # Message handling
        self.response_queue = queue.Queue()
        self.pending_requests = {}  # request_id -> (message, timestamp)
        self.lock = threading.Lock()
        self.request_timeout = 10.0  # seconds
        
    def connect_to_server(self, host='localhost', port=12345, player_name='Player') -> bool:
        """Connect to the Scribbo server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.connected = True
            
            print(f"Connected to server at {host}:{port}")
            
            # Start receiving messages in a separate thread
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            # Send join request
            join_message = {
                'type': 'join',
                'name': player_name
            }
            
            response = self.send_message_and_wait_response(join_message)
            
            if response and response.get('type') == 'join_success':
                self.player_id = response.get('player_id')
                self.player_color = response.get('color')
                self.game_state = response.get('game_state', {})
                
                print(f"Successfully joined as Player {self.player_id} with color {self.player_color}")
                return True
            else:
                error_msg = response.get('message', 'Unknown error') if response else 'No response'
                print(f"Failed to join game: {error_msg}")
                self.disconnect()
                return False
                
        except Exception as e:
            print(f"Error connecting to server: {e}")
            self.disconnect()
            return False
    
    def send_message(self, message: dict) -> bool:
        """Send a message to the server using proper framing"""
        if not self.connected or not self.socket:
            return False
    
        try:
            # Set timeout for sending
            self.socket.settimeout(10.0)
            send_message_frame(self.socket, message)  # ✅ Use the framed version
            return True
        except socket.timeout:
            print("Timeout sending message to server")
            self.disconnect()
            return False
        except ConnectionResetError:
            print("Connection reset by the server")
            self.disconnect()
            return False
        except Exception as e:
            print(f"Error sending message: {e}")
            self.disconnect()
            return False

    
    def send_message_and_wait_response(self, message: dict, timeout=5.0) -> Optional[dict]:
        """Send a message and wait for a response with proper request ID correlation"""
        if not self.connected:
            return None
        
        # Generate unique request ID for correlation
        request_id = str(uuid.uuid4())
        message['request_id'] = request_id
        
        # Track this request
        with self.lock:
            self.pending_requests[request_id] = (message, time.time())
        
        # Send the message
        if not self.send_message(message):
            with self.lock:
                if request_id in self.pending_requests:
                    del self.pending_requests[request_id]
            return None
        
        # Wait for response
        if timeout is None:
            timeout = self.request_timeout
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.lock:
                # Check if we have a response for this request
                if request_id not in self.pending_requests:
                    # Request was completed
                    break
                
                # Clean up old pending requests
                current_time = time.time()
                expired_requests = [
                    req_id for req_id, (_, timestamp) in self.pending_requests.items()
                    if current_time - timestamp > self.request_timeout
                ]
                for req_id in expired_requests:
                    del self.pending_requests[req_id]
            
            time.sleep(0.1)  # Small delay to prevent busy waiting
        
        # Check if request timed out
        with self.lock:
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
                print(f"Timeout waiting for response to message type: {message.get('type', 'unknown')}")
                return None
        
        # Response was received and handled - get it from the queue
        try:
            response = self.response_queue.get_nowait()
            return response
        except queue.Empty:
            return {'type': 'success', 'request_id': request_id}
    
    def receive_messages(self):
        """Receive messages from server in a separate thread"""
        while self.connected and self.socket:
            try:
                self.socket.settimeout(5.0)
                message = recv_message_frame(self.socket)
                if not message:
                    print("Server closed connection")
                    break
                self.handle_incoming_message(message)
            except socket.timeout:
                continue
            except ConnectionResetError:
                print("Connection reset by the server")
                break
            except Exception as e:
                if self.connected:
                    print(f"Error receiving message: {e}")
                break

        self.disconnect()
    
    def handle_incoming_message(self, message: dict):
        """Handle incoming message with proper request ID correlation"""
        msg_type = message.get('type')
        request_id = message.get('request_id')
        
        with self.lock:
            # Check if this is a response to a pending request
            if request_id and request_id in self.pending_requests:
                # This is a response to a specific request
                del self.pending_requests[request_id]
                self.response_queue.put(message)
                return
            
            # This is a broadcast message or unsolicited response
            self.handle_broadcast_message(message)
    
    def handle_broadcast_message(self, message: dict):
        """Handle broadcast messages (player_joined, player_left, etc.)"""
        msg_type = message.get('type')
        
        if msg_type == 'player_joined':
            self.handle_player_joined(message)
        elif msg_type == 'player_left':
            self.handle_player_left(message)
        elif msg_type == 'square_locked':
            self.handle_square_locked(message)
        elif msg_type == 'drawing_update':
            self.handle_drawing_update(message)
        elif msg_type == 'square_captured':
            self.handle_square_captured(message)
        elif msg_type == 'square_failed':
            self.handle_square_failed(message)
        elif msg_type == 'game_state':
            self.game_state = message.get('state', {})
        elif msg_type == 'error':
            print(f"Server error: {message.get('message', 'Unknown error')}")
        else:
            print(f"Unknown broadcast message type: {msg_type}")
    
    def handle_player_joined(self, message: dict):
        """Handle notification that a player joined"""
        player_id = message.get('player_id')
        name = message.get('name')
        color = message.get('color')
        total_players = message.get('total_players')
        
        print(f"Player {name} (ID: {player_id}) joined with color {color}. Total players: {total_players}")
    
    def handle_player_left(self, message: dict):
        """Handle notification that a player left"""
        player_id = message.get('player_id')
        name = message.get('name')
        squares_freed = message.get('squares_freed', [])
        
        print(f"Player {name} (ID: {player_id}) left the game")
        if squares_freed:
            print(f"Squares freed: {squares_freed}")
    
    def handle_square_locked(self, message: dict):
        """Handle notification that a square is being drawn on"""
        row = message.get('row')
        col = message.get('col')
        player_id = message.get('player_id')
        
        print(f"Square ({row}, {col}) is now being drawn on by Player {player_id}")
    
    def handle_drawing_update(self, message: dict):
        """Handle real-time drawing updates from other players"""
        row = message.get('row')
        col = message.get('col')
        player_id = message.get('player_id')
        drawing_data = message.get('data', [])
        
        # In a full implementation, this would update the visual representation
        print(f"Drawing update in square ({row}, {col}) by Player {player_id}")
    
    def handle_square_captured(self, message: dict):
        """Handle notification that a square was captured"""
        row = message.get('row')
        col = message.get('col')
        player_id = message.get('player_id')
        coverage = message.get('coverage')
        game_over = message.get('game_over', False)
        
        print(f"Square ({row}, {col}) captured by Player {player_id} with {coverage:.1f}% coverage")
        
        if game_over:
            winner_id = message.get('winner_id')
            final_scores = message.get('final_scores', {})
            
            print("=== GAME OVER ===")
            if winner_id:
                print(f"Winner: Player {winner_id}")
            else:
                print("Game ended in a tie!")
            
            print("Final scores:")
            for pid, score in final_scores.items():
                print(f"  Player {pid}: {score} squares")
    
    def handle_square_failed(self, message: dict):
        """Handle notification that a square capture failed"""
        row = message.get('row')
        col = message.get('col')
        player_id = message.get('player_id')
        coverage = message.get('coverage')
        
        print(f"Player {player_id} failed to capture square ({row}, {col}) with {coverage:.1f}% coverage")
    
    def start_drawing_in_square(self, row: int, col: int) -> bool:
        """Start drawing in a specific square"""
        if not (0 <= row < 8) or not (0 <= col < 8):
            print("Invalid square coordinates")
            return False
        
        if self.drawing_active:
            print("Already drawing in another square")
            return False
        
        message = {
            'type': 'start_drawing',
            'row': row,
            'col': col
        }
        
        response = self.send_message_and_wait_response(message)
        if response and response.get('type') == 'start_drawing_success':
            self.drawing_active = True
            self.current_square = (row, col)
            self.drawing_data = []
            print(f"Started drawing in square ({row}, {col})")
            return True
        else:
            error_msg = response.get('message', 'Unknown error') if response else 'No response'
            print(f"Failed to start drawing: {error_msg}")
            return False
    
    def add_drawing_point(self, x: float, y: float):
        """Add a drawing point (relative coordinates within the square)"""
        if not self.drawing_active or not self.current_square:
            print("Not currently drawing")
            return False
        
        # Add point to drawing data
        self.drawing_data.append({'x': x, 'y': y, 'timestamp': time.time()})
        
        # Send periodic updates to server (every few points to avoid flooding)
        if len(self.drawing_data) % 5 == 0:
            self.send_drawing_update()
        
        return True
    
    def send_drawing_update(self):
        """Send current drawing data to server"""
        if not self.drawing_active or not self.current_square:
            return
        
        row, col = self.current_square
        message = {
            'type': 'drawing_data',
            'row': row,
            'col': col,
            'data': self.drawing_data[-5:]  # Send last 5 points
        }
        
        # This is a fire-and-forget message, no response needed
        self.send_message(message)
    
    def finish_drawing(self, coverage_percentage: float = 0.0) -> bool:
        """Finish drawing in the current square"""
        if not self.drawing_active or not self.current_square:
            print("Not currently drawing")
            return False
        
        row, col = self.current_square
        message = {
            'type': 'finish_drawing',
            'row': row,
            'col': col,
            'coverage': coverage_percentage
        }
        
        response = self.send_message_and_wait_response(message)
        if response and response.get('type') in ['square_captured', 'square_failed']:
            self.drawing_active = False
            self.current_square = None
            self.drawing_data = []
            
            if response.get('type') == 'square_captured':
                print(f"Successfully captured square ({row}, {col}) with {coverage_percentage:.1f}% coverage")
            else:
                print(f"Failed to capture square ({row}, {col}) with {coverage_percentage:.1f}% coverage")
            
            return True
        else:
            error_msg = response.get('message', 'Unknown error') if response else 'No response'
            print(f"Failed to finish drawing: {error_msg}")
            return False
    
    def get_game_state(self) -> Optional[dict]:
        """Get current game state from server"""
        message = {
            'type': 'get_game_state'
        }
        
        response = self.send_message_and_wait_response(message)
        if response and response.get('type') == 'game_state':
            self.game_state = response.get('state', {})
            return self.game_state
        else:
            error_msg = response.get('message', 'Unknown error') if response else 'No response'
            print(f"Failed to get game state: {error_msg}")
            return None
    
    def print_board_state(self):
        """Print current board state to console"""
        if not self.game_state or 'board' not in self.game_state:
            print("No game state available")
            return
        
        board = self.game_state['board']
        players = self.game_state.get('players', {})
        
        print("\n=== BOARD STATE ===")
        print("   0 1 2 3 4 5 6 7")
        
        for i, row in enumerate(board):
            row_str = f"{i}  "
            for cell in row:
                if cell is None:
                    row_str += ". "
                else:
                    row_str += f"{cell} "
            print(row_str)
        
        print("\n=== PLAYERS ===")
        for pid, player in players.items():
            print(f"Player {pid}: {player['name']} ({player['color']}) - {player['score']} squares")
        
        # Show active squares
        active_squares = self.game_state.get('active_squares', {})
        if active_squares:
            print("\n=== ACTIVE SQUARES ===")
            for square_key, player_id in active_squares.items():
                row, col = map(int, square_key.split(','))
                print(f"Square ({row}, {col}) being drawn on by Player {player_id}")
    
    def disconnect(self):
        """Disconnect from server"""
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        print("Disconnected from server")
    
    def main(self):
        """Main client loop for interactive gameplay"""
        print("\nCommands:")
        print("  draw <row> <col> <coverage>  - Draw in square (coverage 0-100)")
        print("  board                        - Show current board state")
        print("  state                        - Get game state")
        print("  quit                         - Quit the game")
        
        try:
            while self.connected:
                command = input("\n> ").strip().lower()
                
                if command == 'quit':
                    break
                elif command == 'board':
                    self.print_board_state()
                elif command == 'state':
                    self.get_game_state()
                    print(f"Game state: {self.game_state}")
                elif command.startswith('draw '):
                    parts = command.split()
                    if len(parts) >= 4:
                        try:
                            row = int(parts[1])
                            col = int(parts[2])
                            coverage = float(parts[3])
                            
                            if self.start_drawing_in_square(row, col):
                                print(f"Simulating drawing with {coverage}% coverage...")
                                time.sleep(1)  # Simulate drawing time
                                self.finish_drawing(coverage)
                            
                        except ValueError:
                            print("Invalid parameters. Use: draw <row> <col> <coverage>")
                    else:
                        print("Usage: draw <row> <col> <coverage>")
                else:
                    print("Unknown command")
        
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.disconnect()

def main():
    """Main function for command line client interface"""
    import sys
    
    client = ScribboClient()
    
    # Get connection parameters
    host = input("Enter server host (default: localhost): ").strip() or 'localhost'
    port_str = input("Enter server port (default: 12345): ").strip()
    port = 12345
    if port_str:
        try:
            port = int(port_str)
        except ValueError:
            print("Invalid port, using default 12345")
    
    player_name = input("Enter your name: ").strip() or "Player"
    
    # Connect to server
    if not client.connect_to_server(host, port, player_name):
        print("Failed to connect to server")
        return
    
    print("\\nCommands:")
    print("  draw <row> <col> <coverage>  - Draw in square (coverage 0-100)")
    print("  board                        - Show current board state")
    print("  state                        - Get game state")
    print("  quit                         - Quit the game")
    
    try:
        while client.connected:
            command = input("\\n> ").strip().lower()
            
            if command == 'quit':
                break
            elif command == 'board':
                client.print_board_state()
            elif command == 'state':
                client.get_game_state()
                print(f"Game state: {client.game_state}")
            elif command.startswith('draw '):
                parts = command.split()
                if len(parts) >= 4:
                    try:
                        row = int(parts[1])
                        col = int(parts[2])
                        coverage = float(parts[3])
                        
                        if client.start_drawing_in_square(row, col):
                            print(f"Simulating drawing with {coverage}% coverage...")
                            time.sleep(1)  # Simulate drawing time
                            client.finish_drawing(coverage)
                        
                    except ValueError:
                        print("Invalid parameters. Use: draw <row> <col> <coverage>")
                else:
                    print("Usage: draw <row> <col> <coverage>")
            else:
                print("Unknown command")
    
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
