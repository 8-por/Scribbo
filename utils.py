import json
import struct
from protocol import MessageProtocol

def send_message_frame(sock, message_dict):
    """Send a message with a 4-byte length prefix"""
    try:
        data = json.dumps(message_dict).encode('utf-8')

        # Check if data is too large
        if len(data) > MessageProtocol.MAX_MESSAGE_SIZE:
            raise ValueError(f"Message exceeds maximum size ({len(data)} > {MessageProtocol.MAX_MESSAGE_SIZE})")
        
        length = struct.pack('!I', len(data)) # 4-byte prefix for length (big-endian)
        sock.sendall(length + data)

    except Exception as e:
        raise RuntimeError(f"Failed to send message: {e}")

def recv_message_frame(sock):
    """Receive a message by reading the length first (4 bytes), then the data"""
    # Read the first 4 bytes
    raw_len = sock.recv(4)
    if not raw_len or len(raw_len) != 4:
        return None # Connection closed or incomplete header
    
    msg_len = struct.unpack('!I', raw_len)[0]

    # Check message size
    if msg_len > MessageProtocol.MAX_MESSAGE_SIZE:
        raise ValueError(f"Message too large: {msg_len} bytes")

    # Keep reading until receiving full message
    data = b''
    while len(data) < msg_len:
        packet = sock.recv(msg_len - len(data))
        if not packet:
            return None # Connection lost
        data += packet

    try:
        return json.loads(data.decode('utf-8'))
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON data received")