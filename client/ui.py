import tkinter as tk
from tkinter import messagebox, scrolledtext 
import threading

class ChatUI:
    """
    Handles the user interface for the chat application.
    """

    def __init__(self, root, client):
        """
        Initialize the user interface.

        :param root: The Tkinter root window
        :param client: The ChatClient instance
        """
        self.root = root
        self.client = client

        # Keep track of current pages for list accounts and messages
        self.current_user_page = 0
        self.current_msg_page = 0

        # Start on the login screen
        self.root.title("Login")
        self.create_login_screen()
    
    ### LOGIN + ACCOUNT CREATION WORKFLOW ###
    def create_login_screen(self):
        """
        Create the login screen.
        """
        self.clear_window()

        frame = tk.Frame(self.root, padx=10, pady=20)  # Add padding around the frame
        frame.pack(expand=True)

        tk.Label(frame, text="Enter Username:").pack(pady=5)
        self.username_entry = tk.Entry(frame)
        self.username_entry.pack(padx=10, pady=5, fill=tk.X)

         # Explicitly set focus to the username entry field
        self.username_entry.focus_set()

        self.check_button = tk.Button(frame, text="Continue", command=self.check_username)
        self.check_button.pack(pady=10)

        # Bind the Enter key to trigger the Continue button
        self.username_entry.bind("<Return>", lambda event: self.check_button.invoke())

    def check_username(self):
        """
        Checks if the username exists and prompts for the next step.
        """
        username = self.username_entry.get().strip()

        if not username:
            messagebox.showerror("Error", "Username cannot be empty.")
            return

        # Check if the username exists
        lookup_result = self.client.lookup_account(username)

        if lookup_result:
            # Username exists, prompt for password to log in
            self.prompt_password(username, login=True)
        else:
            # Username does not exist, prompt for password to create an account
            self.prompt_password(username, login=False)

    def prompt_password(self, username, login=True):
        """
        Prompts for a password after username check.

        :param username: The username to log in or create an account for
        :param login: Whether to log in (True) or create an account (False)
        """
        self.clear_window()
        
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True)

        action_text = "Login" if login else "Create Account"
        tk.Label(frame, text=f"Enter Password to {action_text}:").pack(pady=5)
        
        self.password_entry = tk.Entry(frame, show="*")
        self.password_entry.pack(padx=10, pady=5, fill=tk.X)

        # Explicitly set focus to the password entry field
        self.password_entry.focus_set()

        confirm_button = tk.Button(
            frame, 
            text=action_text, 
            command=lambda: self.process_credentials(username, login)
        )
        confirm_button.pack(pady=10)

        # Bind the Enter key to trigger the Login/Create button
        self.password_entry.bind("<Return>", lambda event: confirm_button.invoke())

    def process_credentials(self, username, login):
        """
        Processes login or account creation based on user input.

        :param username: The username to log in or create an account for
        :param login: Whether to log in (True) or create an account (False)
        """
        password = self.password_entry.get().strip()

        if not password:
            messagebox.showerror("Error", "Password cannot be empty.")
            return

        # Run login or account creation in a background thread
        threading.Thread(target=self.handle_credentials, args=(username, password, login), daemon=True).start()

    def handle_credentials(self, username, password, login):
        """
        Handles login or account creation in a background thread.

        :param username: The username to log in or create an account for
        :param password: The password to use
        :param login: Whether to log in (True) or create an account (False)
        """
        if login:
            # Log in to the existing account
            print("[DEBUG] Logging in")
            result = self.client.login(username, password)
            if isinstance(result, tuple): # If sucess, result will be a tuple
                success, unread_count = result
            else:
                success, unread_count = result, None
            print(f"[DEBUG] Login result: {success}, {unread_count}")
            self.root.after(0, lambda: self.handle_login_result(success, unread_count))
        else:
            # Create a new account
            print("[DEBUG] Creating account")
            result = self.client.create_account(username, password)
            if isinstance(result, tuple): # If success, result will be a tuple
                success, _ = result
            else:
                success = result
            print(f"[DEBUG] Account creation result: {success}")
            self.root.after(0, lambda: self.handle_account_creation_result(success))

    def handle_login_result(self, success, unread_count):
        """
        Handle UI update after login.

        :param success: Whether the login was successful
        :param unread_count: The number of unread messages
        """
        if success:
            messagebox.showinfo("Login Successful", f"You have {unread_count} unread messages.")
            print("[DEBUG] Calling create_chat")
            self.create_chat_screen()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password. Please try again.")

    def handle_account_creation_result(self, success):
        """
        Handle UI update after account creation.

        :param success: Whether the account creation was successful
        """
        if success:
            messagebox.showinfo("Account Created", "Account successfully created! Logging in...")
            print("[DEBUG] Calling create_chat")
            self.create_chat_screen()
        else:
            messagebox.showerror("Error", "Failed to create an account. Please try again.")

    ### CHAT SCREEN WORKFLOW ###
    def create_chat_screen(self):
        """
        Create the main chat screen.
        """
        print("[DEBUG] In create_chat")
        self.clear_window()
        self.root.title("Chat")
        self.root.geometry("900x600")  # Larger window

        # Ensure grid layout is configured to allow resizing
        self.root.rowconfigure(1, weight=1)  # Expandable row for main chat UI
        self.root.columnconfigure(0, weight=1)  # Sidebar
        self.root.columnconfigure(1, weight=3)  # Chat window takes more space

        # Settings Toolbar (At the Top)
        settings_frame = tk.Frame(self.root, relief=tk.RAISED, bd=2, padx=5, pady=5)
        settings_frame.grid(row=0, column=0, columnspan=2, sticky="we")

        tk.Button(settings_frame, text="Log out", fg="red", command=self.disconnect).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(settings_frame, text="Delete Account", fg="red", command=self.confirm_delete_account).pack(side=tk.RIGHT, padx=5, pady=5)

        # Container to hold both sidebar and chat frame
        container = tk.Frame(self.root)
        container.grid(row=1, column=0, columnspan=2, sticky="nswe")

        container.columnconfigure(0, weight=1)  # Sidebar takes space
        container.columnconfigure(1, weight=3)  # Chat window expands more
        container.rowconfigure(0, weight=1)  # Make sure it expands

        # Sidebar for user list
        self.sidebar = tk.Frame(container, width=250, relief=tk.SUNKEN, bd=2)
        self.sidebar.grid(row=0, column=0, sticky="nswe")

        tk.Label(self.sidebar, text="Users:").pack(pady=5)
        self.user_listbox = tk.Listbox(self.sidebar, height=self.client.max_users)
        self.user_listbox.pack(fill=tk.BOTH, expand=True)

        self.user_search = tk.Entry(self.sidebar)
        self.user_search.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(self.sidebar, text="Search", command=self.load_user_list).pack(pady=2)

        self.prev_user_button = tk.Button(self.sidebar, text="Prev Page", command=lambda: self.change_user_page(-1))
        self.prev_user_button.pack(pady=2)
        self.next_user_button = tk.Button(self.sidebar, text="Next Page", command=lambda: self.change_user_page(1))
        self.next_user_button.pack(pady=2)

        # Chat frame
        self.chat_frame = tk.Frame(container)
        self.chat_frame.grid(row=0, column=1, sticky="nswe")

        self.chat_display = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, state="disabled", height=20)
        self.chat_display.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Ensure chat_display gets focus so buttons are immediately clickable
        self.chat_display.focus_set()

        # Message pagination controls
        self.pagination_frame = tk.Frame(self.chat_frame)
        self.pagination_frame.pack()

        self.prev_msg_button = tk.Button(self.pagination_frame, text="Previous Messages", command=lambda: self.change_msg_page(-1))
        self.prev_msg_button.pack(side=tk.LEFT)
        self.next_msg_button = tk.Button(self.pagination_frame, text="Next Messages", command=lambda: self.change_msg_page(1))
        self.next_msg_button.pack(side=tk.RIGHT)

        # "New Message" button
        tk.Button(self.chat_frame, text="New Message", command=self.open_new_message_window).pack(pady=10)

        self.load_user_list()
        self.load_messages()
        self.client.start_listener(self.display_message)

    ### LIST ACCOUNTS WORKFLOW ###
    def load_user_list(self):
        """
        Start a thread to fetch and display users.
        """
        threading.Thread(target=self.fetch_users, daemon=True).start()

    def fetch_users(self):
        """
        Fetch user list in a background thread.
        """
        search_text = self.user_search.get().strip()

        users = self.client.list_accounts(search_text)

        # Schedule an update to the user list
        self.root.after(0, lambda: self.update_user_list(users))
    
    def update_user_list(self, users):
        """
        Update the user list UI.

        :param users: The list of users to display
        """
        self.user_listbox.delete(0, tk.END)

        if not users:
            self.user_listbox.insert(tk.END, "No users found.")
            return
        
        self.user_listbox.insert(tk.END, *[username for _, username in users])

        # Update pagination buttons
        self.prev_user_button.config(state=tk.NORMAL if self.current_user_page > 0 else tk.DISABLED)
        self.next_user_button.config(state=tk.NORMAL if len(users) == self.client.max_users else tk.DISABLED)

    def change_user_page(self, direction):
        """
        Paginate through user list.

        :param direction: The direction to move in the user list
        """
        new_page = self.current_user_page + direction
        if new_page < 0:
            return 
        
        self.current_user_page = new_page
        print(f"Changing user page to {self.current_user_page}")
        self.load_user_list()

    ### MESSAGES WORKFLOW ###
    def load_messages(self):
        """
        Start a thread to fetch and display messages.
        """
        threading.Thread(target=self.fetch_messages, daemon=True).start()

    def fetch_messages(self):
        """
        Fetch messages.
        """
        messages = self.client.request_messages()

        # TODO: Dealing with message pagination
        print(f"Loading messages: {messages}")
        self.root.after(0, lambda: self.update_messages(messages))

    def update_messages(self, messages):
        """
        Update the chat display with messages.

        :param messages: The list of messages to display
        """
        self.chat_display.config(state="normal")
        self.chat_display.delete("1.0", tk.END)
        
        # Build the message string in one go
        chat_text = "\n".join(f"{sender}: {message}" for _, sender, message in messages)

        # Insert all at once
        self.chat_display.insert(tk.END, chat_text + "\n")

        self.chat_display.config(state="disabled")

        # Update pagination buttons
        self.prev_msg_button.config(state=tk.NORMAL if self.current_msg_page > 0 else tk.DISABLED)
        self.next_msg_button.config(state=tk.NORMAL if len(messages) == self.client.max_msg else tk.DISABLED)

    def change_msg_page(self, direction):
        """
        Paginate through messages.

        :param direction: The direction to move in the message list
        """
        self.current_msg_page += direction
        if self.current_msg_page < 0:
            self.current_msg_page = 0

        print(f"Changing message page to {self.current_msg_page}")
        self.load_messages()
    
    ### SEND MESSAGE WORKFLOW ###
    def open_new_message_window(self):
        """
        Opens a window to compose and send a new message.
        """
        new_msg_window = tk.Toplevel(self.root)
        new_msg_window.title("New Message")
        new_msg_window.geometry("400x250")

        frame = tk.Frame(new_msg_window, padx=10, pady=20)  # Add padding around the frame
        frame.pack(expand=True)

        tk.Label(new_msg_window, text="Recipient Username:").pack(pady=5)
        recipient_entry = tk.Entry(new_msg_window)
        recipient_entry.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(new_msg_window, text="Message:").pack(pady=5)
        message_entry = tk.Text(new_msg_window, height=5)
        message_entry.pack(fill=tk.BOTH, padx=10, pady=5)

        tk.Button(new_msg_window, text="Send", command=lambda: self.send_message(recipient_entry, message_entry, new_msg_window)).pack(pady=10)

    def send_message(self, recipient_entry, message_entry, new_msg_window):
        """
        Handles sending the message.

        :param recipient_entry: The entry field for the recipient
        :param message_entry: The text field for the message
        :param new_msg_window: The window to close after sending
        """
        recipient = recipient_entry.get().strip()
        message = message_entry.get("1.0", tk.END).strip()

        if not recipient or not message:
            messagebox.showerror("Error", "Recipient and message cannot be empty.")
            return
        
        # Start thread to send message
        threading.Thread(target=self.process_send_message, args=(recipient, message, new_msg_window), daemon=True).start()
    
    def process_send_message(self, recipient, message, new_msg_window):
        """
        Send the message in a background thread.

        :param recipient: The recipient of the message
        :param message: The message to send
        :param new_msg_window: The window to close after sending
        """
        success = self.client.send_message(recipient, message)
        self.root.after(0, lambda: self.handle_send_message_result(success, recipient, new_msg_window))
    
    def handle_send_message_result(self, success, recipient, new_msg_window):
        """
        Handle UI update after sending a message.

        :param success: Whether the message was sent successfully
        :param recipient: The recipient of the message
        :param new_msg_window: The window to close after sending
        """
        if success:
            messagebox.showinfo("Message Sent", f"Message to {recipient} sent successfully!")
            new_msg_window.destroy()
        else:
            messagebox.showerror("Error", "Failed to send message.")
    
    def display_message(self, message):
        """
        Display a message in the chat window.

        :param message: The message to display
        """
        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.config(state="disabled")
        self.chat_display.yview(tk.END)

    ### DELETE MESSAGE WORKFLOW ###
    def show_delete_message_window(self):
        """
        Open a window to delete messages.
        """
        delete_window = tk.Toplevel(self.root)
        delete_window.title("Delete Messages")
        delete_window.geometry("300x400")

        tk.Label(delete_window, text="Select messages to delete:").pack()
        msg_listbox = tk.Listbox(delete_window, selectmode=tk.MULTIPLE)
        msg_listbox.pack(expand=True, fill=tk.BOTH)

        # Fetch messages
        messages = self.client.request_messages()
        msg_id_map = {}  # Map UI selection to message IDs

        for idx, (msg_id, sender, message) in enumerate(messages):
            display_text = f"{sender}: {message[:30]}..."  # Display trimmed message
            msg_id_map[idx] = msg_id
            msg_listbox.insert(tk.END, display_text)

        tk.Button(delete_window, text="Delete", command=lambda: self.delete_selected_messages(msg_listbox, msg_id_map, delete_window)).pack()

    def delete_selected_messages(self, msg_listbox, msg_id_map, delete_window):
        """
        Delete selected messages.

        :param msg_listbox: The listbox containing messages
        :param msg_id_map: The mapping of listbox index to message ID
        :param delete_window: The window to close after deletion
        """
        selected_indices = msg_listbox.curselection()
        selected_msg_ids = [msg_id_map[i] for i in selected_indices]

        # Start thread to delete messages
        threading.Thread(target=self.process_delete_messages, args=(selected_msg_ids, delete_window), daemon=True).start()

    def process_delete_messages(self, selected_msg_ids, delete_window):
        """
        Process message deletion in a background thread.

        :param selected_msg_ids: The list of message IDs to delete
        :param delete_window: The window to close after deletion
        """
        success = self.client.delete_messages(selected_msg_ids)
        self.root.after(0, lambda: self.handle_delete_messages_result(success, delete_window))
    
    def handle_delete_messages_result(self, success, delete_window):
        """
        Handle UI update after deleting messages.

        :param success: Whether the messages were deleted successfully
        :param delete_window: The window to close after deletion
        """
        if success:
            messagebox.showinfo("Success", "Messages deleted successfully")
            delete_window.destroy()
        else:
            messagebox.showerror("Error", "Failed to delete messages")

    ### DELETE ACCOUNT WORKFLOW ###
    def confirm_delete_account(self):
        """
        Confirm account deletion.
        """
        confirm = messagebox.askokcancel("Confirm", "Are you sure you want to delete your account?")
        if confirm:
            # Start thread to delete account
            threading.Thread(target=self.delete_account, daemon=True).start()
        
    def delete_account(self):
        """
        Delete the account in a background thread.
        """
        success = self.client.delete_account()
        self.root.after(0, lambda: self.handle_delete_account_result(success))
    
    def handle_delete_account_result(self, success):
        """
        Handle UI update after deleting the account.

        :param success: Whether the account was deleted successfully
        """
        if success:
            messagebox.showinfo("Account Deleted", "Account deleted successfully")
            self.root.quit()
        else:
            messagebox.showerror("Error", "Failed to delete account")
    
    def disconnect(self):
        """
        Disconnect from the server.
        """
        self.client.close()
        self.root.destroy()

    def clear_window(self):
        """
        Clear the window of all widgets.
        """
        for widget in self.root.winfo_children():
            widget.destroy()