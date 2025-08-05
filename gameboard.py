"""
Graphical game board for the Scribbo game.
Handles the drawing and interaction with squares on the game board
"""
from protocol_gui import MessageProtocol
from square import Square
import pygame

class GameBoard:
    def __init__(self):
        self.square_size = MessageProtocol.SQUARE_SIZE
        self.board_size = MessageProtocol.BOARD_SIZE
        self.COLS = 2
        self.ROWS = 2
        
        # 2D array of squares
        self.squares = [[Square((x*self.square_size, y*self.square_size)) for x in range(self.COLS)] for y in range(self.ROWS)]
    
    def draw_squares(self, screen):
        """Draw all squares on the game board"""
        for y, row in enumerate(self.squares):
            for x, square in enumerate(row):
                rect = pygame.Rect(x*self.square_size, y*self.square_size, self.square_size, self.square_size)
                pygame.draw.rect(screen, (0,0,0), rect, 1) # Draw square outline

                square_rect = rect.inflate(-8, -8)
                pygame.draw.rect(screen, square.color if square.is_taken else (255, 255, 255), square_rect)
    
    def is_game_over(self):
        """Check if none of the squares are active"""
        return all(square.is_taken for row in self.squares for square in row)
    
    def get_square_at(self, x, y):
        """Get the square at the given mouse position"""
        col = x // self.square_size
        row = y // self.square_size

        if 0 <= col < self.board_size and 0 <= row < self.board_size:
            return self.squares[row][col]
        return None
    
    def board_to_message(self):
        board_state = [['' for _ in range(self.ROWS)] for _ in range(self.COLS)]
        for y in range(self.ROWS):
            for x in range(self.COLS):
                if self.squares[y][x].color == None:
                    board_state[y][x] = '0'
                elif self.squares[y][x].color == (255, 0, 0):
                    board_state[y][x] = 'R'
                elif self.squares[y][x].color == (0, 255, 0):
                    board_state[y][x] = 'G'
                elif self.squares[y][x].color == (0, 0, 255):
                    board_state[y][x] = 'B'
                else:
                    board_state[y][x] = 'Y'
        
        return {
            'type': 'board_state',
            'board_state': board_state
        }
    
    def message_to_board(self,board_state):
        for y in range(self.ROWS):
            for x in range(self.COLS):
                if board_state[y][x] == '0':
                    self.squares[y][x].color = None
                    self.squares[y][x].is_taken = False
                elif board_state[y][x] == 'R':
                    self.squares[y][x].color = (255, 0, 0)
                    self.squares[y][x].is_taken = True
                elif board_state[y][x] == 'G':
                    self.squares[y][x].color = (0, 255, 0)
                    self.squares[y][x].is_taken = True
                elif board_state[y][x] == 'B':
                    self.squares[y][x].color = (0, 0, 255)
                    self.squares[y][x].is_taken = True
                else:
                    self.squares[y][x].color = (255, 255, 0)
                    self.squares[y][x].is_taken = True
        return

    
    
