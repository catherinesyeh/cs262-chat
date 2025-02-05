# Wire Protocol: Chat

## General rules

All messages in this protocol support several base types:

- **Integers.** Integers have a defined length in bytes, specificed as part of the message specification. All integers are in big-endian byte order.
- **Booleans.** Booleans are 1-byte integers equal to 1 or 0.
- **Strings.** Strings are in UTF-8. Strings are NOT zero-terminated (as in C), but have a defined length stored in an integer field earlier in the message. This integer field specifies the number of characters in the string. Since strings are in UTF-8, the number of characters is equal to the number of bytes.

All messages begin with a 1-byte integer Operation ID. Each message type specified below has a unique Operation ID. The same Operation ID is used for messages from the client to the server (actions/requests) and messages from the server to the client (responses), though these message types will have different formats. The formats will be specified as "request" or "response" formats under the header for the applicable Operation ID.

### Versioning

If an operation's message specification is updated, the updated version of the operation must be assigned a new ID.

## Look Up Account (Operation ID 1)

### Request

- Operation ID (1 byte integer)
- Username Length (1 byte integer)
- Username (String)

### Response

- Operation ID (1 byte integer)
- Account Exists (Boolean/1 byte integer)
  - 0: no account exists
  - 1: account exists

The remaining fields will be sent only if the account exists:

- Bcrypt Cost (1 byte integer)
- Bcrypt Salt (16 bytes)

## Log In (Operation ID 2)

### Request

- Operation ID (1 byte integer)
- Username Length (1 byte integer)
- Username (String)
- Password Hash Length (1 byte integer)
- Password Hash (String - bcrypt password hash)

### Response

- Operation ID (1 byte integer)
- Success (Boolean/1 byte integer)

## Create Account (Operation ID 3)

_Note: when creating an account a user's socket will automatically be associated with the newly created account. No subsequent login is required._

### Request

- Operation ID (1 byte integer)
- Username Length (1 byte integer)
- Username (String)
- Password Hash Length (1 byte integer)
- Password Hash (String - bcrypt password hash)

_Note: The cost and salt will be determined by the server based on the password hash, which is a string in bcrypt format and thus contains these values._

### Response

- Operation ID (1 byte integer)
- Success (Boolean/1 byte integer)

## List accounts (Operation ID 4)

### Request

- Operation ID (1 byte integer)
- Maximum number of accounts to list (1 byte integer)
- Offset account ID (4 byte integer)
- Filter text length (1 byte integer)
  - Set to 0 when no filtering is requested.
- Filter text (string)
  - Filters the returned accounts to only those whose usernames match the format `*[text]*`

### Response

- Operation ID (1 byte integer)
- Number of accounts (1 byte integer)
- For each account:
  - Account ID (4 byte integer)
  - Username length (1 byte integer)
  - Username (String)
