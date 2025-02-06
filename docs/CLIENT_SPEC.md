# General Chat Client Specifications

## Main files

All client-related files are in the [client/](../client/) folder.

- [client.py](../client/client.py): Main program to run chat client
- [config.py](../client/config.py): Reads in details from config file to initialize client
- [network.py](../client/network.py): Handles the client-side network communication for the chat application
  - [mock_network](../client/mock_network.py): A mock version of `network.py` that doesn't require a server (for testing purposes only)
- [ui.py](../client/ui.py): Handles the user interface for the chat application

## Connection handling

The chat client establishes a TCP socket connection to the server, which persists for the session.
The connection is specified via a configuration file: e.g., [config_example.json](../config_example.json).

## User interface

The client provides a simple graphical interface with these key views:

- **Login screen:** where the user enters their username and password to create an account or login.
- **Chat window:**
  - Sidebar with searchable list of users
    - Sorted into pages that the user can navigate between, with `MAX_USERS_TO_DISPLAY` messages on each page
    - Each user's status (active or inactive) is displayed
  - List of messages, ordered by most recent first
    - Sorted into pages that the user can navigate between, with `MAX_MSG_TO_DISPLAY` messages on each page
    - Message status (read or unread) is displayed
    - User can select message(s) to delete
  - Message window
    - Displays currently message user is reading **OR**
    - New message user is composing to send to someone else.
  - Settings toolbar
    - User can delete their account here **OR**
    - Log out of their account
