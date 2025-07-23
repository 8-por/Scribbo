"""
Scribbo Game Launcher
Simple launcher script for starting server or client instances.
"""

import sys
import argparse
from server import ScribboServer
from client import ScribboClient

def start_server(host='localhost', port=12345):
    """Start the Scribbo server"""
    print(f"Starting Scribbo server on {host}:{port}")
    print("Press Ctrl+C to stop the server")
    
    server = ScribboServer(host, port)
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\\nShutting down server...")
        server.cleanup()
    except Exception as e:
        print(f"Server error: {e}")
        server.cleanup()

def start_client(host='localhost', port=12345, name='Player'):
    """Start the Scribbo client"""
    print(f"Starting Scribbo client: {name}")
    print(f"Connecting to server at {host}:{port}")
    
    client = ScribboClient()
    
    try:
        if client.connect_to_server(host, port, name):
            print("Connected successfully!")
            print("\\nGame Instructions:")
            print("- The board is an 8x8 grid (rows 0-7, columns 0-7)")
            print("- To capture a square, you must color at least 50% of it")
            print("- Use 'draw <row> <col> <coverage>' to simulate drawing")
            print("- Use 'board' to see the current board state")
            print("- Use 'quit' to exit")
            
            # Run the client's main loop
            client.main()
        else:
            print("Failed to connect to server")
    except KeyboardInterrupt:
        print("\\nDisconnecting...")
        client.disconnect()
    except Exception as e:
        print(f"Client error: {e}")
        client.disconnect()

def main():
    """Main launcher function"""
    parser = argparse.ArgumentParser(description='Scribbo Game Launcher')
    parser.add_argument('mode', choices=['server', 'client'], 
                       help='Start in server or client mode')
    parser.add_argument('--host', default='localhost', 
                       help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=12345, 
                       help='Server port (default: 12345)')
    parser.add_argument('--name', default='Player', 
                       help='Player name for client mode (default: Player)')
    
    args = parser.parse_args()
    
    if args.mode == 'server':
        start_server(args.host, args.port)
    elif args.mode == 'client':
        start_client(args.host, args.port, args.name)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Interactive mode if no arguments provided
        print("Scribbo Game Launcher")
        print("====================")
        print("1. Start Server")
        print("2. Start Client")
        print("3. Exit")
        
        while True:
            try:
                choice = input("\\nSelect option (1-3): ").strip()
                
                if choice == '1':
                    host = input("Enter host (default: localhost): ").strip() or 'localhost'
                    port_str = input("Enter port (default: 12345): ").strip()
                    port = 12345
                    if port_str:
                        try:
                            port = int(port_str)
                        except ValueError:
                            print("Invalid port, using default 12345")
                    start_server(host, port)
                    break
                    
                elif choice == '2':
                    host = input("Enter server host (default: localhost): ").strip() or 'localhost'
                    port_str = input("Enter server port (default: 12345): ").strip()
                    port = 12345
                    if port_str:
                        try:
                            port = int(port_str)
                        except ValueError:
                            print("Invalid port, using default 12345")
                    name = input("Enter your player name: ").strip() or 'Player'
                    start_client(host, port, name)
                    break
                    
                elif choice == '3':
                    print("Goodbye!")
                    break
                    
                else:
                    print("Invalid choice. Please select 1, 2, or 3.")
                    
            except KeyboardInterrupt:
                print("\\nGoodbye!")
                break
    else:
        main()
