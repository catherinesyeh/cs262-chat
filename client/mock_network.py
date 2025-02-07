import sys

class MockChatClient:
    """Mock ChatClient for UI testing without a server."""

    def __init__(self, host, port, max_msg, max_users, use_json_protocol):
        self.host = host
        self.port = port
        self.max_msg = max_msg
        self.max_users = max_users
        self.use_json_protocol = use_json_protocol
        self.existing_users = {
            "alice": "hashedpassword123",
            "bob": "hashedpassword456",
            "charlie": "hashedpassword789"
        }  # Simulated user database

        self.messages = {}  # {recipient: [(message_id, sender, message)]}
        self.message_counter = 1  # Simulated message IDs

    def lookup_account(self, username):
        """Simulates checking if an account exists."""
        return (12, b'simulated_salt1234') if username in self.existing_users else None

    def login(self, username, password):
        """Simulates login process."""
        if username in self.existing_users:
            return True, 5  # Simulating 5 unread messages
        return False, "Invalid credentials"

    def create_account(self, username, password):
        """Simulates account creation."""
        if username in self.existing_users:
            return False, "Account already exists"

        self.existing_users[username] = "hashedpassword123"
        return True, "Account created successfully"

    def list_accounts(self, max_accounts=10, offset_id=0, filter_text=""):
        """Simulates listing accounts with optional filtering."""
        usernames = list(self.existing_users.keys())

        if filter_text:
            usernames = [u for u in usernames if filter_text.lower() in u.lower()]

        usernames = usernames[offset_id:offset_id + max_accounts]

        print(f"[MOCK] Listing accounts: {usernames}")

        return [(i + 1, username) for i, username in enumerate(usernames)]

    def send_message(self, recipient, message):
        """Simulates sending a message."""
        if recipient not in self.existing_users:
            return False

        if recipient not in self.messages:
            self.messages[recipient] = []

        message_id = self.message_counter
        self.message_counter += 1

        self.messages[recipient].append((message_id, "mock_sender", message))
        return True, message_id

    def request_messages(self):
        """Simulates retrieving unread messages."""
        if "mock_user" not in self.messages:
            return []

        unread_messages = self.messages["mock_user"][:self.max_msg]
        self.messages["mock_user"] = self.messages["mock_user"][self.max_msg:]

        return unread_messages

    def delete_message(self, message_ids):
        """Simulates deleting messages."""
        if "mock_user" in self.messages:
            self.messages["mock_user"] = [
                (msg_id, sender, msg) for msg_id, sender, msg in self.messages["mock_user"]
                if msg_id not in message_ids
            ]
            return True
        return False

    def delete_account(self):
        """Simulates account deletion."""
        self.existing_users.clear()
        self.messages.clear()
        self.close()

    def close(self):
        """Simulates closing the connection."""
        print("[MOCK] Client closed.")
        sys.exit(0)