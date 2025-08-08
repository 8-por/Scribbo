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




## How to Play

### Server Setup
1. One player starts the server using `python server.py`
2. Server displays its IP and port for other players to connect
3. Server automatically starts the game when first player joins

### Joining the Game
1. Edit server host/port at main on client_gui.py
2. python ./client_gui.py



### Example Gameplay
<img width="1199" height="678" alt="image" src="https://github.com/user-attachments/assets/a50777dc-ee64-417a-a3b3-98b9aaa13838" />```




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






