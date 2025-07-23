"""
Test script for Scribbo client-server system
Demonstrates basic functionality and can be used for testing.
"""

import threading
import time
import json
from server import ScribboServer
from client import ScribboClient
from protocol import MessageProtocol
from game_engine import GameEngine

class ScribboTester:
    def __init__(self):
        self.server = None
        self.clients = []
        self.game_engine = GameEngine()
        
    def start_test_server(self, host='localhost', port=12345):
        """Start a test server"""
        print("Starting test server...")
        self.server = ScribboServer(host, port)
        
        # Start server in a separate thread
        server_thread = threading.Thread(target=self.server.start_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Give server time to start
        time.sleep(1)
        print(f"Test server started on {host}:{port}")
        
    def create_test_client(self, name: str, host='localhost', port=12345) -> ScribboClient:
        """Create and connect a test client"""
        client = ScribboClient()
        
        if client.connect_to_server(host, port, name):
            self.clients.append(client)
            print(f"Test client '{name}' connected successfully")
            return client
        else:
            print(f"Failed to connect test client '{name}'")
            return None
            
    def simulate_game_session(self):
        """Simulate a complete game session with multiple players"""
        print("\\n=== STARTING SIMULATED GAME SESSION ===")
        
        # Start server
        self.start_test_server()
        
        # Create multiple test clients
        clients = []
        player_names = ["Alice", "Bob", "Charlie", "Diana"]
        
        for name in player_names:
            client = self.create_test_client(name)
            if client:
                clients.append(client)
                time.sleep(0.5)  # Stagger connections
        
        if len(clients) < 2:
            print("Need at least 2 clients for testing")
            return
        
        print(f"\\nConnected {len(clients)} players, starting game simulation...")
        time.sleep(2)
        
        # Simulate some game moves
        test_moves = [
            (0, 0, 0, 75.0),  # Player 0, square (0,0), 75% coverage
            (1, 1, 1, 60.0),  # Player 1, square (1,1), 60% coverage  
            (0, 2, 2, 45.0),  # Player 0, square (2,2), 45% coverage (should fail)
            (1, 3, 3, 80.0),  # Player 1, square (3,3), 80% coverage
            (0, 4, 4, 90.0),  # Player 0, square (4,4), 90% coverage
            (1, 5, 5, 55.0),  # Player 1, square (5,5), 55% coverage
        ]
        
        for player_idx, row, col, coverage in test_moves:
            if player_idx < len(clients):
                client = clients[player_idx]
                player_name = player_names[player_idx]
                
                print(f"\\n{player_name} attempting to draw in square ({row}, {col})...")
                
                if client.start_drawing_in_square(row, col):
                    time.sleep(1)  # Simulate drawing time
                    client.finish_drawing(coverage)
                    print(f"  -> Finished with {coverage}% coverage")
                else:
                    print(f"  -> Failed to start drawing")
                
                time.sleep(1)  # Wait between moves
        
        # Show final game state
        print("\\n=== FINAL GAME STATE ===")
        if clients:
            clients[0].get_game_state()
            time.sleep(0.5)
            clients[0].print_board_state()
        
        # Cleanup
        print("\\n=== CLEANING UP ===")
        for client in clients:
            client.disconnect()
        
        if self.server:
            self.server.cleanup()
            
        print("Test session completed!")

def test_protocol_messages():
    """Test protocol message creation and validation"""
    print("\\n=== TESTING PROTOCOL MESSAGES ===")
    
    # Test message creation
    join_msg = MessageProtocol.create_join_message("TestPlayer")
    print(f"Join message: {join_msg}")
    
    start_draw_msg = MessageProtocol.create_start_drawing_message(2, 3)
    print(f"Start drawing message: {start_draw_msg}")
    
    finish_draw_msg = MessageProtocol.create_finish_drawing_message(2, 3, 75.5)
    print(f"Finish drawing message: {finish_draw_msg}")
    
    # Test validation functions
    print(f"Valid coordinates (3, 4): {MessageProtocol.validate_coordinates(3, 4)}")
    print(f"Invalid coordinates (8, 9): {MessageProtocol.validate_coordinates(8, 9)}")
    print(f"Valid coverage 75.0: {MessageProtocol.validate_coverage(75.0)}")
    print(f"Invalid coverage 150.0: {MessageProtocol.validate_coverage(150.0)}")
    print(f"Successful capture 60%: {MessageProtocol.is_successful_capture(60.0)}")
    print(f"Failed capture 40%: {MessageProtocol.is_successful_capture(40.0)}")

def test_game_engine():
    """Test game engine functionality"""
    print("\\n=== TESTING GAME ENGINE ===")
    
    engine = GameEngine()
    
    # Test drawing patterns
    patterns = ["diagonal", "circle", "square", "cross", "random"]
    
    for pattern in patterns:
        points = engine.create_test_drawing(pattern)
        coverage = engine.calculate_coverage_percentage(points)
        drawing_time = engine.estimate_drawing_time(points)
        valid = engine.validate_drawing_points(points)
        
        print(f"{pattern.capitalize()} pattern:")
        print(f"  Points: {len(points)}")
        print(f"  Coverage: {coverage:.1f}%")
        print(f"  Drawing time: {drawing_time:.2f}s")
        print(f"  Valid: {valid}")
    
    # Test board validation
    valid_board = [[None for _ in range(8)] for _ in range(8)]
    valid_board[0][0] = 1
    valid_board[1][1] = 2
    
    from game_engine import GameValidator
    print(f"\\nValid board test: {GameValidator.validate_board_state(valid_board)}")
    
    # Test game completion
    empty_board = [[None for _ in range(8)] for _ in range(8)]
    full_board = [[1 for _ in range(8)] for _ in range(8)]
    
    print(f"Empty board complete: {engine.is_game_complete(empty_board)}")
    print(f"Full board complete: {engine.is_game_complete(full_board)}")
    
    # Test winner calculation
    test_players = {
        1: {'name': 'Alice', 'color': 'red', 'score': 15},
        2: {'name': 'Bob', 'color': 'blue', 'score': 20},
        3: {'name': 'Charlie', 'color': 'green', 'score': 20},
    }
    
    winner, all_winners, max_score = engine.calculate_winner(test_players)
    print(f"\\nWinner calculation:")
    print(f"  Single winner: {winner}")
    print(f"  All winners: {all_winners}")
    print(f"  Max score: {max_score}")

def run_interactive_test():
    """Run an interactive test where user can manually test features"""
    print("\\n=== INTERACTIVE TEST MODE ===")
    print("Commands:")
    print("  server - Start a test server")
    print("  client <name> - Connect a client")
    print("  protocol - Test protocol messages")
    print("  engine - Test game engine")
    print("  simulate - Run full simulation")
    print("  quit - Exit")
    
    tester = ScribboTester()
    
    while True:
        command = input("\\nTest> ").strip().lower()
        
        if command == 'quit':
            break
        elif command == 'server':
            tester.start_test_server()
        elif command.startswith('client '):
            name = command[7:] or "TestPlayer"
            tester.create_test_client(name)
        elif command == 'protocol':
            test_protocol_messages()
        elif command == 'engine':
            test_game_engine()
        elif command == 'simulate':
            tester.simulate_game_session()
        elif command == 'help':
            print("Available commands: server, client <name>, protocol, engine, simulate, quit")
        else:
            print("Unknown command. Type 'help' for available commands.")

def main():
    """Main test function"""
    import sys
    
    print("Scribbo Game Test Suite")
    print("======================")
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == 'protocol':
            test_protocol_messages()
        elif test_type == 'engine':
            test_game_engine()
        elif test_type == 'simulate':
            tester = ScribboTester()
            tester.simulate_game_session()
        elif test_type == 'interactive':
            run_interactive_test()
        else:
            print(f"Unknown test type: {test_type}")
            print("Available tests: protocol, engine, simulate, interactive")
    else:
        # Run all tests by default
        test_protocol_messages()
        test_game_engine()
        
        # Ask if user wants to run simulation
        response = input("\\nRun full simulation? (y/n): ").strip().lower()
        if response == 'y':
            tester = ScribboTester()
            tester.simulate_game_session()

if __name__ == "__main__":
    main()
