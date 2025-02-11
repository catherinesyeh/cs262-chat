import json
import struct
from .network import ChatClient

class WireChatClient(ChatClient):
    """
    Handles the client-side network communication for the chat application using a custom wire protocol.
    (Subclass of ChatClient)
    """
    def listen_for_messages(self): 
        """
        Listen for messages from the server and store them.
        """
        print("[CLIENT] Listening for messages...")

        while self.running:
            try:
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
                    self.log_error("Operation failed")
                else: # Invalid operation ID
                    self.log_error(f"[WIRE PROTOCOL] Invalid operation ID: {op_id}")
            
            except (OSError, ConnectionError) as e:
                self.log_error(f"Socket closed or connection reset. Stopping listener: {e}")
                break
            
            except Exception as e:
                self.log_error(f"Error receiving messages: {e}")
                self.close()
                break

    ### (1) LOOKUP
    def send_lookup_account(self, username):
        """
        OPERATION 1: Send a lookup account message to the server (LOOKUP_USER).

        :param username: Username to lookup
        """
        self.check_not_connected_error()
            
        message = struct.pack("!B B", 1, len(username)) + username.encode("utf-8")
        self.socket.send(message)
    
    def handle_lookup_account_response(self):
        """
        Handle the response from the server for the LOOKUP_USER operation (1).
        """
        print("[LOOKUP] Handling response...")
        response = self.socket.recv(1) # Expected response: 1 byte exists 
        if len(response) < 1:
            return self.log_error("LOOKUP_USER Invalid response from server", None)
        
        exists = struct.unpack("!B", response)[0]
        if exists == 0:
            print("[LOOKUP] Account does not exist")
            self.bcrypt_prefix = None
        else:
            # Otherwise, account exists
            # Extract salt from response
            response = self.socket.recv(29) # Expected response: 29 byte bcrypt prefix
            if len(response) < 29:
                return self.log_error("LOOKUP_USER Invalid response from server", None)

            print("[LOOKUP] Account exists:", exists)

            salt = struct.unpack("!29s", response)[0]
            self.bcrypt_prefix = salt

        # Notify UI of lookup result
        if self.message_callback:
            self.message_callback(f"LOOKUP_USER:{exists}")
    
    ### (2) LOGIN
    def send_login(self, username, password):
        """
        OPERATION 2: Send a login message to the server (LOGIN).
        Assumes LOOKUP_USER has been called and account exists.

        :param username: Username to login
        :param password: Password to login
        """
        self.check_not_connected_error()

        hashed_password = self.get_hashed_password_for_login(username, password)

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
            return self.log_error("LOGIN Invalid response from server", False)
        
        success = struct.unpack("!B", response)[0]

        if success == 0:
            self.log_error("Invalid credentials", False)
            unread_count = 0
        else:
            response = self.socket.recv(2) # Expected response: 2 byte unread message count
            if len(response) < 2:
                return self.log_error("LOGIN Invalid response from server", False)
            unread_count = struct.unpack("!H", response)[0]
        
        # Notify UI of login result
        if self.message_callback:
            self.message_callback(f"LOGIN:{success}:{unread_count}")
        return success, unread_count # Return the number of unread messages if login successful

    ### (3) CREATE ACCOUNT
    def send_create_account(self, username, password):
        """
        OPERATION 3: Create a new account (CREATE_ACCOUNT).
        Assumes LOOKUP_USER has been called and account does not exist.

        :param username: Username to create
        :param password: Password to create
        """
        self.check_not_connected_error()
    
        hashed_password = self.generate_hashed_password_for_create(username, password)

        message = struct.pack("!B B", 3, len(username)) + username.encode("utf-8")
        message += struct.pack("!B", len(hashed_password)) + hashed_password
        self.socket.send(message)
    
    def handle_create_account_response(self):
        """
        Handle the response from the server for the CREATE_ACCOUNT operation (3).
        """
        response = self.socket.recv(1) # Expected response: 1 byte success
        if len(response) < 1:
            return self.log_error("CREATE_ACCOUNT Invalid response from server")
        
        success = struct.unpack("!B", response)[0]

        if success == 0:
            self.log_error("Account creation failed")

        # Notify UI of account creation result
        if self.message_callback:
            self.message_callback(f"CREATE_ACCOUNT:{success}")

        # Automatically login after account creation
        if self.username and self.password:
            self.send_login(self.username, self.password)
        else:
            self.log_error("Username and password not set")

    ### (4) LIST ACCOUNTS
    def send_list_accounts(self, filter_text=""):
        """
        OPERATION 4: Request a list of accounts from the server (LIST_ACCOUNTS).

        :param filter_text: Filter text to search for
        """
        self.check_not_connected_error()
        
        # Determine the offset ID based on the direction user wants to go
        offset_id = self.last_offset_account_id

        print("[ACCOUNTS] Offset ID:", offset_id, ", Filter:", filter_text, ", Max users:", self.max_users)
        
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
            return self.log_error("LIST_ACCOUNTS Invalid response from server")
        
        num_accounts = struct.unpack("!B", response)[0]

        accounts = []
        for _ in range(num_accounts):
            header = self.socket.recv(5) # First 5 bytes: 4 byte account ID + 1 byte username length

            if len(header) < 5:
                self.log_error("LIST_ACCOUNTS Invalid response from server")
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
    
    ### (5) SEND MESSAGE
    def send_message(self, recipient, message):
        """
        OPERATION 5: Send a message to the server (SEND_MESSAGE).

        :param recipient: Recipient of the message
        :param message: Message to send
        """
        self.check_not_connected_error()
        
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
            return self.log_error("SEND_MESSAGE Invalid response from server", False)
        
        success, message_id = struct.unpack("!B I", response)

        if success == 0:
            return self.log_error("Message failed to send", False)
        
        print(f"[MESSAGE SENT] Message ID: {message_id}")
        # Notify UI of message sent
        if self.message_callback:
            self.message_callback(f"SEND_MESSAGE:{success}")
        return True, message_id # Return the message ID
    
    ### (6) REQUEST MESSAGES
    def send_request_messages(self):
        """
        OPERATION 6: Request unread messages from the server (REQUEST_MESSAGES).
        """
        self.check_not_connected_error()
        
        self.socket.send(struct.pack("!B B", 6, self.max_msg)) # Request up to max messages

    def handle_request_messages_response(self):
        """
        Handle the response from the server for the REQUEST_MESSAGES operation (6).

        :return: List of messages
        """
        response = self.socket.recv(1) # Expected response: 1 byte num messages
        if len(response) < 1:
            return self.log_error("REQUEST_MESSAGES Invalid response from server")
        
        num_messages = struct.unpack("!B", response)[0]
        print(f"[MESSAGES] Received {num_messages} messages")

        messages = []
        for _ in range(num_messages):

            id_header = self.socket.recv(4) # Expected response: 4 byte message ID
            if len(id_header) < 4:
                self.log_error("REQUEST_MESSAGES Invalid response from server")
                continue
            message_id = struct.unpack("!I", id_header)[0]

            sender_header = self.socket.recv(1) # Expected response: 1 byte sender length
            if len(sender_header) < 1:
                self.log_error("REQUEST_MESSAGES Invalid response from server")
                continue
            sender_len = struct.unpack("!B", sender_header)[0]
            sender = self.socket.recv(sender_len).decode("utf-8")

            message_header = self.socket.recv(2) # Expected response: 2 byte message length
            if len(message_header) < 2:
                self.log_error("REQUEST_MESSAGES Invalid response from server")
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
    
     ### (7) DELETE MESSAGES
    def send_delete_message(self, message_ids):
        """
        OPERATION 7: Delete messages from the server (DELETE_MESSAGES).

        :param message_ids: List of message IDs to delete
        """
        self.check_not_connected_error()
        
        num_messages = len(message_ids)
        if num_messages == 0:
            return self.log_error("No messages to delete", False)
        
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
            return self.log_error("DELETE_MESSAGES Invalid response from server", False)
            
        success = struct.unpack("!B", response)[0]

        if success == 0:
            return self.log_error("Message deletion failed", False)
        
        print(f"[MESSAGE DELETED] Messages deleted successfully")
        # Notify UI of message deletion
        if self.message_callback:
            self.message_callback(f"DELETE_MESSAGES:{success}")
        return True
    
    ### (8) DELETE ACCOUNT
    def send_delete_account(self):
        """
        OPERATION 8: Delete the account from the server (DELETE_ACCOUNT).
        """
        self.check_not_connected_error()
        
        print("[ACCOUNT DELETION] Deleting account...")
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
            self.message_callback(f"DELETE_ACCOUNT:{1}") # success
        return True