# cs262-chat

CS262 Design Exercise 1: Chat Server

This project should provide a fully functional chat system built over raw sockets.

## Setup

1. Duplicate [config_example.json](config_example.json) and rename to `config.json`.
   - Fill in your configuration details.
2. Install python dependencies for client:

```
poetry install
```

## Server

## Client

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

## Testing

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
