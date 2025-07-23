# Scribbo Game

A multiplayer client-server drawing game implemented from scratch using Python socket programming.

## Game Description

Scribbo is a competitive drawing game where players compete to capture squares on an 8×8 grid board. Players take turns drawing in empty squares, and if they color at least 50% of a square's area, they capture it. The player with the most captured squares at the end wins.

## Game Rules

- **Board**: 8×8 grid of squares
- **Objective**: Capture the most squares by the end of the game
- **Capturing**: Click and draw in an empty square until at least 50% is colored
- **Winning**: Player with the most squares when the board is full wins
- **Blocking**: While a player is drawing in a square, other players cannot draw in it

## Running the Game

### Method 1: Using the Launcher (Easiest)

```bash
# Interactive launcher
python launcher.py

# Command line options
python launcher.py server --host localhost --port 12345
python launcher.py client --host localhost --port 12345 --name "PlayerName"
```

### Method 2: Direct Execution

**Start Server:**
```bash
python server.py [host] [port]
# Example: python server.py localhost 12345
```

**Start Client:**
```bash
python client.py
# Follow prompts to enter server details and player name
```

### Method 3: Testing and Simulation

```bash
# Run automated tests
python test_game.py protocol    # Test message protocols
python test_game.py engine      # Test game engine
python test_game.py simulate    # Full game simulation
python test_game.py interactive # Interactive test mode
```

## How to Play

### Server Setup
1. One player starts the server using `python server.py`
2. Server displays its IP and port for other players to connect
3. Server automatically starts the game when first player joins

### Joining the Game
1. Run the client: `python client.py`
2. Enter server host/port and your player name
3. You'll be assigned a unique color and player ID

### Game Commands (Client)
```
draw <row> <col> <coverage>  # Draw in square with % coverage (0-100)
board                        # Show current board state
state                        # Display detailed game state
quit                         # Leave the game
```

### Example Gameplay
```
> draw 0 0 75
Started drawing in square (0, 0)
Finished drawing in square (0, 0) with 75.0% coverage
Square (0, 0) captured by Player 1 with 75.0% coverage

> board
=== BOARD STATE ===
   0 1 2 3 4 5 6 7
0  1 . . . . . . .
1  . . . . . . . .
2  . . . . . . . .
...

=== PLAYERS ===
Player 1: Alice (red) - 1 squares
Player 2: Bob (blue) - 0 squares
```

## Network Protocol

### Message Format
All messages are JSON objects sent over TCP sockets:

```json
{
  "type": "message_type",
  "param1": "value1",
  "param2": "value2"
}
```

### Key Message Types

**Client → Server:**
- `join`: Join the game with player name
- `start_drawing`: Begin drawing in a square
- `drawing_data`: Send real-time drawing points
- `finish_drawing`: Complete drawing with coverage percentage
- `get_game_state`: Request current game state

**Server → Client:**
- `join_success`: Confirm successful join with player info
- `player_joined`/`player_left`: Player connection updates
- `square_locked`: Square is being drawn on
- `square_captured`/`square_failed`: Drawing completion results
- `drawing_update`: Real-time drawing from other players


## Todo
### Potential Enhancements
- **Graphics**: Add GUI with actual drawing canvas



