"""
Reprsents individual squares in the board.
Previously (row, col) in game logic, now (x, y) = pygame.mouse.get_pos()

"""
from PIL import Image
from PIL import ImageDraw 
from protocol_gui import MessageProtocol
import threading

class Square:
    def __init__(self, coordinates):
        self.square_size = MessageProtocol.SQUARE_SIZE
        self.owner = None
        self.color = None
        self.coordinates = coordinates # refers to implied pixel corners 
        self.lock = threading.Lock()
        self.is_taken = False
        self.image = Image.new('RGB', (self.square_size, self.square_size)) # Create a new image for the square

    def __getstate__(self):
        """Return the state of the square for serialization.
           Does not include lock or image
        """
        return {
            'coordinates': self.coordinates,
            'owner': self.owner,
            'color': self.color,
            'is_active': self.is_taken
        }

    def __setstate__(self, state):
        """Set the state of the square from deserialization."""
        self.square_size = MessageProtocol.SQUARE_SIZE
        self.coordinates = state['coordinates']
        self.owner = state['owner']
        self.color = state['color']
        self.is_taken = state['is_taken']
        self.lock = threading.Lock()
        self.image = Image.new('RGB', (self.square_size, self.square_size))

    def clone(self, cloned_square):
        """Create a deep copy of the square."""
        self.is_taken = cloned_square.is_taken
        self.owner = cloned_square.owner
        self.color = cloned_square.color

    def draw(self, player, x, y):
        """Draw on the square at the given coordinates."""
        draw = ImageDraw.Draw(self.image)
        
        # Convert coordinates to PIL image coordinates
        rel_x = x - self.coordinates[0]
        rel_y = y - self.coordinates[1]

        # Draw a small square around the drawing point
        # Bounding box defined by (left, top) and (right, bottom)
        square_size = 10
        left = max(0, rel_x - square_size // 2)
        top = max(0, rel_y - square_size // 2)
        right = min (self.square_size, rel_x + square_size // 2)
        bottom = min (self.square_size, rel_y + square_size // 2)
        right = max(right, left + 1)
        bottom = max(bottom, top + 1)
        draw.rectangle([left, top, right, bottom], fill=player.color)


