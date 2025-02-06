import tkinter as tk
from tkinter import messagebox, scrolledtext 

class ChatUI:
    """
    Handles the user interface for the chat application.
    """

    def __init__(self, root, client):
        """
        Initialize the user interface.
        """
        self.root = root
        self.client = client

        # Keep track of current pages for list accounts and messages
        self.current_user_page = 0
        self.current_msg_page = 0

        # Start on the login screen
        self.root.title("Login")
        self.create_login_screen()
    
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
        """Checks if the username exists and prompts for the next step."""
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
        """Prompts for a password after username check."""
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
        """Processes login or account creation based on user input."""
        password = self.password_entry.get().strip()

        if not password:
            messagebox.showerror("Error", "Password cannot be empty.")
            return

        if login:
            # Log in to the existing account
            success, unread_count = self.client.login(username, password)
            if success:
                messagebox.showinfo("Login Successful", f"You have {unread_count} unread messages.")
                self.create_chat_screen()
            else:
                messagebox.showerror("Login Failed", unread_count)
        else:
            # Create a new account
            success, message = self.client.create_account(username, password)
            if success:
                messagebox.showinfo("Account Created", "You can now log in!")
                self.create_login_screen()
            else:
                messagebox.showerror("Error", message)

    def create_chat_screen(self):
        """
        Create the main chat screen.
        """
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

        tk.Button(settings_frame, text="Disconnect", fg="red", command=self.disconnect).pack(side=tk.LEFT, padx=5, pady=5)
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


    def load_user_list(self):
        """Fetch and display a paginated list of users."""
        search_text = self.user_search.get().strip()

        users = self.client.list_accounts(self.client.max_users, self.current_user_page * self.client.max_users, search_text)
        
        self.user_listbox.delete(0, tk.END)

        if not users:
            self.user_listbox.insert(tk.END, "No users found.")
            return

        for _, username in users:
            self.user_listbox.insert(tk.END, username)

        # Update pagination buttons
        self.prev_user_button.config(state=tk.NORMAL if self.current_user_page > 0 else tk.DISABLED)
        self.next_user_button.config(state=tk.NORMAL if len(users) == self.client.max_users else tk.DISABLED)

    def change_user_page(self, direction):
        """Paginate through user list."""
        new_page = self.current_user_page + direction
        if new_page < 0:
            return 
        
        self.current_user_page = new_page
        self.load_user_list()

    def load_messages(self):
        """Fetch and display a paginated list of messages."""
        messages = self.client.request_messages(self.client.max_msg, self.current_msg_page * self.client.max_msg)

        print(f"Loading messages: {messages}")

        self.chat_display.config(state="normal")
        self.chat_display.delete("1.0", tk.END)

        for _, sender, message in messages:
            self.chat_display.insert(tk.END, f"{sender}: {message}\n")

        self.chat_display.config(state="disabled")

        # Update pagination buttons
        self.prev_msg_button.config(state=tk.NORMAL if self.current_msg_page > 0 else tk.DISABLED)
        self.next_msg_button.config(state=tk.NORMAL if len(messages) == self.client.max_msg else tk.DISABLED)

    def change_msg_page(self, direction):
        """Paginate through messages."""
        self.current_msg_page += direction
        if self.current_msg_page < 0:
            self.current_msg_page = 0

        print(f"Changing message page to {self.current_msg_page}")
        self.load_messages()
    
    def open_new_message_window(self):
        """Opens a window to compose and send a new message."""
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

        def send_message():
            """Handles sending the message."""
            recipient = recipient_entry.get().strip()
            message = message_entry.get("1.0", tk.END).strip()

            if not recipient or not message:
                messagebox.showerror("Error", "Recipient and message cannot be empty.")
                return

            success = self.client.send_message(recipient, message)
            if success:
                messagebox.showinfo("Message Sent", f"Message to {recipient} sent successfully!")
                new_msg_window.destroy()
            else:
                messagebox.showerror("Error", "Failed to send message.")

        tk.Button(new_msg_window, text="Send", command=send_message).pack(pady=10)
    
    def display_message(self, message):
        """
        Display a message in the chat window.
        """
        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.config(state="disabled")
        self.chat_display.yview(tk.END)

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

        def delete_selected_messages():
            """Delete selected messages."""
            selected_indices = msg_listbox.curselection()
            selected_msg_ids = [msg_id_map[i] for i in selected_indices]

            if self.client.delete_messages(selected_msg_ids):
                messagebox.showinfo("Success", "Messages deleted successfully")
                delete_window.destroy()
            else:
                messagebox.showerror("Error", "Failed to delete messages")

        tk.Button(delete_window, text="Delete", command=delete_selected_messages).pack()

    def confirm_delete_account(self):
        """
        Confirm account deletion.
        """
        confirm = messagebox.askokcancel("Confirm", "Are you sure you want to delete your account?")
        if confirm:
            if self.client.delete_account():
                messagebox.showinfo("Account Deleted", "Account deleted successfully")
                self.root.quit()
            else:
                messagebox.showerror("Error", "Failed to delete account")
    
    def disconnect(self):
        """
        Disconnect from the server.
        """
        self.client.close()
        self.root.quit()

    def clear_window(self):
        """
        Clear the window of all widgets.
        """
        for widget in self.root.winfo_children():
            widget.destroy()