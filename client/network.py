import socket
import threading
import bcrypt
import struct

class ChatClient:
    """
    Handles the client-side network communication for the chat application.
    """
    def __init__(self, host, port, max_msg, max_users):
        """
        Initialize the client.
        """
        self.host = host # Server host
        self.port = port # Server port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a TCP socket
        self.running = False # Flag to indicate if the client is running
        self.thread = None # Thread to listen for messages from the server

        self.received_messages = [] # List of received messages
        self.max_msg = max_msg # Maximum number of messages to display
        self.max_users = max_users # Maximum number of users to display
        self.message_callback = None # Callback function to handle received messages
        print("[INITIALIZED] Client initialized")
    
    def connect(self):
        """ 
        Establish a connection to the server.
        """
        try:
            self.socket.connect((self.host, self.port))
            self.running = True
            print(f"[CONNECTED] Connected to {self.host}:{self.port}")
        except Exception as e:
            print(f"[ERROR] Could not connect to {self.host}:{self.port}")
            print(e)
            return False
        return True

    def lookup_account(self, username):
        """
        Send a lookup account message to the server.
        """
        # Send lookup request to server (Operation ID 1)
        message = struct.pack("!B B", 1, len(username)) + username.encode("utf-8")
        self.socket.send(message)
        response = self.socket.recv(20) # Expected response: 1 byte op ID + 1 byte exists + 1 byte cost + 16-byte salt

        _, exists = struct.unpack("!B B", response[:2])

        if exists == 0:
            return None # Account does not exist
        
        # Otherwise, account exists
        # Extract cost and salt from response
        cost, salt = struct.unpack("!B 16s", response[2:])
        return cost, salt

    
    def login(self, username, password):
        """
        Send a login message to the server.
        """
        if not self.running:
            print("[ERROR] Not connected to server")
            return False
        
        # Lookup account
        result = self.lookup_account(username)
        if result is None:
            print("[ERROR] Account does not exist")
            return False

        # Otherwise, account exists
        # Hash the password using the cost and salt
        _, salt = result
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)

        # Send login request to server (Operation ID 2)
        message = struct.pack("!B B", 2, len(username)) + username.encode("utf-8") 
        message += struct.pack("!B", len(hashed_password)) + hashed_password
        self.socket.send(message)

        response = self.socket.recv(4) # Expected response: 1 byte op ID + 1 byte success + 2 byte unread count

        _, success, unread_count = struct.unpack("!B B H", response)
        if success == 0:
            print("[ERROR] Login failed")
            return False, "Invalid credentials"
        return True, unread_count # Return the number of unread messages if login successful
    
    def create_account(self, username, password):
        """
        Create a new account.
        """
        if not self.running:
            print("[ERROR] Not connected to server")
            return False
        
        # Lookup account to check if it already exists
        if self.lookup_account(username):
            print("[ERROR] Account already exists")
            return False
        
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)

        # Send create account request to server (Operation ID 3)
        message = struct.pack("!B B", 3, len(username)) + username.encode("utf-8")
        message += struct.pack("!B", len(hashed_password)) + hashed_password
        self.socket.send(message)

        response = self.socket.recv(2) # Expected response: 1 byte op ID + 1 byte success
        _, success = struct.unpack("!B B", response)

        if success == 0:
            print("[ERROR] Account creation failed")
            return False
        return True # Account created successfully
    
    def list_accounts(self, offset_id=0, filter_text=""):
        """
        Request a list of accounts from the server.
        """
        if not self.running:
            print("[ERROR] Not connected to server")
            return

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
        Send a message to the server.
        """
        if not self.running:
            print("[ERROR] Not connected to server")
            return
        
        # Send message to server (Operation ID 5)
        message_bytes = message.encode("utf-8")
        request = struct.pack("!B B", 5, len(recipient)) + recipient.encode("utf-8")
        request += struct.pack("!H", len(message_bytes)) + message_bytes
        self.socket.send(request)

        response = self.socket.recv(6) # Expected response: 1 byte op ID + 1 byte success + 4 byte message ID
        _, success, message_id = struct.unpack("!B B I", response)

        if success == 0:
            print("[ERROR] Message failed to send")
            return False
        
        print(f"[MESSAGE SENT] Message ID: {message_id}")
        return True, message_id # Return the message ID

    def request_messages(self):
        """
        Request unread messages from the server.
        """
        if not self.running:
            print("[ERROR] Not connected to server")
            return
        
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
            print(f"[RECEIVED MESSAGE] ID: {message_id}, Sender: {sender}, Message: {message}")

            if self.message_callback:
                self.message_callback(f"{sender}: {message}")

        return messages
    
    def delete_message(self, message_ids):
        """
        Delete messages from the server.
        """
        if not self.running:
            print("[ERROR] Not connected to server")
            return
        
        num_messages = len(message_ids)
        if num_messages == 0:
            print("[ERROR] No messages to delete")
            return
        
        # Send delete message request to server (Operation ID 7)
        request = struct.pack("!B B", 7, num_messages)
        for message_id in message_ids:
            request += struct.pack("!I", message_id)
        self.socket.send(request)

        response = self.socket.recv(2) # Expected response: 1 byte op ID + 1 byte success
        _, success = struct.unpack("!B B", response)

        if success == 0:
            print("[ERROR] Message deletion failed")
            return False
        
        print(f"[MESSAGE DELETED] {num_messages} messages deleted successfully")
        return True
    
    def delete_account(self):
        """
        Delete the account from the server.
        """
        if not self.running:
            print("[ERROR] Not connected to server")
            return
        
        # Send delete account request to server (Operation ID 8)
        request = struct.pack("!B", 8)
        self.socket.send(request)

        self.socket.recv(1) # Expected response: 1 byte op ID

        print("[ACCOUNT DELETED] Account deleted successfully")
        self.close()
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
                print(f"[CLIENT ERROR] Could not receive messages: {e}")
                break

    def start_listener(self, callback):
        """
        Start a thread to listen for messages from the server.
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