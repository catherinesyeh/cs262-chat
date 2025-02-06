import socket
import threading
import time

class ChatClient:
    """
    Handles the client-side network communication for the chat application.
    """
    def __init__(self, host, port):
        """
        Initialize the client.
        """
        self.host = host # Server host
        self.port = port # Server port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a TCP socket
        self.running = False # Flag to indicate if the client is running
        self.thread = None # Thread to listen for messages from the server
        self.received_messages = [] # List of received messages
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
    
    def send_message(self, message):
        """
        Send a message to the server.
        """
        if not self.running:
            print("[ERROR] Not connected to server")
            return
        try:
            self.socket.send(message.encode("utf-8"))
            print(f"[SENT] {message}")
        except Exception as e:
            print("[ERROR] Could not send message")
            print(e)

    def receive_messages(self):
        """
        Listen for messages from the server and store them.
        """
        print("[CLIENT] Listening for messages...")

        while self.running:
            try:
                print("[CLIENT] Waiting for message...")
                message = self.socket.recv(1024).decode("utf-8")  # Blocking call

                if not message:
                    print("[CLIENT ERROR] No message received, closing connection")
                    break

                self.received_messages.append(message)
                print(f"[CLIENT] Received message: {message}")  # Log received messages

            except OSError as e:
                if e.errno == 9:  # Bad file descriptor error
                    print("[CLIENT ERROR] Socket was closed unexpectedly")
                    break
                else:
                    print(f"[CLIENT ERROR] Could not receive message: {e}")
                    break

    def start(self):
        """
        Start a thread to listen for messages from the server.
        """

        if self.connect():
            self.thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.thread.start()

            if not self.thread.is_alive():
                print("[ERROR] Could not start thread to listen for messages")
                self.close()
            else: 
                print("[STARTED] Listening for messages from server")

    def close(self):
        """
        Close the connection to the server.
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        self.socket.close()
        self.socket = None
        self.received_messages.clear()
        print("[DISCONNECTED] Disconnected from server")