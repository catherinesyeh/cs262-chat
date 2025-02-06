# General Chat Client Specifications

## Connection handling

The chat client establishes a TCP socket connection to the server, which persists for the session.
The connection is specified via a configuration file: e.g., [config_example.json](../config_example.json).

## User interface

The client provides a simple graphical interface with these key views:

- **Login screen:** where the user enters their username and password to create an account or login.
- **Chat window:**
  - Sidebar with searchable list of users
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
