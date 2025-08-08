"""
Scribbo Game Server with GUI
"""
import socket
import threading
import time
from player import Player
from gameboard import GameBoard
from protocol_gui import MessageProtocol
from utils import send_message_frame, recv_message_frame

class ScribboServer_GUI:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.board = GameBoard()
        self.players = {}
        self.max_players = MessageProtocol.MAX_PLAYERS

    def start_server(self):
        """Start the server and accept connections"""
        addr = (self.host, self.port)
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(addr)
        server_socket.listen()
        print(f"Server started at {addr}")

        # Set up board broadcasting
        client_broadcasting = threading.Thread(target=self.handle_broadcast)
        client_broadcasting.start()

        # Start new thread for each client and store them in a list
        threads = []
        client_connections = 0

        while client_connections < self.max_players:
            client_socket, client_addr = server_socket.accept()
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket, client_addr))
            client_handler.start()
            threads.append(client_handler)
            client_connections += 1
        
        # Game loop
        while not self.board.is_game_over():
            time.sleep(1)
    
        for thread in threads:
            thread.join()
    
        client_broadcasting.join()
        # Close socket
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.close()
    
    def handle_client(self, client_socket, client_address):
        print(f"Accepted new client connection from {client_address}")

        while True:
            try:
                message = recv_message_frame(client_socket)
                msg_type = message.get('type')

                if msg_type == 'new_player':
                    color = message.get('color')
                    self.players[client_socket] = Player(color)
                    print(f"New player joined with color {color}")

                elif msg_type == 'filled_drawing_gui':
                    self.players[client_socket].stop_drawing_server_marked()
            
                elif msg_type in ['start_drawing_gui', 'stop_drawing_gui']:
                    x = message.get('x')
                    y = message.get('y')

                    print(f"Received {msg_type} message at ({x}, {y}) from client {client_address}")

                    # Update server's game board
                    square = self.board.get_square_at(x, y)
                    if msg_type == 'start_drawing_gui':
                        result = self.players[client_socket].start_drawing(square, x, y) # tries to lock the sqaure
                        if result == 'square_lock_on':                                   # another player has already locked it
                            square_locked_message = {
                                'type': 'square_lock_on'
                            }
                            send_message_frame(client_socket, square_locked_message)
                
                    
                    elif msg_type == 'stop_drawing_gui':
                        self.players[client_socket].stop_drawing()                        # unlock square   
    
                # Check if game is over
                if self.board.is_game_over():
                    print("GAME OVER")
                    break
            
            except Exception as _:
                return
        
        print("returning from handle_client")
        return

    def handle_broadcast(self):
        while True:
            time.sleep(0.2)
            for client in self.players.keys():
                send_message_frame(client, self.board.board_to_message())
        
            if self.board.is_game_over():
                for client in self.players.keys():
                    winner_msg = self.winner_message(self.players)
                    print(winner_msg)
                    send_message_frame(client, winner_msg)
                break

        for client in self.players.keys():
            # broadcast final board update
            send_message_frame(client, self.board.board_to_message())
    
        time.sleep(8)
        for client in self.players.keys():
            client.close()
    
        return
    
    def winner_message(self, players):
    # Calculate the winner
        max_squares_captured = 0
        winner_color_key = None

        for color_key, player in self.players.items():
            if player.taken_squares > max_squares_captured:
                max_squares_captured = player.taken_squares
                winner_color_key = color_key
    
        if winner_color_key is not None:
            winner_color = players[winner_color_key].color
            if winner_color == (255, 0, 0):
                winner_text = f"The winner is Player Red."
            elif winner_color == (0,255, 0):
                winner_text = f"The winner is Player Green"
            elif winner_color == (0, 0, 255):
                winner_text = f"The winner is Player Blue"
            elif winner_color == (255, 255, 0):
                winner_text = f"The winner is Player Yellow"
            else:
                winner_text = "Its a tie!"
    
        return {
            'type': 'winner',
            'winner_text': winner_text
        }


def main():

    host = 'localhost'
    port = 12345

    server = ScribboServer_GUI(host, port)
    server.start_server()

if __name__ == "__main__":
    main()
