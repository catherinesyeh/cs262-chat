import time 
import sys
import os
import pytest

# Add project root to sys.path
print("sys path before: ", sys.path)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
print("sys path after: ", sys.path)

from client import config
from client.network.network_json import JSONChatClient
from client.network.network_wire import WireChatClient

# -----------------------------------------------------------------------------
# Global Variables
# -----------------------------------------------------------------------------
# Global storage for received messages (accessible across tests)
received_messages = {"messages": []}

# Global callback function to store received messages
def message_callback(msg):
    print(f"[CALLBACK] Received message: {msg}")
    if msg.startswith("REQUEST_MESSAGES:"):
        msg_data = msg.split(":", 1)[1]
        messages = eval(msg_data)  # Convert string to list of message tuples
        received_messages["messages"].extend(messages)

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
@pytest.fixture(scope="module")
def sender_client():
    """
    Set up a ChatClient instance and connect to the server.
    """
    client_config = config.get_config()
    host = client_config["host"]
    port = client_config["port"]
    max_msg = client_config["max_msg"]
    max_users = client_config["max_users"]
    use_json_protocol = client_config["use_json_protocol"]
    print(f"Configuration: \nhost={host}, \nport={port}, \nmax_msg={max_msg}, \nmax_users={max_users}, \nuse_json_protocol={use_json_protocol}")

    # Create a client based on the protocol
    if use_json_protocol: 
        client = JSONChatClient(host, port, max_msg, max_users)
    else:
        client = WireChatClient(host, port, max_msg, max_users)
    
    yield client

    client.close()

@pytest.fixture(scope="module")
def receiver_client():
    """
    Set up a ChatClient instance and connect to the server.
    """
    client_config = config.get_config()
    host = client_config["host"]
    port = client_config["port"]
    max_msg = client_config["max_msg"]
    max_users = client_config["max_users"]
    use_json_protocol = client_config["use_json_protocol"]
    print(f"Configuration: \nhost={host}, \nport={port}, \nmax_msg={max_msg}, \nmax_users={max_users}, \nuse_json_protocol={use_json_protocol}")
    
    # Create a client based on the protocol
    if use_json_protocol:
        client = JSONChatClient(host, port, max_msg, max_users)
    else:
        client = WireChatClient(host, port, max_msg, max_users)

    yield client

    client.close()

@pytest.fixture(autouse=True)
def clear_received_messages():
    """
    Before each test, clear the received messages.
    """
    received_messages["messages"] = []

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------
def test_server_connection(sender_client):
    """
    Test if the client can connect to the server.
    """
    assert sender_client.running == True, "Client failed to connect to server"

def test_lookup_nonexistent_user(sender_client):
    """
    Test if the client can lookup a user that does not exist.
    """
    username = "test_user"

    sender_client.send_lookup_account(username)
    time.sleep(1) # Wait for server response

    assert sender_client.bcrypt_prefix is None, "Lookup should fail for nonexistent user"

def test_create_account(sender_client):
    """
    Test if the client can create an account.
    """
    username = "test_user"
    password = "test_password"

    # Create account
    sender_client.send_create_account(username, password)
    time.sleep(1) # Wait for server response

    # Now lookup should succeed
    sender_client.send_lookup_account(username)
    time.sleep(1) # Wait for server response

    assert sender_client.bcrypt_prefix is not None, "Lookup should succeed for created user"

def test_login(sender_client):
    """
    Test if the client can login.
    """
    username = "test_user"
    password = "test_password"

    # Login
    sender_client.send_login(username, password)
    time.sleep(1) # Wait for server response

    assert sender_client.username == username, "Login failed: Username not set correctly"

def test_send_receive_message(sender_client, receiver_client):
    """
    Test if the client can send and receive messages.
    """
    recipient = "test_receiver"
    message = "Hello, world!"

    # Attach callback to receiver client
    receiver_client.start_listener(message_callback)

    # Create recipient
    receiver_client.send_create_account(recipient, "test_password")
    time.sleep(1) # Wait for server response

    # Send message from sender to receiver
    sender_client.send_message(recipient, message)
    time.sleep(1) # Wait for server response

    # Request messages for recipient
    receiver_client.send_request_messages()
    time.sleep(1) # Wait for server response

    print(received_messages["messages"])

    # Check if message was received
    assert any(message == msg[2] for msg in received_messages["messages"]), "Message not received"

