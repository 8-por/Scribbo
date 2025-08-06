"""
Add drawing mechanism on client side
"""
import socket
import json
import time
import sys
import threading
import pygame
from gameboard import GameBoard
from player import Player
from player import color_selection
from protocol_gui import MessageProtocol

def receive_messages(board, client_socket):
    end_of_game = False
    while not end_of_game:
        try:
            data = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            if not data:
                break

            message = json.loads(data)
            msg_type = message.get('type')

            # if msg_type == 'winner_color_key'
            if msg_type == 'winner':
                winner_text = message.get('winner_text')
                print(f"Game over, winner message received: {winner_text}")
                global winner_key
                winner_key = winner_text
                end_of_game = True  

            elif msg_type == 'square_lock_on':
                print("The square you're trying to draw on is currently in use.")

            else:
                # msg_type == 'board_state'
                board_state = message.get('board_state')
                print("board_state received: ", board_state)
                board.message_to_board(board_state)
        
        except BlockingIOError:
            pass
        except Exception as e:
            continue
    
    
    while True:
        try:
            data = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            if data is not None:
                msg = json.loads(data)
                final_board_update = msg.get('board_state')
                board.message_to_board(final_board_update)
                break
        except BlockingIOError:
            pass
        except Exception as e:
            continue
    return







BUFFER_SIZE = 2048
winner_key = "Thanks for playing!"
board = GameBoard()

def main():

    SERVER_IP = '127.0.0.1'  # localhost
    SERVER_PORT = 12345
    ADDR = (SERVER_IP, SERVER_PORT)
    # Create a TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(ADDR)
    print(f"Connected to server at {ADDR}")

    # Initialize the game
    pygame.init()
    game_over = False

    # square_size = MessageProtocol.SQUARE_SIZE
    # board_size = MessageProtocol.BOARD_SIZE
    # screen_size = (board_size * square_size, board_size * square_size)
    screen_size = (400, 400)
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("Scribbo Game")    

    chosen_color = color_selection(screen)
    player = Player(chosen_color)

    # Send new player message to server
    new_player_message = {
        'type': 'new_player',
        'color' : chosen_color
    }

    # Start receiving messages in seperate thread
    receive_thread = threading.Thread(target=receive_messages, args=(board, client_socket))
    # receive_thread.daemon = True
    receive_thread.start()

    message_str = json.dumps(new_player_message)
    client_socket.send(message_str.encode('utf-8'))

    while not game_over:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                player.drawing_active = True
                x, y = pygame.mouse.get_pos()
                square = board.get_square_at(x, y)
                player.start_drawing(square, x, y)

                start_drawing_gui_message = {
                    'type': 'start_drawing_gui',
                    'x': x,
                    'y': y
                }
                client_socket.send((json.dumps(start_drawing_gui_message)).encode('utf-8'))
            
            elif event.type == pygame.MOUSEBUTTONUP:
                x, y = pygame.mouse.get_pos()
                # Player stopped drawing at (x,y)
                player.stop_drawing()
                player.drawing_active = False
                if player.min_coverage_reached:
                    # Send message that sqaure is filled
                    filled_drawing_gui_message = {
                        'type': 'filled_drawing_gui',
                        'x': x,
                        'y': y
                    }
                    client_socket.send((json.dumps(filled_drawing_gui_message)).encode('utf-8'))
                    print("I have sent out a filled square")
                else:
                    stop_drawing_gui_message = {
                        'type': 'stop_drawing_gui',
                        'x': x,
                        'y': y
                    }
                    client_socket.send((json.dumps(stop_drawing_gui_message)).encode('utf-8'))
                player.min_coverage_reached = False
            
            elif event.type == pygame.MOUSEMOTION:
                x, y = pygame.mouse.get_pos()
                if player.drawing_active:
                    square = board.get_square_at(x, y)
                    player.continue_drawing(square, x, y)
            
            elif event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()


        # display board
        screen.fill((255, 255, 255))
        board.draw_squares(screen)
        pygame.display.flip()

        if board.is_game_over():
            game_over = True
    
    screen.fill((255, 255, 255))
    board.draw_squares(screen)
    pygame.display.flip()
    time.sleep(3)
    pygame.quit()
    
    
    # display game over
    pygame.init()
    screen_size = (1000, 600)
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("Game over")
    font = pygame.font.SysFont('Consolas', 20)
    screen.fill((255, 255, 255))
    text = font.render(winner_key, True, (0, 0, 0))
    text_rect = text.get_rect(center=(500, 300))
    screen.blit(text, text_rect)
    pygame.display.flip()
    time.sleep(7)
    pygame.quit()


    receive_thread.join()
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.close()

if __name__ == "__main__":
    main()



