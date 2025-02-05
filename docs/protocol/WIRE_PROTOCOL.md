# Wire Protocol: Chat

## General rules

All messages in this protocol support several base types:

- **Integers.** Integers have a defined length in bytes, specificed as part of the message specification. All integers are in big-endian byte order.
- **Booleans.** Booleans are 1-byte integers equal to 1 or 0.
- **Strings.** Strings are in UTF-8. Strings are NOT zero-terminated (as in C), but have a defined length stored in an integer field earlier in the message. This integer field specifies the number of characters in the string. Since strings are in UTF-8, the number of characters is equal to the number of bytes.

All messages begin with a 1-byte integer Operation ID. Each message type specified below has a unique Operation ID. The same Operation ID is used for messages from the client to the server (actions/requests) and messages from the server to the client (responses), though these message types will have different formats. The formats will be specified as "request" or "response" formats under the header for the applicable Operation ID.

## Look Up Account (Operation ID 1)

### Request

todo

### Response

todo
