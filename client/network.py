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

        self.last_offset_account_id = 0 # Offset ID for pagination of accounts
        self.bcrypt_prefix = None # Bcrypt prefix for password hashing
        self.username = None # Username of the client
        self.password = None # Password of the client
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

        buffer = b"" # Buffer to store incoming data for JSON messages
        while self.running:
            try:
                if self.use_json_protocol:
                    # Parse JSON messages and store them
                    chunk = self.socket.recv(1024) # Read available bytes in chunks
                    if not chunk:
                        print("[DISCONNECTED] Disconnected from server")
                        self.close()
                        break
                    buffer += chunk
                    while b'\n' in buffer: # Process each complete JSON message
                        message, buffer = buffer.split(b'\n', 1)
                        self._handle_json_response(message.decode("utf-8"))
                else:
                    # Parse custom protocol messages
                    # Try reading first byte (operation ID) first
                    op_id = self.socket.recv(1)
                    if not op_id or len(op_id) < 1:
                        print("[DISCONNECTED] Disconnected from server")
                        self.close()
                        break
                    op_id = struct.unpack("!B", op_id)[0] # Convert to integer
                    print("[OP ID]", op_id)
                    if op_id == 1: # LOOKUP_USER
                        self.handle_lookup_account_response()
                    elif op_id == 2: # LOGIN
                        self.handle_login_response()
                    elif op_id == 3: # CREATE_ACCOUNT
                        self.handle_create_account_response()
                    elif op_id == 4: # LIST_ACCOUNTS
                        self.handle_list_accounts_response()
                    elif op_id == 5: # SEND_MESSAGE
                        self.handle_send_message_response()
                    elif op_id == 6: # REQUEST_MESSAGES
                        self.handle_request_messages_response()
                    elif op_id == 7: # DELETE_MESSAGES
                        self.handle_delete_message_response() 
                    elif op_id == 8: # DELETE_ACCOUNT
                        # Note: this is potentially not needed as the socket will be automatically disconnected
                        self.handle_delete_account_response()
                    elif op_id == 255: # FAILURE
                        self._log_error("Operation failed")
                    else: # Invalid operation ID
                        self._log_error(f"[WIRE PROTOCOL] Invalid operation ID: {op_id}")
            
            except (OSError, ConnectionError) as e:
                self._log_error(f"Socket closed or connection reset. Stopping listener: {e}")
                break
            
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
        if not self.running:
            return
        self.running = False
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)  # Properly close the socket
                self.socket.close()
            except OSError:
                pass  # Ignore errors if the socket, is already closed
            self.socket = None

        # Don't try to join the thread if we're already in it
        if threading.current_thread() != self.thread and self.thread is not None:
            self.thread.join(timeout=1)

        print("[DISCONNECTED] Disconnected from server")
    
    ### MAIN OPERATIONS ###
    ### (1) LOOKUP
    def send_lookup_account(self, username):
        """
        OPERATION 1: Send a lookup account message to the server (LOOKUP_USER).

        :param username: Username to lookup
        """
        if not self.running:
           return self._log_error("Not connected to server")
            
        if self.use_json_protocol: # Use JSON protocol for lookup
            self._send_json_request("LOOKUP_USER", {"username": username})
        else: # Else, use custom protocol
            message = struct.pack("!B B", 1, len(username)) + username.encode("utf-8")
            self.socket.send(message)
        
    def handle_lookup_account_response(self):
        """
        Handle the response from the server for the LOOKUP_USER operation (1).
        """
        print("[LOOKUP] Handling response...")
        response = self.socket.recv(1) # Expected response: 1 byte exists 
        if len(response) < 1:
            return self._log_error("LOOKUP_USER Invalid response from server", None)
        
        exists = struct.unpack("!B", response)[0]
        if exists == 0:
            print("[LOOKUP] Account does not exist")
            self.bcrypt_prefix = None
        else:
            # Otherwise, account exists
            # Extract salt from response
            response = self.socket.recv(29) # Expected response: 29 byte bcrypt prefix
            if len(response) < 29:
                return self._log_error("LOOKUP_USER Invalid response from server", None)

            print("[LOOKUP] Account exists:", exists)

            salt = struct.unpack("!29s", response)[0]
            self.bcrypt_prefix = salt

        # Notify UI of lookup result
        if self.message_callback:
            self.message_callback(f"LOOKUP_USER:{exists}")
    
    def handle_lookup_account_response_json(self, payload):
        """
        Handle the JSON response from the server for the LOOKUP_USER operation (1).

        :param payload: JSON payload
        """
        print("[LOOKUP] Handling JSON response...")
        self.bcrypt_prefix = payload["bcrypt_prefix"].encode("utf-8") if payload["exists"] else None

        # Notify UI of lookup result
        if self.message_callback:
            self.message_callback(f"LOOKUP_USER:{payload['exists']}")
    
    ### (2) LOGIN
    def send_login(self, username, password):
        """
        OPERATION 2: Send a login message to the server (LOGIN).
        Assumes LOOKUP_USER has been called and account exists.

        :param username: Username to login
        :param password: Password to login
        """
        if not self.running:
            return self._log_error("Not connected to server")

        # Save username 
        self.username = username
        
        # Lookup account
        salt = self.bcrypt_prefix
        if salt is None:
            return self._log_error("Account does not exist")

        # Otherwise, account exists
        # Hash the password using the cost and salt
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)

        if self.use_json_protocol: # Use JSON protocol for login
            self._send_json_request("LOGIN", {"username": username, "password_hash": hashed_password.decode('utf-8')})
        else: # Else, use custom protocol
            message = struct.pack("!B B", 2, len(username)) + username.encode("utf-8") 
            message += struct.pack("!B", len(hashed_password)) + hashed_password
            self.socket.send(message)
        
    def handle_login_response(self):
        """
        Handle the response from the server for the LOGIN operation (2).

        :return: Tuple of success flag and unread message count if login is successful, False otherwise
        """
        response = self.socket.recv(1) # Expected response: 1 byte success
        if len(response) < 1:
            return self._log_error("LOGIN Invalid response from server", False)
        
        success = struct.unpack("!B", response)[0]

        if success == 0:
            self._log_error("Invalid credentials", False)
            unread_count = 0
        else:
            response = self.socket.recv(2) # Expected response: 2 byte unread message count
            if len(response) < 2:
                return self._log_error("LOGIN Invalid response from server", False)
            unread_count = struct.unpack("!H", response)[0]
        
        # Notify UI of login result
        if self.message_callback:
            self.message_callback(f"LOGIN:{success}:{unread_count}")
        return success, unread_count # Return the number of unread messages if login successful
    
    def handle_login_response_json(self, payload):
        """
        Handle the JSON response from the server for the LOGIN operation (2).

        :param payload: JSON payload
        :return: Tuple of success flag and unread message count if login is successful, False otherwise
        """
        # Notify UI of login result
        success = payload["success"]
        unread_messages = payload["unread_messages"]
        if self.message_callback:
            self.message_callback(f"LOGIN:{success}:{unread_messages}")
        return True, unread_messages if success else False
    
    ### (3) CREATE ACCOUNT
    def send_create_account(self, username, password):
        """
        OPERATION 3: Create a new account (CREATE_ACCOUNT).
        Assumes LOOKUP_USER has been called and account does not exist.

        :param username: Username to create
        :param password: Password to create
        """
        if not self.running:
            return self._log_error("Not connected to server", False)
    
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
        self.bcrypt_prefix = salt

        # store username and password for login later
        self.username = username
        self.password = password

        if self.use_json_protocol: # Use JSON protocol for account creation
            self._send_json_request("CREATE_ACCOUNT", {"username": username, "password_hash": hashed_password.decode('utf-8')})
        else: # Else, use custom protocol
            message = struct.pack("!B B", 3, len(username)) + username.encode("utf-8")
            message += struct.pack("!B", len(hashed_password)) + hashed_password
            self.socket.send(message)

    def handle_create_account_response(self):
        """
        Handle the response from the server for the CREATE_ACCOUNT operation (3).
        """
        response = self.socket.recv(1) # Expected response: 1 byte success
        if len(response) < 1:
            return self._log_error("CREATE_ACCOUNT Invalid response from server")
        
        success = struct.unpack("!B", response)[0]

        if success == 0:
            self._log_error("Account creation failed")

        # Notify UI of account creation result
        if self.message_callback:
            self.message_callback(f"CREATE_ACCOUNT:{success}")

        # Automatically login after account creation
        if self.username and self.password:
            self.send_login(self.username, self.password)
        else:
            self._log_error("Username and password not set")
        
    def handle_create_account_response_json(self):
        """
        Handle the JSON response from the server for the CREATE_ACCOUNT operation (3).
        """
        # Notify UI of account creation result
        if self.message_callback:
            self.message_callback(f"CREATE_ACCOUNT:{True}")
            
        # Automatically login after account creation
        if self.username and self.password:
            self.send_login(self.username, self.password)
        else:
            self._log_error("Username and password not set")
    
    ### (4) LIST ACCOUNTS
    def send_list_accounts(self, filter_text=""):
        """
        OPERATION 4: Request a list of accounts from the server (LIST_ACCOUNTS).

        :param filter_text: Filter text to search for
        """
        if not self.running:
            return self._log_error("Not connected to server")
        
        # Determine the offset ID based on the direction user wants to go
        offset_id = self.last_offset_account_id

        print("[ACCOUNTS] Offset ID:", offset_id, ", Filter:", filter_text, ", Max users:", self.max_users)
        
        if self.use_json_protocol: # Use JSON protocol for listing accounts
            self._send_json_request("LIST_ACCOUNTS", {"maximum_number": self.max_users, "offset_account_id": offset_id, "filter_text": filter_text})
        else: # Else, use custom protocol
            message = struct.pack("!B B I B", 4, self.max_users, offset_id, len(filter_text))
            message += filter_text.encode("utf-8")
            self.socket.send(message)

    def handle_list_accounts_response(self):
        """
        Handle the response from the server for the LIST_ACCOUNTS operation (4).

        :return: List of accounts
        """
        response = self.socket.recv(1) # Expected response: 1 byte number of accounts
        if len(response) < 1:
            return self._log_error("LIST_ACCOUNTS Invalid response from server")
        
        num_accounts = struct.unpack("!B", response)[0]

        accounts = []
        for _ in range(num_accounts):
            header = self.socket.recv(5) # First 5 bytes: 4 byte account ID + 1 byte username length

            if len(header) < 5:
                self._log_error("LIST_ACCOUNTS Invalid response from server")
                continue

            account_id, username_len = struct.unpack("!I B", header)

            # Extract username
            username = self.socket.recv(username_len).decode("utf-8")
            print("Username:", username)
            accounts.append((account_id, username))
        
        print(f"[ACCOUNTS] Retrieved {num_accounts} accounts")

        # Notify UI of user list update
        if self.message_callback:
            self.message_callback(f"LIST_ACCOUNTS:{json.dumps(accounts)}")
        return accounts
    
    def handle_list_accounts_response_json(self, payload):
        """
        Handle the JSON response from the server for the LIST_ACCOUNTS operation (4).

        :param payload: JSON payload
        :return: List of accounts
        """
        account_data = payload["accounts"]
        accounts = [(account["account_id"], account["username"]) for account in account_data]
        print(f"[ACCOUNTS] Retrieved {len(accounts)} accounts")

        if self.message_callback: # Notify UI of user list update
            self.message_callback(f"LIST_ACCOUNTS:{json.dumps(accounts)}")
        return accounts
    
    ### (5) SEND MESSAGE
    def send_message(self, recipient, message):
        """
        OPERATION 5: Send a message to the server (SEND_MESSAGE).

        :param recipient: Recipient of the message
        :param message: Message to send
        """
        if not self.running:
            return self._log_error("Not connected to server", False)
        
        if self.use_json_protocol: # Use JSON protocol for sending messages
            self._send_json_request("SEND_MESSAGE", {"recipient": recipient, "message": message})
        else: # Else, use custom protocol
            message_bytes = message.encode("utf-8")
            request = struct.pack("!B B", 5, len(recipient)) + recipient.encode("utf-8")
            request += struct.pack("!H", len(message_bytes)) + message_bytes
            self.socket.send(request)

    def handle_send_message_response(self):
        """
        Handle the response from the server for the SEND_MESSAGE operation (5).

        :return: True if message is sent successfully + message ID, False otherwise
        """
        response = self.socket.recv(5) # Expected response: 1 byte success + 4 byte message ID
        if len(response) < 5:
            return self._log_error("SEND_MESSAGE Invalid response from server", False)
        
        success, message_id = struct.unpack("!B I", response)

        if success == 0:
            return self._log_error("Message failed to send", False)
        
        print(f"[MESSAGE SENT] Message ID: {message_id}")
        # Notify UI of message sent
        if self.message_callback:
            self.message_callback(f"SEND_MESSAGE:{success}")
        return True, message_id # Return the message ID
    
    def handle_send_message_response_json(self, payload):
        """
        Handle the JSON response from the server for the SEND_MESSAGE operation (5).

        :param payload: JSON payload
        :return: True if message is sent successfully + message ID, False otherwise
        """
        message_id = payload["message_id"]
        print(f"[MESSAGE SENT] Message ID: {message_id}")
        # Notify UI of message sent
        if self.message_callback:
            self.message_callback(f"SEND_MESSAGE:{True}")
        return True, message_id # Return the message ID

    ### (6) REQUEST MESSAGES
    def send_request_messages(self):
        """
        OPERATION 6: Request unread messages from the server (REQUEST_MESSAGES).
        """
        if not self.running:
            return self._log_error("Not connected to server")
        
        if self.use_json_protocol: # Use JSON protocol for requesting messages
            self._send_json_request("REQUEST_MESSAGES", {"maximum_number": self.max_msg})
        else: # Else, use custom protocol
            self.socket.send(struct.pack("!B B", 6, self.max_msg)) # Request up to max messages

    def handle_request_messages_response(self):
        """
        Handle the response from the server for the REQUEST_MESSAGES operation (6).

        :return: List of messages
        """
        response = self.socket.recv(1) # Expected response: 1 byte num messages
        if len(response) < 1:
            return self._log_error("REQUEST_MESSAGES Invalid response from server")
        
        num_messages = struct.unpack("!B", response)[0]
        print(f"[MESSAGES] Received {num_messages} messages")

        messages = []
        for _ in range(num_messages):

            id_header = self.socket.recv(4) # Expected response: 4 byte message ID
            if len(id_header) < 4:
                self._log_error("REQUEST_MESSAGES Invalid response from server")
                continue
            message_id = struct.unpack("!I", id_header)[0]

            sender_header = self.socket.recv(1) # Expected response: 1 byte sender length
            if len(sender_header) < 1:
                self._log_error("REQUEST_MESSAGES Invalid response from server")
                continue
            sender_len = struct.unpack("!B", sender_header)[0]
            sender = self.socket.recv(sender_len).decode("utf-8")

            message_header = self.socket.recv(2) # Expected response: 2 byte message length
            if len(message_header) < 2:
                self._log_error("REQUEST_MESSAGES Invalid response from server")
                continue
            message_len = struct.unpack("!H", message_header)[0]
            message = self.socket.recv(message_len).decode("utf-8")

            print(f"[DEBUG] Sender: {sender}, Message: {message}")

            # Add message to list
            messages.append((message_id, sender, message))
            

        # print (f"[MESSAGES] Retrieved {num_messages} messages")
        # Notify UI of received messages
        if self.message_callback:
            self.message_callback(f"REQUEST_MESSAGES:{json.dumps(messages)}")
        return messages

    def handle_request_messages_response_json(self, payload):
        """
        Handle the JSON response from the server for the REQUEST_MESSAGES operation (6).

        :param payload: JSON payload
        :return: List of messages
        """
        message_data = payload["messages"]
        messages = [(message["message_id"], message["sender"], message["message"]) for message in message_data]
        # print(f"[MESSAGES] Retrieved {len(messages)} messages")
        # Notify UI of received messages
        if self.message_callback:
            self.message_callback(f"REQUEST_MESSAGES:{json.dumps(messages)}")
        return messages
    
    ### (7) DELETE MESSAGES
    def send_delete_message(self, message_ids):
        """
        OPERATION 7: Delete messages from the server (DELETE_MESSAGES).

        :param message_ids: List of message IDs to delete
        """
        if not self.running:
            return self._log_error("Not connected to server", False)
        
        num_messages = len(message_ids)
        if num_messages == 0:
            return self._log_error("No messages to delete", False)
        
        if self.use_json_protocol: # Use JSON protocol for deleting messages
            self._send_json_request("DELETE_MESSAGES", {"message_ids": message_ids})
        else: # Else, use custom protocol
            request = struct.pack("!B B", 7, num_messages)
            for message_id in message_ids:
                request += struct.pack("!I", message_id)
            self.socket.send(request)

    def handle_delete_message_response(self):
        """
        Handle the response from the server for the DELETE_MESSAGES operation (7).

        :return: True if messages are deleted successfully, False otherwise
        """
        response = self.socket.recv(1) # Expected response: 1 byte success
        if len(response) < 1:
            return self._log_error("DELETE_MESSAGES Invalid response from server", False)
            
        success = struct.unpack("!B", response)[0]

        if success == 0:
            return self._log_error("Message deletion failed", False)
        
        print(f"[MESSAGE DELETED] Messages deleted successfully")
        # Notify UI of message deletion
        if self.message_callback:
            self.message_callback(f"DELETE_MESSAGES:{success}")
        return True
    
    def handle_delete_message_response_json(self):
        """
        Handle the JSON response from the server for the DELETE_MESSAGES operation (7).

        :return: True if messages are deleted successfully, False otherwise
        """
        print(f"[MESSAGE DELETED] Messages deleted successfully")
        # Notify UI of message deletion
        if self.message_callback:
            self.message_callback(f"DELETE_MESSAGES:{True}")
        return True
    
    ### (8) DELETE ACCOUNT
    def send_delete_account(self):
        """
        OPERATION 8: Delete the account from the server (DELETE_ACCOUNT).
        """
        if not self.running:
            return self._log_error("Not connected to server", False)
        
        print("[ACCOUNT DELETION] Deleting account...")
        if self.use_json_protocol: # Use JSON protocol for deleting account
            self._send_json_request("DELETE_ACCOUNT")
        else: # Else, use custom protocol
            request = struct.pack("!B", 8)
            self.socket.send(request)

    def handle_delete_account_response(self):
        """
        Handle the response from the server for the DELETE_ACCOUNT operation (8).

        :return: True if account is deleted successfully
        """
        print("[ACCOUNT DELETED] Account deleted successfully")
        # Notify UI of account deletion
        if self.message_callback:
            self.message_callback(f"DELETE_ACCOUNT:{True}")
        return True
    
    def handle_delete_account_response_json(self):
        """
        Handle the JSON response from the server for the DELETE_ACCOUNT operation (8).

        :return: True if account is deleted successfully
        """
        print("[ACCOUNT DELETED] Account deleted successfully (JSON)")
        # Notify UI of account deletion
        if self.message_callback:
            self.message_callback(f"DELETE_ACCOUNT:{True}")
        return True

    ### HELPERS ###
    def _send_json_request(self, operation, payload=None):
        """
        Send a request to the server using the JSON protocol

        :param operation: Operation name
        :param payload: Payload data
        """
        if not self.use_json_protocol: # Custom protocol is handled separately
            return None
    
        request = (json.dumps({"operation": operation, "payload": payload or {}}) + '\n').encode("utf-8")
        self.socket.send(request)

    def _handle_json_response(self, message):
        """
        Handle JSON responses from the server.

        :param message: JSON message
        :return: True if the message is handled successfully, False otherwise
        """
        try:
            parsed_message = json.loads(message)
            operation = parsed_message.get("operation")
            success = parsed_message.get("success")
            if not success:
                # Log error message if operation failed
                self._log_error(f"Operation {operation} failed: {parsed_message['message']}")

            # Else, get the payload data
            payload = parsed_message.get("payload")
            if payload is None:
                return self._log_error(f"Operation {operation} failed: No payload found")
            
            # Handle the JSON response based on the operation
            if operation == "LOOKUP_USER":
                return self.handle_lookup_account_response_json(payload)
            elif operation == "LOGIN":
                return self.handle_login_response_json(payload)
            elif operation == "CREATE_ACCOUNT":
                return self.handle_create_account_response_json()
            elif operation == "LIST_ACCOUNTS":
                return self.handle_list_accounts_response_json(payload)
            elif operation == "SEND_MESSAGE":
                return self.handle_send_message_response_json(payload)
            elif operation == "REQUEST_MESSAGES":
                return self.handle_request_messages_response_json(payload)
            elif operation == "DELETE_MESSAGES":
                return self.handle_delete_message_response_json()
            elif operation == "DELETE_ACCOUNT":
                # Note: this is potentially not needed as the socket will be automatically disconnected
                return self.handle_delete_account_response_json()
            else:
                return self._log_error(f"Unknown operation: {operation}")
        except Exception as e:
            return self._log_error(f"Error handling JSON response: {e}")

    def _log_error(self, message, return_value=None):
        """ 
        Helper method to log errors and return a default value. 

        :param message: Error message
        :param return_value: Default return value
        :return: Default return value
        """
        print(f"[ERROR] {message}")
        return return_value