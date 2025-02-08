# cs262-chat

CS262 Design Exercise 1: Chat Server

This project should provide a fully functional chat system built over raw sockets.

## Setup

1. Duplicate [config_example.json](config_example.json) and rename to `config.json`.
   - Fill in your configuration details.
2. Duplicate [server/config.example.properties](server/config.example.properties) and rename to `server/config.properties`.
   - Fill in your configuration details. Be sure these match!
3. Install the python dependencies for the client (this requires `poetry` to be installed):

```
poetry install
```

## Server

The server is a Java application built using Gradle. On Linux, run `./gradlew run` from the `server` directory to run the server. (On Windows, this can be replaced with `./gradlew.bat`.)

### Server Testing

Run `./gradlew test` from the `server` directory.

## Client

The client is a Python application with a Tkinter interface.

1. Navigate to [client/](client/) folder:

```
cd client
```

2. Start client:

```
poetry run python client.py
```

- To test without server, add the `-test` flag:

```
poetry run python client.py -test
```

### Client Testing

**Note: under construction right now**

1. Navigate into [tests](tests) folder:

```
cd tests
```

2. Start tests:

```
poetry run pytest
```

## Documentation

More comprehensive internal documentation (including engineering notebooks) is in the [docs/](docs/) folder.
