# General Chat Server Specifications

## Password hashing

Passwords are double-hashed using bcrypt. Double-hashing means that the password will be hashed both by the client and by the server. The server will use the bcrypt hash sent by the client as an input for its own hashing function. Both the client and server hash will have unique salts. Double-hashing prevents values obtained by exfiltrating the database from being used for future login, while also protecting passwords in transit.

The client can obtain the bcrypt settings needed for login by making an account lookup request; this request will return the password salt and number of bcrypt rounds to use. All password hashes will be transmitted in the standard bcrypt string format, which includes the number of rounds, salt, and hash.

## Request/Response System

Most messages from the server will be sent only as a response to a request, with one exception: a read messages response will be sent to a client when a message is sent to that client's logged in user and their connection is active.

Requests can be sent in either JSON format or the custom wire protocol. Any request sent with an opening curly bracket `{` as the first byte (`0x7b`/`123`) will be interpreted as a JSON message. (Thus `123` can never be used as an operation ID.) For spontaneous/unrequested message responses, as described above, the format used by the first request message sent over the connection by the client will be used.

## Pagination

All entities (accounts and messages) are assigned a unique integer ID, which will always be assigned in ascending order. Entities are always returned to the client ordered by ID. The highest ID received by the client in one request can then be used as the "offset ID" in the next request - the server will then return only entities with a greater ID.

## Maximum Lengths

Usernames: 256 characters (2^8)
Messages: 65536 characters (2^16)
