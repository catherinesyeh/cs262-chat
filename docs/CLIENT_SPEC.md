# General Chat Client Specifications

## Main files

All client-related files are in the [client/](../client/) folder.

- [client.py](../client/client.py): Main program to run chat client
- [config.py](../client/config.py): Reads in details from config file to initialize client
- [network.py](../client/network.py): Handles the client-side network communication for the chat application
  (implementing all required operations for the assignment on the client's side)
- [ui.py](../client/ui.py): Handles the user interface for the chat application

## Connection handling

The chat client establishes a TCP socket connection to the server, which persists for the session.
The connection is specified via a configuration file: e.g., [config_example.json](../config_example.json).

## Switching between protocols

The user can set the `USE_JSON_PROTOCOL` flag in `config.json` to determine whether the custom wire protocol
or the JSON protocol is used.

## User interface

The client provides a simple graphical interface with these key views:

- **Login screen:** where the user enters their username and password to create an account or login.
- **Chat window:** shows up once the user logs in.
  - Sidebar with searchable list of users
    - Sorted into pages that the user can navigate between, with a max of `MAX_USERS_TO_DISPLAY` messages on each page
      (editable in `config.json`)
  - List of unread messages, ordered by most recent first
    - Sorted into pages that the user can navigate between, with a max of `MAX_MSG_TO_DISPLAY` messages on each page
      (editable in `config.json`)
    - User can select message(s) to delete
  - Settings toolbar
    - User can delete their account here **OR**
    - Log out of their account
- **New message window:** opens when the user presses the _New Message_ button. This is where the user can compose a message to someone else.
  - Valid recipients are all other existing users in the system, other than the user themselves (as specified in the [SERVER_SPEC](SERVER_SPEC.md), the user cannot send a message to themselves by design).

## Error handling

Popup alerts will be displayed to the user in the UI if the system encounters an error (e.g., wrong credentials entered, invalid or empty recipient/message, etc.).

- These are also handled programatically by [network.py](../client/network.py).
