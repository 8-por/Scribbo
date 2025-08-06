import pygame
import sys
from protocol_gui import MessageProtocol

class Player:
    def __init__(self, color_str):
        self.color_str = color_str
        self.color = COLORS[color_str]
        self.taken_squares = 0 # Player' score
        self.current_square = None
        self.drawing_active = False
        self.min_coverage_reached = False
        self.square_size = MessageProtocol.SQUARE_SIZE
    
    def start_drawing(self, square, x, y):
        if square is None:
            print(f"Square is invalid")
            response = 'square_locked_on'
            return response
        elif square.lock.acquire(blocking=False): 
            print(f"Square is currently in use: ({x}, {y})")
            response = 'square_locked_on'
            return response
        elif square.is_taken:
            return 'square_taken'
        self.current_square = square
        print("Current square: ", self.current_square.coordinates)
        square.draw(self, x, y)
        return None
    
    def stop_drawing(self):
        # Called by client when player stops pressing mouse button
        if self.current_square:
            self.current_square.lock.release()

            # Coverage calculation. range [0,1]
            colored_pixels = sum(1 for pixel in self.current_square.image.getdata() if pixel == self.color)
            total_pixels = self.square_size * self.square_size
            coverage = (colored_pixels / total_pixels) 
            
            print("Colored: ", colored_pixels)
            print("Total: ", total_pixels)
            print("Coverage: ", coverage)

            if coverage >= MessageProtocol.MIN_COVERAGE_PERCENTAGE:
                self.min_coverage_reached = True
            self.current_square = None
    
    def continue_drawing(self, square, x, y):
        if self.current_square and square and square.coordinates == self.current_square.coordinates:
            self.current_square.draw(self, x, y)
    
    def stop_drawing_server_coloured(self):
        if self.current_square:
            self.current_square.lock.release()
            self.current_square.is_taken = True
            self.current_square.color = self.color
            self.current_square.owner = self
            self.taken_squares += 1
            print("This should have increased: ", self.taken_squares)
            self.current_square = None
        
        else:
            print("Current square is none")



# screen_size = (400, 400)
def color_selection(screen):
    player_colors = set(COLORS.keys())
    font = pygame.font.Font(None, 36)
    color_rects = {}  # Initialize color_rects dictionary to store color rectangles
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                for color, rect in color_rects.items():
                    if rect.collidepoint(event.pos) and color in player_colors:
                        print("color picked: ", color)
                        player_colors.remove(color)
                        return color

        screen.fill((255, 255, 255))
        for i, color in enumerate(COLORS):
            pygame.draw.rect(screen, COLORS[color], (50 + i * 80, 50, 70, 70))
            color_rects[color] = pygame.Rect(50 + i * 80, 50, 70, 70)

        pygame.display.flip()

COLORS = {
    'R': (255, 0, 0),  # Red
    'G': (0, 255, 0),  # Green
    'B': (0, 0, 255),  # Blue
    'Y': (255, 255, 0)  # Yellow
}