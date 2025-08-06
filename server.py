"""
Scribbo Game Server
Manages multiple client connections and game state for the Scribbo drawing game.
"""

import socket
import threading
import json
import time
from typing import Dict, List, Set, Tuple, Optional
from utils import send_message_frame, recv_message_frame

class ScribboServer:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.socket = None
        self.clients: Dict[socket.socket, Dict] = {}  # socket -> client info
        self.game_state = {
            'board': [[None for _ in range(8)] for _ in range(8)],  # None = empty, player_id = owned
            'active_squares': {},  # (row, col) -> player_id (currently being drawn on)
            'players': {},  # player_id -> {color, name, score}
            'game_started': False,
            'game_ended': False,
            'winner': None
        }
        self.player_colors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'pink', 'cyan']
        self.next_player_id = 1
        self.lock = threading.Lock()
        
    def start_server(self):
        """Start the server and listen for connections"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(8)  # Allow up to 8 players
            
            print(f"Scribbo server started on {self.host}:{self.port}")
            print("Waiting for players to connect...")
            
            while True:
                try:
                    client_socket, address = self.socket.accept()
                    print(f"New connection from {address}")
                    
                    # Start a new thread to handle this client
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    print(f"Error accepting connection: {e}")
                    
        except Exception as e:
            print(f"Error starting server: {e}")
        finally:
            self.cleanup()
    
    def handle_client(self, client_socket: socket.socket, address):
        """Handle communication with a connected client"""
        player_id = None
        
        try:
            while True:
                # Receive message from client
                message = recv_message_frame(client_socket)
                if not message:
                    break
                
                try:
                    response = self.process_message(client_socket, message)
                    
                    if response:
                        send_message_frame(client_socket, response)
                        
                except Exception as e:
                    print(f"Error processing message from {address}: {e}")
                    
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            self.disconnect_client(client_socket)
    
    def process_message(self, client_socket: socket.socket, message: dict) -> Optional[dict]:
        """Process incoming message from client and return response"""
        msg_type = message.get('type')
        request_id = message.get('request_id')  # Get request ID for correlation
        
        response = None
        
        if msg_type == 'join':
            response = self.handle_join(client_socket, message)
        elif msg_type == 'start_drawing':
            response = self.handle_start_drawing(client_socket, message)
        elif msg_type == 'drawing_data':
            response = self.handle_drawing_data(client_socket, message)
        elif msg_type == 'finish_drawing':
            response = self.handle_finish_drawing(client_socket, message)
        elif msg_type == 'get_game_state':
            response = self.handle_get_game_state(client_socket)
        else:
            response = {'type': 'error', 'message': f'Unknown message type: {msg_type}'}
        
        # Add request_id to response for correlation
        if response and request_id:
            response['request_id'] = request_id
            
        return response
    
    def handle_join(self, client_socket: socket.socket, message: dict) -> dict:
        """Handle a player joining the game"""
        with self.lock:
            if len(self.clients) >= 8:
                return {'type': 'error', 'message': 'Game is full'}
            
            if self.game_state['game_ended']:
                return {'type': 'error', 'message': 'Game has ended'}
            
            player_name = message.get('name', f'Player{self.next_player_id}')
            player_id = self.next_player_id
            player_color = self.player_colors[len(self.clients) % len(self.player_colors)]
            
            # Add client info
            self.clients[client_socket] = {
                'player_id': player_id,
                'name': player_name,
                'color': player_color,
                'address': client_socket.getpeername()
            }
            
            # Add player to game state
            self.game_state['players'][player_id] = {
                'name': player_name,
                'color': player_color,
                'score': 0
            }
            
            self.next_player_id += 1
            
            print(f"Player {player_name} (ID: {player_id}) joined with color {player_color}")
            
            # Start game if this is the first player
            if len(self.clients) == 1:
                self.game_state['game_started'] = True
                print("Game started!")
            
            # Broadcast player joined to all clients
            self.broadcast_message({
                'type': 'player_joined',
                'player_id': player_id,
                'name': player_name,
                'color': player_color,
                'total_players': len(self.clients)
            }, exclude=client_socket)
            
            return {
                'type': 'join_success',
                'player_id': player_id,
                'color': player_color,
                'game_state': self.get_game_state_dict()
            }
    
    def handle_start_drawing(self, client_socket: socket.socket, message: dict) -> dict:
        """Handle a player starting to draw in a square"""
        if client_socket not in self.clients:
            return {'type': 'error', 'message': 'Not connected'}
        
        player_id = self.clients[client_socket]['player_id']
        row = message.get('row')
        col = message.get('col')
        
        if row is None or col is None or not (0 <= row < 8) or not (0 <= col < 8):
            return {'type': 'error', 'message': 'Invalid square coordinates'}
        
        with self.lock:
            # Check if square is already owned
            if self.game_state['board'][row][col] is not None:
                return {'type': 'error', 'message': 'Square is already owned'}
            
            # Check if square is currently being drawn on by another player
            if (row, col) in self.game_state['active_squares']:
                current_player = self.game_state['active_squares'][(row, col)]
                if current_player != player_id:
                    return {'type': 'error', 'message': 'Square is currently being drawn on by another player'}
            
            # Mark square as active for this player
            self.game_state['active_squares'][(row, col)] = player_id
            
            print(f"Player {player_id} started drawing in square ({row}, {col})")
            
            # Broadcast to all other clients
            self.broadcast_message({
                'type': 'square_locked',
                'row': row,
                'col': col,
                'player_id': player_id
            }, exclude=client_socket)
            
            return {'type': 'start_drawing_success', 'row': row, 'col': col}
    
    def handle_drawing_data(self, client_socket: socket.socket, message: dict) -> dict:
        """Handle drawing data from a player"""
        if client_socket not in self.clients:
            return {'type': 'error', 'message': 'Not connected'}
        
        player_id = self.clients[client_socket]['player_id']
        row = message.get('row')
        col = message.get('col')
        drawing_data = message.get('data', [])
        
        # Verify the player is allowed to draw in this square
        with self.lock:
            if (row, col) not in self.game_state['active_squares']:
                return {'type': 'error', 'message': 'Square is not active for drawing'}
            
            if self.game_state['active_squares'][(row, col)] != player_id:
                return {'type': 'error', 'message': 'You are not authorized to draw in this square'}
        
        # Broadcast drawing data to other clients for real-time visualization
        self.broadcast_message({
            'type': 'drawing_update',
            'row': row,
            'col': col,
            'player_id': player_id,
            'data': drawing_data
        }, exclude=client_socket)
        
        return {'type': 'drawing_data_received'}
    
    def handle_finish_drawing(self, client_socket: socket.socket, message: dict) -> dict:
        """Handle a player finishing drawing in a square"""
        if client_socket not in self.clients:
            return {'type': 'error', 'message': 'Not connected'}
        
        player_id = self.clients[client_socket]['player_id']
        row = message.get('row')
        col = message.get('col')
        coverage_percentage = message.get('coverage', 0)
        
        with self.lock:
            # Verify the player was drawing in this square
            if (row, col) not in self.game_state['active_squares']:
                return {'type': 'error', 'message': 'Square is not active for drawing'}
            
            if self.game_state['active_squares'][(row, col)] != player_id:
                return {'type': 'error', 'message': 'You are not authorized to finish drawing in this square'}
            
            # Remove from active squares
            del self.game_state['active_squares'][(row, col)]
            
            # Check if player covered at least 50% of the square
            success = coverage_percentage >= 50.0
            
            if success:
                # Player successfully captured the square
                self.game_state['board'][row][col] = player_id
                self.game_state['players'][player_id]['score'] += 1
                
                print(f"Player {player_id} captured square ({row}, {col}) with {coverage_percentage:.1f}% coverage")
                
                # Check if game is over (all squares filled)
                game_over = self.check_game_over()
                
                response_data = {
                    'type': 'square_captured',
                    'row': row,
                    'col': col,
                    'player_id': player_id,
                    'coverage': coverage_percentage,
                    'game_over': game_over
                }
                
                if game_over:
                    winner_id, max_score = self.calculate_winner()
                    self.game_state['game_ended'] = True
                    self.game_state['winner'] = winner_id
                    response_data['winner_id'] = winner_id
                    response_data['final_scores'] = {pid: self.game_state['players'][pid]['score'] 
                                                   for pid in self.game_state['players']}
                    
                    print(f"Game over! Winner: Player {winner_id} with {max_score} squares")
                
            else:
                # Player failed to capture the square
                print(f"Player {player_id} failed to capture square ({row}, {col}) with {coverage_percentage:.1f}% coverage")
                
                response_data = {
                    'type': 'square_failed',
                    'row': row,
                    'col': col,
                    'player_id': player_id,
                    'coverage': coverage_percentage
                }
            
            # Broadcast result to all clients
            self.broadcast_message(response_data)
            
            return response_data
    
    def handle_get_game_state(self, client_socket: socket.socket) -> dict:
        """Return current game state to client"""
        return {
            'type': 'game_state',
            'state': self.get_game_state_dict()
        }
    
    def get_game_state_dict(self) -> dict:
        """Get a serializable copy of the game state"""
        return {
            'board': self.game_state['board'],
            'active_squares': {f"{k[0]},{k[1]}": v for k, v in self.game_state['active_squares'].items()},
            'players': self.game_state['players'],
            'game_started': self.game_state['game_started'],
            'game_ended': self.game_state['game_ended'],
            'winner': self.game_state['winner']
        }
    
    def check_game_over(self) -> bool:
        """Check if all squares have been captured"""
        for row in self.game_state['board']:
            for cell in row:
                if cell is None:
                    return False
        return True
    
    def calculate_winner(self) -> Tuple[Optional[int], int]:
        """Calculate the winner based on scores"""
        if not self.game_state['players']:
            return None, 0
        
        max_score = max(player['score'] for player in self.game_state['players'].values())
        winners = [pid for pid, player in self.game_state['players'].items() 
                  if player['score'] == max_score]
        
        # If there's a tie, return the first winner (could be enhanced to handle ties differently)
        return winners[0] if len(winners) == 1 else None, max_score
    
    def broadcast_message(self, message: dict, exclude: socket.socket = None):
        """Send a message to all connected clients except the excluded one"""
        message_str = json.dumps(message)
        disconnected_clients = []
        
        for client_socket in self.clients:
            if client_socket != exclude:
                try:
                    send_message_frame(client_socket, message)
                except Exception as e:
                    print(f"Error sending message to client: {e}")
                    disconnected_clients.append(client_socket)
        
        # Clean up disconnected clients
        for client_socket in disconnected_clients:
            self.disconnect_client(client_socket)
    
    def disconnect_client(self, client_socket: socket.socket):
        """Handle client disconnection"""
        if client_socket in self.clients:
            with self.lock:
                client_info = self.clients[client_socket]
                player_id = client_info['player_id']
                
                # Remove from active squares if player was drawing
                squares_to_remove = [(row, col) for (row, col), pid in self.game_state['active_squares'].items() 
                                   if pid == player_id]
                for square in squares_to_remove:
                    del self.game_state['active_squares'][square]
                
                # Remove player from game state
                if player_id in self.game_state['players']:
                    del self.game_state['players'][player_id]
                
                # Remove from clients
                del self.clients[client_socket]
                
                print(f"Player {client_info['name']} (ID: {player_id}) disconnected")
                
                # Broadcast player left
                self.broadcast_message({
                    'type': 'player_left',
                    'player_id': player_id,
                    'name': client_info['name'],
                    'squares_freed': squares_to_remove
                })
        
        try:
            client_socket.close()
        except:
            pass
    
    def cleanup(self):
        """Clean up server resources"""
        print("Shutting down server...")
        
        # Close all client connections
        for client_socket in list(self.clients.keys()):
            self.disconnect_client(client_socket)
        
        # Close server socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print("Server shut down complete")

def main():
    """Main function to start the server"""
    import sys
    
    host = 'localhost'
    port = 12345
    
    # Allow command line arguments for host and port
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print("Invalid port number")
            sys.exit(1)
    
    server = ScribboServer(host, port)
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.cleanup()
    except Exception as e:
        print(f"Server error: {e}")
        server.cleanup()

if __name__ == "__main__":
    main()
