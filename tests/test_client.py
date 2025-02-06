import socket
import threading
import time 
import sys
import os
import queue

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client import config
from client.network import ChatClient

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def start_mock_server(response_message="Hello, client!", expect_client_message=False):
    """
    Start a mock server and send a response message.
    
    Args:
        response_message (str): Message to send to client
        expect_client_message (bool): Whether to wait for client message before sending response
    """
    received_messages = []

    # Get the server configuration
    server_config = config.get_config()
    old_host = server_config["host"]

    # Create temporary socket to find a free port
    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    temp_socket.bind((old_host, 0))
    host, port = temp_socket.getsockname()
    temp_socket.close()

    def mock_server():
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server_socket.bind((host, port))
            print(f"[MOCK SERVER] Started at {host}:{port}")
            server_socket.listen(1)

            client_socket, _ = server_socket.accept()
            print("[MOCK SERVER] Client connected.")

            if expect_client_message:
                # Wait for client message first
                try:
                    print("[MOCK SERVER] Waiting for client message...")
                    message = client_socket.recv(1024).decode("utf-8")
                    if message:
                        received_messages.append(message)
                        print(f"[MOCK SERVER] Received from client: {message}")
                except Exception as e:
                    print(f"[MOCK SERVER ERROR] Failed to receive message: {e}")

            # Send response if specified
            if response_message:
                print(f"[MOCK SERVER] Sending response: {response_message}")
                client_socket.send(response_message.encode("utf-8"))
                print("[MOCK SERVER] Response sent")
            
            # Keep connection alive briefly
            time.sleep(2)

            client_socket.close()
            server_socket.close()
            print("[MOCK SERVER] Connection closed.")

        except Exception as e:
            print(f"[MOCK SERVER ERROR] {e}")

    server_thread = threading.Thread(target=mock_server, daemon=True)
    server_thread.start()
    time.sleep(0.5)  # Wait for server to start

    return host, port, received_messages


def start_client(host, port):
    """
    Start the client.
    """
    client = ChatClient(host, port)
    return client

# -----------------------------------------------------------------------------
# Pytest Test Cases
# -----------------------------------------------------------------------------

def test_client_initialization():
    """
    Test the initialization of the ChatClient class.
    """
    server_config = config.get_config()
    host = server_config["host"]
    port = server_config["port"]
    client = start_client(host, port) 
    assert client.host == host
    assert client.port == port
    assert not client.running
    assert client.thread is None
    assert client.received_messages == []
    client.close()

def test_client_connect():
    """
    Test the connection to the server.
    """
    host, port, _ = start_mock_server() 
    client = start_client(host, port)
    assert client.connect() is True 
    client.close()

def test_client_start():
    """
    Test starting the client.
    """
    host, port, _ = start_mock_server() 
    client = start_client(host, port)
    client.start()
    time.sleep(1) # Wait for the thread to start
    assert client.running
    assert client.thread is not None
    assert client.thread.is_alive()
    client.close()

def test_client_send_message():
    """
    Test sending a message to the server.
    """
    expected_message = "Hello, server!"
    host, port, received_messages = start_mock_server(expect_client_message=True)  # Wait for client message

    client = start_client(host, port)
    client.start()

    print("[TEST] Sending message to server...")
    client.send_message(expected_message)
    time.sleep(1)  # Wait for the message to be sent

    assert len(received_messages) > 0, f"[TEST ERROR] No messages received by server, client.received_messages: {client.received_messages}"
    assert received_messages[0] == expected_message, f"[TEST ERROR] Wrong message received: {received_messages}"

    client.close()

def test_client_receive_messages():
    """
    Test receiving messages from the server.
    """
    expected_message = "Hello, client!"
    host, port, _ = start_mock_server(expected_message, expect_client_message=False)  # Don't wait for client message

    client = start_client(host, port)
    client.start()

    # Wait for message to be received
    max_retries = 10
    retry_interval = 0.2
    received = False
    
    for _ in range(max_retries):
        time.sleep(retry_interval)
        if expected_message in client.received_messages:
            received = True
            break

    print(f"[TEST DEBUG] Final received messages: {client.received_messages}")

    assert received, f"[TEST ERROR] Client did not receive expected message within timeout. Messages received: {client.received_messages}"
    assert expected_message in client.received_messages

    client.close()

def test_client_close():
    """
    Test closing the client connection.
    """
    host, port, _ = start_mock_server()
    client = start_client(host, port)
    client.connect()

    client.close()
    time.sleep(1) # Wait for the connection to close
    
    assert not client.running
    assert client.thread is None
    assert client.socket is None
    assert client.received_messages == []


