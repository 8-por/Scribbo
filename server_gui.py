"""
Scribbo Game Server with GUI
"""
import socket
import threading
import time
import json
from player import Player
from gameboard import GameBoard
from protocol_gui import MessageProtocol


def broadcast_message(client, message: dict):
    message_str = json.dumps(message)
    client.send(message_str.encode('utf-8'))

def winner_message(players):
    # Calculate the winner
    max_squares_captured = 0
    winner_color_key = None

    for color_key, player in players.items():
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


def handle_client(client_socket, client_address):
    print(f"Accepted new client connection from {client_address}")
    
    while True:
        try:
            
            data = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            if not data:
                break

            message = json.loads(data)
            msg_type = message.get('type')

            if msg_type == 'new_player':
                color = message.get('color')
                players[client_socket] = Player(color)
                print(f"New player joined with color {color}")

            elif msg_type == 'filled_drawing_gui':
                players[client_socket].stop_drawing_server_coloured()
            
            elif msg_type in ['start_drawing_gui', 'stop_drawing_gui']:
                x = message.get('x')
                y = message.get('y')

                print(f"Received {msg_type} message at ({x}, {y}) from client {client_address}")

                # Update server's game board
                square = board.get_square_at(x, y)
                if msg_type == 'start_drawing_gui':
                    result = players[client_socket].start_drawing(square, x, y) # tries to lock the sqaure
                    if result == 'square_lock_on':                              # another player has already locked it
                        square_locked_message = {
                            'type': 'square_lock_on'
                        }
                        broadcast_message(client_socket, square_locked_message)
                
                    
                elif msg_type == 'stop_drawing_gui':
                    players[client_socket].stop_drawing()                       # unlock square   

                
            
            # Check if game is over
            if board.is_game_over():
                print("GAME OVER")
                break
            
        except Exception as _:
            return
        
    print("returning from handle_client")
    return

def handle_broadcast():
    while True:
        time.sleep(0.2)
        for client in players.keys():
            broadcast_message(client, board.board_to_message())
        
        if board.is_game_over():
            for client in players.keys():
                winner_msg = winner_message(players)
                print(winner_msg)
                broadcast_message(client, winner_msg)
            break

    for client in players.keys():
        # broadcast final board update
        broadcast_message(client, board.board_to_message())
    
    time.sleep(8)
    for client in players.keys():
        client.close()
    
    return


players = {}
board = GameBoard()
player_colors = ["RED", "GREEN", "BLUE", "YELLOW"]
BUFFER_SIZE = 2048

def main():
    
    SERVER_IP = 'localhost'
    SERVER_PORT = 12345
    ADDR = (SERVER_IP, SERVER_PORT)
    MAX_PLAYERS = MessageProtocol.MAX_PLAYERS

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(ADDR)
    server_socket.listen()
    print(f"Server started at {ADDR}")

    # Set up board broadcasting
    client_broadcasting = threading.Thread(target=handle_broadcast)
    client_broadcasting.start()

    # Wait for client connections 
    # Store client threads in a list
    threads = []
    num_players = 0
    
    while num_players < MAX_PLAYERS:
        client_socket, client_addr = server_socket.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_addr))
        client_handler.start()
        threads.append(client_handler)
        num_players += 1

    # Game loop
    while not board.is_game_over():
        time.sleep(1)
    
    for thread in threads:
        thread.join()
    
    client_broadcasting.join()
    # Close socket
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.close()

if __name__ == "__main__":
    main()





