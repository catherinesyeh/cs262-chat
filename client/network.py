import socket
import threading
import bcrypt
import struct
import json

class ChatClient:
    """
    Handles the client-side network communication for the chat application.
    """
    def __init__(self, host, port, max_msg, max_users, use_json_protocol):
        """
        Initialize the client.

        :param host: Server host
        :param port: Server port
        :param max_msg: Maximum number of messages to display
        :param max_users: Maximum number of users to display
        :param use_json_protocol: Flag to indicate if JSON protocol is used
        """
        self.host = host # Server host
        self.port = port # Server port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a TCP socket
        self.running = False # Flag to indicate if the client is running
        self.thread = None # Thread to listen for messages from the server
        self.use_json_protocol = use_json_protocol # Flag to indicate if JSON protocol is used (true: JSON, false: custom)

        self.received_messages = [] # List of received messages
        self.max_msg = max_msg # Maximum number of messages to display
        self.max_users = max_users # Maximum number of users to display
        self.message_callback = None # Callback function to handle received messages
        print("[INITIALIZED] Client initialized")
        self.connect()
    
    def connect(self):
        """ 
        Establish a connection to the server.

        :return: True if connection is successful, False otherwise
        """
        try:
            self.socket.connect((self.host, self.port))
            self.running = True
            print(f"[CONNECTED] Connected to {self.host}:{self.port}")
        except Exception as e:
            return self._log_error(f"Could not connect to {self.host}:{self.port} - {e}", False)
        return True
    

    def listen_for_messages(self): 
        """
        Listen for messages from the server and store them.
        """
        print("[CLIENT] Listening for messages...")
        while self.running:
            try:
                self.request_messages()
            except Exception as e:
                self._log_error(f"Error receiving messages: {e}")
                self.close()
                break

    def start_listener(self, callback):
        """
        Start a thread to listen for messages from the server.

        :param callback: Callback function to handle received messages
        """
        self.message_callback = callback
        self.thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        self.thread.start()

    def close(self):
        """
        Close the connection to the server.
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        if self.socket:
            self.socket.close()
            self.socket = None
        self.received_messages.clear()
        print("[DISCONNECTED] Disconnected from server")
    
    # Main operations
    def lookup_account(self, username):
        """
        OPERATION 1: Send a lookup account message to the server (LOOKUP_USER).

        :param username: Username to lookup
        :return: Tuple of bcrypt cost and salt if account exists, None otherwise
        """
        if not self.running:
           return self._log_error("Not connected to server")
            
        if self.use_json_protocol: # Use JSON protocol for lookup
            response = self._send_json_request("LOOKUP_USER", {"username": username}, error_message="Account lookup failed")
            # Extract cost and salt from JSON response if account exists
            payload = response["payload"]
            return (payload["bcrypt_prefix"]) if payload["exists"] else None

        # Else, use custom protocol
        # Send lookup request to server (Operation ID 1)
        message = struct.pack("!B B", 1, len(username)) + username.encode("utf-8")
        self.socket.send(message)
        response = self.socket.recv(19) # Expected response: 1 byte op ID + 1 byte exists + 1 byte cost + 16-byte salt

        _, exists = struct.unpack("!B B", response[:2])

        if exists == 0:
            return None # Account does not exist
        
        # Otherwise, account exists
        # Extract cost and salt from response
        cost, salt = struct.unpack("!B 29s", response[2:])
        return cost, salt

    
    def login(self, username, password):
        """
        OPERATION 2: Send a login message to the server (LOGIN).

        :param username: Username to login
        :param password: Password to login
        :return: Tuple of success flag and unread message count if login is successful
        """
        if not self.running:
            return self._log_error("Not connected to server")
        
        # Lookup account
        salt = self.lookup_account(username)
        if salt is None:
            return self._log_error("Account does not exist")

        # Otherwise, account exists
        # Hash the password using the cost and salt
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt.encode("utf-8"))

        if self.use_json_protocol: # Use JSON protocol for login
            response = self._send_json_request("LOGIN", {"username": username, "password_hash": hashed_password.decode('utf-8')}, error_message="Invalid credentials")
            payload = response["payload"]
            return True, payload["unread_messages"]

        # Else, use custom protocol
        # Send login request to server (Operation ID 2)
        message = struct.pack("!B B", 2, len(username)) + username.encode("utf-8") 
        message += struct.pack("!B", len(hashed_password)) + hashed_password
        self.socket.send(message)

        response = self.socket.recv(4) # Expected response: 1 byte op ID + 1 byte success + 2 byte unread count

        _, success, unread_count = struct.unpack("!B B H", response)
        if success == 0:
            self._log_error("Invalid credentials", False)
        return True, unread_count # Return the number of unread messages if login successful
    
    def create_account(self, username, password):
        """
        OPERATION 3: Create a new account (CREATE_ACCOUNT).

        :param username: Username to create
        :param password: Password to create
        :return: True if account is created successfully, False otherwise
        """
        if not self.running:
            return self._log_error("Not connected to server", False)
        
        # Lookup account to check if it already exists
        if self.lookup_account(username):
            return self._log_error("Account already exists", False)
        
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)

        if self.use_json_protocol: # Use JSON protocol for account creation
            response = self._send_json_request("CREATE_ACCOUNT", {"username": username, "password_hash": hashed_password.decode('utf-8')}, error_message="Account creation failed")
            return True # Account created successfully

        # Else, use custom protocol
        # Send create account request to server (Operation ID 3)
        message = struct.pack("!B B", 3, len(username)) + username.encode("utf-8")
        message += struct.pack("!B", len(hashed_password)) + hashed_password
        self.socket.send(message)

        response = self.socket.recv(2) # Expected response: 1 byte op ID + 1 byte success
        _, success = struct.unpack("!B B", response)

        if success == 0:
            return self._log_error("Account creation failed", False)
        return True # Account created successfully
    
    def list_accounts(self, offset_id=0, filter_text=""):
        """
        OPERATION 4: Request a list of accounts from the server (LIST_ACCOUNTS).

        :param offset_id: Offset ID for pagination
        :param filter_text: Filter text to search for
        :return: List of accounts
        """
        if not self.running:
            return self._log_error("Not connected to server")
        
        if self.use_json_protocol: # Use JSON protocol for listing accounts
            response = self._send_json_request("LIST_ACCOUNTS", {"maximum_number": self.max_users, "offset_id": offset_id, "filter_text": filter_text}, error_message="Could not retrieve accounts")
            account_data = response["payload"]["accounts"]
            accounts = [(account["account_id"], account["username"]) for account in account_data]
            print(f"[ACCOUNTS] Retrieved {len(accounts)} accounts")
            return accounts

        # Else, use custom protocol
        # Send list accounts request to server (Operation ID 4)
        message = struct.pack("!B B I B", 4, self.max_users, offset_id, len(filter_text))
        message += filter_text.encode("utf-8")
        self.socket.send(message)

        response = self.socket.recv(2) # Expected response: 1 byte op ID + 1 byte number of accounts
        _, num_accounts = struct.unpack("!B B", response)

        accounts = []
        for _ in range(num_accounts):
            header = self.socket.recv(5) # First 5 bytes: 4 byte account ID + 1 byte username length
            account_id, username_len = struct.unpack("!I B", header)

            # Extract username
            username = self.socket.recv(username_len).decode("utf-8")
            accounts.append((account_id, username))
        
        print(f"[ACCOUNTS] Retrieved {num_accounts} accounts")
        return accounts
    
    def send_message(self, recipient, message):
        """
        OPERATION 5: Send a message to the server (SEND_MESSAGE).

        :param recipient: Recipient of the message
        :param message: Message to send
        :return: True if message is sent successfully + message ID, False otherwise
        """
        if not self.running:
            return self._log_error("Not connected to server", False)
        
        if self.use_json_protocol: # Use JSON protocol for sending messages
            response = self._send_json_request("SEND_MESSAGE", {"recipient": recipient, "message": message}, error_message="Message failed to send")
            message_id = response["payload"]["message_id"]
            print(f"[MESSAGE SENT] Message ID: {message_id}")
            return True, message_id # Return the message ID

        # Else, use custom protocol
        # Send message to server (Operation ID 5)
        message_bytes = message.encode("utf-8")
        request = struct.pack("!B B", 5, len(recipient)) + recipient.encode("utf-8")
        request += struct.pack("!H", len(message_bytes)) + message_bytes
        self.socket.send(request)

        response = self.socket.recv(6) # Expected response: 1 byte op ID + 1 byte success + 4 byte message ID
        _, success, message_id = struct.unpack("!B B I", response)

        if success == 0:
            return self._log_error("Message failed to send", False)
        
        print(f"[MESSAGE SENT] Message ID: {message_id}")
        return True, message_id # Return the message ID

    def request_messages(self):
        """
        OPERATION 6: Request unread messages from the server (REQUEST_MESSAGES).

        :return: List of messages
        """
        if not self.running:
            return self._log_error("Not connected to server")
        
        if self.use_json_protocol: # Use JSON protocol for requesting messages
            response = self._send_json_request("REQUEST_MESSAGES", {"maximum_number": self.max_msg}, error_message="Could not retrieve messages")
            message_data = response["payload"]["messages"]
            messages = [(message["message_id"], message["sender"], message["message"]) for message in message_data]
            print(f"[MESSAGES] Retrieved {len(messages)} messages")
            return messages
            
        # Else, use custom protocol
        # Send message request to server (Operation ID 6)
        self.socket.send(struct.pack("!B B", 6, self.max_msg)) # Request up to max messages

        response = self.socket.recv(2) # Expected response: 1 byte op ID + 1 byte success
        _, num_messages = struct.unpack("!B B", response)

        messages = []
        for _ in range(num_messages):
            header = self.socket.recv(7) # Expected response: 4 byte message ID + 1 byte sender length + 2 byte message length
            message_id, sender_len, message_len = struct.unpack("!I B H", header)

            # Extract sender and message
            sender = self.socket.recv(sender_len).decode("utf-8")
            message = self.socket.recv(message_len).decode("utf-8")

            # Add message to list
            messages.append((message_id, sender, message))

            if self.message_callback:
                self.message_callback(f"{sender}: {message}")

        print (f"[MESSAGES] Retrieved {num_messages} messages")
        return messages
    
    def delete_message(self, message_ids):
        """
        OPERATION 7: Delete messages from the server (DELETE_MESSAGES).

        :param message_ids: List of message IDs to delete
        :return: True if messages are deleted successfully, False otherwise
        """
        if not self.running:
            return self._log_error("Not connected to server", False)
        
        num_messages = len(message_ids)
        if num_messages == 0:
            return self._log_error("No messages to delete", False)
        
        if self.use_json_protocol: # Use JSON protocol for deleting messages
            response = self._send_json_request("DELETE_MESSAGES", {"message_ids": message_ids}, error_message="Message deletion failed")
            print(f"[MESSAGE DELETED] {num_messages} messages deleted successfully")
            return True
        
        # Else, use custom protocol
        # Send delete message request to server (Operation ID 7)
        request = struct.pack("!B B", 7, num_messages)
        for message_id in message_ids:
            request += struct.pack("!I", message_id)
        self.socket.send(request)

        response = self.socket.recv(2) # Expected response: 1 byte op ID + 1 byte success
        _, success = struct.unpack("!B B", response)

        if success == 0:
            return self._log_error("Message deletion failed", False)
        
        print(f"[MESSAGE DELETED] {num_messages} messages deleted successfully")
        return True
    
    def delete_account(self):
        """
        OPERATION 8: Delete the account from the server (DELETE_ACCOUNT).

        :return: True if account is deleted successfully, False otherwise
        """
        if not self.running:
            return self._log_error("Not connected to server", False)
        
        if self.use_json_protocol: # Use JSON protocol for deleting account
            self._send_json_request("DELETE_ACCOUNT", error_message="Account deletion failed")
            print("[ACCOUNT DELETED] Account deleted successfully")
            self.close()
            return True
        
        # Send delete account request to server (Operation ID 8)
        request = struct.pack("!B", 8)
        self.socket.send(request)

        self.socket.recv(1) # Expected response: 1 byte op ID

        print("[ACCOUNT DELETED] Account deleted successfully")
        self.close()
        return True

    # Helper methods
    def _send_json_request(self, operation, payload=None, error_message=""):
        """
        Send a request to the server using the JSON protocol

        :param operation: Operation name
        :param payload: Payload data
        :param error_message: Error message to display
        :return: JSON response from the server
        """
        if not self.use_json_protocol: # Custom protocol is handled separately
            return None
    
        request = (json.dumps({"operation": operation, "payload": payload or {}}) + '\n').encode("utf-8")
        self.socket.send(request)
        response = self.socket.makefile().readline().strip() #
        parsed_response = json.loads(response) # Parse the JSON response
        return parsed_response if parsed_response.get("success") else self._log_error(f"Operation {operation} failed: {error_message}", None)

    def _log_error(self, message, return_value=None):
        """ 
        Helper method to log errors and return a default value. 

        :param message: Error message
        :param return_value: Default return value
        :return: Default return value
        """
        print(f"[ERROR] {message}")
        return return_value