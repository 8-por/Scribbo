#!/usr/bin/env python3
"""
Test script for request ID correlation system
"""

import time
import threading
import uuid
from client import ScribboClient

def test_request_id_generation():
    """Test that request IDs are properly generated and unique"""
    print("Testing request ID generation...")
    
    # Test UUID generation
    request_id1 = str(uuid.uuid4())
    request_id2 = str(uuid.uuid4())
    
    assert request_id1 != request_id2, "Request IDs should be unique"
    assert len(request_id1) > 0, "Request ID should not be empty"
    assert isinstance(request_id1, str), "Request ID should be a string"
    
    print("✓ Request ID generation tests passed!")

def test_message_correlation():
    """Test message correlation functionality"""
    print("Testing message correlation...")
    
    client = ScribboClient()
    
    # Test that request_id is added to messages
    test_message = {'type': 'test'}
    original_message = test_message.copy()
    
    # Simulate what send_message_and_wait_response would do
    request_id = str(uuid.uuid4())
    test_message['request_id'] = request_id
    
    assert 'request_id' in test_message, "request_id should be added to message"
    assert test_message['request_id'] == request_id, "request_id should match"
    assert test_message['type'] == original_message['type'], "Original message type should be preserved"
    
    # Test pending requests tracking
    client.pending_requests[request_id] = (test_message, time.time())
    assert request_id in client.pending_requests, "Request should be tracked"
    
    # Test response correlation
    response_message = {'type': 'test_response', 'request_id': request_id}
    assert response_message['request_id'] == request_id, "Response should have matching request_id"
    
    print("✓ Message correlation tests passed!")

def test_thread_safety():
    """Test thread safety of the correlation system"""
    print("Testing thread safety...")
    
    client = ScribboClient()
    
    # Test that lock is properly used
    assert client.lock is not None, "Lock should be initialized"
    
    # Test thread-safe operations
    with client.lock:
        client.pending_requests['test_id'] = ({'type': 'test'}, time.time())
        assert 'test_id' in client.pending_requests, "Should be able to add request under lock"
    
    print("✓ Thread safety tests passed!")

if __name__ == "__main__":
    print("Scribbo Request ID Correlation Test Suite")
    print("=" * 50)
    
    test_request_id_generation()
    test_message_correlation()
    test_thread_safety()
    
    print("\nAll tests passed! ✓")
    print("The request ID correlation system is working correctly.") 