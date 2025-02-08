package edu.harvard.Data;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class WireProtocol implements Protocol {
  // Gets a length-prefixed string from the input stream.
  // The length must either be a single byte or a four-byte big-endian integer.
  private String getString(InputStream stream, boolean four_bytes) throws IOException {
    int length;
    if (four_bytes) {
      length = java.nio.ByteBuffer.wrap(stream.readNBytes(4)).getInt();
    } else {
      length = stream.read();
    }
    return new String(stream.readNBytes(length), StandardCharsets.UTF_8);
  }

  public Request parseRequest(int operation_code, InputStream inputStream) throws ParseException {
    Operation operation = Operation.codeToOperation(operation_code);
    try {
      Request parsedRequest = new Request();
      parsedRequest.operation = operation;
      switch (operation) {
        case LOOKUP_USER:
          parsedRequest.payload = getString(inputStream, false);
          return parsedRequest;
        case LOGIN:
        case CREATE_ACCOUNT:
        case LIST_ACCOUNTS:
        case SEND_MESSAGE:
        case REQUEST_MESSAGES:
        case DELETE_MESSAGES:
        default:
          // DELETE_ACCOUNT or others with no payload to parse
          return parsedRequest;
      }
    } catch (IOException ex) {
      throw new ParseException("Unexpected wire protocol parsing error.");
    }
  }

  // Output building
  public byte[] generateUnexpectedFailureResponse(Operation operation, String message) {
    return new byte[1];
  }
}
