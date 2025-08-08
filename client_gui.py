"""
Scribbo Game Client with GUI
"""
import socket
import time
import sys
import threading
import pygame
from gameboard import GameBoard
from player import Player
from player import color_selection
from protocol_gui import MessageProtocol
from utils import send_message_frame, recv_message_frame

class ScribboClient_GUI:
    def __init__(self):
        self.board = GameBoard()
        self.player = None
        self.winner_key = "Thanks for playing!"
    
    def connect_to_server(self, host, port):
        addr = (host, port)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(addr)
        print(f"Connected to server at {addr}")

        # Initialize the game
        pygame.init()
        game_over = False

        screen_size = (400, 400)
        screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption("Scribbo Game")    

        chosen_color = color_selection(screen)
        self.player = Player(chosen_color)

        # Send new player message to server
        new_player_message = {
            'type': 'new_player',
            'color' : chosen_color
        }

        # Start receiving messages in seperate thread
        receive_thread = threading.Thread(target=self.receive_messages, args=(self.board, client_socket))
        # receive_thread.daemon = True
        receive_thread.start()

        send_message_frame(client_socket, new_player_message)

        while not game_over:
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.player.drawing_active = True
                    x, y = pygame.mouse.get_pos()
                    square = self.board.get_square_at(x, y)
                    self.player.start_drawing(square, x, y)

                    start_drawing_gui_message = {
                        'type': 'start_drawing_gui',
                        'x': x,
                        'y': y
                    }
                    send_message_frame(client_socket, start_drawing_gui_message)
            
                elif event.type == pygame.MOUSEBUTTONUP:
                    x, y = pygame.mouse.get_pos()
                    # Player stopped drawing at (x,y)
                    self.player.stop_drawing()
                    self.player.drawing_active = False
                    if self.player.min_coverage_reached:
                        # Send message that sqaure is filled
                        filled_drawing_gui_message = {
                            'type': 'filled_drawing_gui',
                            'x': x,
                            'y': y
                        }
                        send_message_frame(client_socket, filled_drawing_gui_message)
                        print("I have sent out a filled square")
                    else:
                        stop_drawing_gui_message = {
                            'type': 'stop_drawing_gui',
                            'x': x,
                            'y': y
                        }
                        send_message_frame(client_socket, stop_drawing_gui_message)
                    self.player.min_coverage_reached = False
            
                elif event.type == pygame.MOUSEMOTION:
                    x, y = pygame.mouse.get_pos()
                    if self.player.drawing_active:
                        square = self.board.get_square_at(x, y)
                        self.player.continue_drawing(square, x, y)
            
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()


            # display board
            screen.fill((255, 255, 255))
            self.board.draw_squares(screen)
            pygame.display.flip()

            if self.board.is_game_over():
                game_over = True
    
        screen.fill((255, 255, 255))
        self.board.draw_squares(screen)
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
        text = font.render(self.winner_key, True, (0, 0, 0))
        text_rect = text.get_rect(center=(500, 300))
        screen.blit(text, text_rect)
        pygame.display.flip()
        time.sleep(7)
        pygame.quit()


        receive_thread.join()
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.close()


    def receive_messages(self, board, client_socket):
        end_of_game = False
        while not end_of_game:
            try:
                message = recv_message_frame(client_socket)
                msg_type = message.get('type')

                # if msg_type == 'winner_color_key'
                if msg_type == 'winner':
                    winner_text = message.get('winner_text')
                    print(f"Game over, winner message received: {winner_text}")
                    self.winner_key = winner_text
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
                msg = recv_message_frame(client_socket)
                final_board_update = msg.get('board_state')
                board.message_to_board(final_board_update)
                break
            except BlockingIOError:
                pass
            except Exception as e:
                continue
        return

def main():

    host = 'localhost'
    port = 12345

    client = ScribboClient_GUI()
    client.connect_to_server(host, port)
    

if __name__ == "__main__":
    main()
