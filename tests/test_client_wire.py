# Add project root to sys.path
import struct
import time
from unittest.mock import patch, MagicMock
import pytest
import os
import sys
import json

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

from client.network.network_wire import WireChatClient
from client import config

# Test the WireChatClient class


@pytest.fixture(scope="function")
def mock_client():
    client_config = config.get_config()
    host = client_config["host"]
    port = client_config["port"]
    max_msg = client_config["max_msg"]
    max_users = client_config["max_users"]
    client = WireChatClient(host, port, max_msg, max_users)
    client.socket = MagicMock()
    client.message_callback = MagicMock()
    client.start_listener(client.message_callback)
    return client


def test_client_connect(mock_client):
    """
    Test the connect method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    assert mock_client.running == True, "Client should be running"


def test_client_close(mock_client):
    """
    Test the close method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    mock_client.close()
    assert mock_client.socket is None, "Client socket should be None"


def test_send_lookup_account(mock_client):
    """
    Test the send_lookup_account method of the WireChatClient class

    :param mock_client: A WireChatClient instance
    """
    user = "test_user"

    expected_request = struct.pack("!B B", 1, len(user)) + user.encode("utf-8")

    # Mock the listen_for_messages method so it doesn't run
    mock_client.listen_for_messages = MagicMock()

    # Call the send_lookup_account method
    mock_client.send_lookup_account("test_user")

    # Check if the sendall method was called with the expected request
    mock_client.socket.send.assert_called_with(expected_request)
