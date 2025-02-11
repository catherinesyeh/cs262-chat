import config
from network import ChatClient
from ui import ChatUI
import tkinter as tk
import sys

def main():
    print("Starting client...")
    client_config = config.get_config()
    host = client_config["host"]
    port = client_config["port"]
    max_msg = client_config["max_msg"]
    max_users = client_config["max_users"]
    use_json_protocol = client_config["use_json_protocol"]

    # Set up a ChatClient instance and connect to the server
    print(f"Configuration: \nhost={host}, \nport={port}, \nmax_msg={max_msg}, \nmax_users={max_users}, \nuse_json_protocol={use_json_protocol}")
    client = ChatClient(host, port, max_msg, max_users, use_json_protocol)

    # Start the user interface, passing in existing client
    root = tk.Tk()
    ChatUI(root, client)
    root.mainloop()

if __name__ == "__main__":
    main()