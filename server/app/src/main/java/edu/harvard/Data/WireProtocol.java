package edu.harvard.Data;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public class WireProtocol implements Protocol {
  private int getFourByteInteger(InputStream stream) throws IOException {
    return java.nio.ByteBuffer.wrap(stream.readNBytes(4)).getInt();
  }

  // Gets a length-prefixed string from the input stream.
  // The length must either be a single byte or a two or four-byte big-endian
  // integer.
  private String getString(InputStream stream, int string_length) throws IOException {
    int length;
    if (string_length == 4) {
      length = getFourByteInteger(stream);
    } else if (string_length == 2) {
      length = (stream.read() << 8) + stream.read();
    } else {
      length = stream.read();
    }
    if (length > 0) {
      return new String(stream.readNBytes(length), StandardCharsets.UTF_8);
    } else {
      return "";
    }
  }

  public Request parseRequest(int operation_code, InputStream inputStream) throws ParseException {
    Operation operation = Operation.codeToOperation(operation_code);
    try {
      Request parsedRequest = new Request();
      parsedRequest.operation = operation;
      switch (operation) {
        case LOOKUP_USER:
          parsedRequest.payload = getString(inputStream, 1);
          return parsedRequest;
        case LOGIN:
        case CREATE_ACCOUNT:
          Data.LoginCreateRequest loginCreatePayload = new Data.LoginCreateRequest();
          loginCreatePayload.username = getString(inputStream, 1);
          loginCreatePayload.password_hash = getString(inputStream, 1);
          parsedRequest.payload = loginCreatePayload;
          return parsedRequest;
        case LIST_ACCOUNTS:
          Data.ListAccountsRequest listPayload = new Data.ListAccountsRequest();
          listPayload.maximum_number = inputStream.read();
          listPayload.offset_account_id = getFourByteInteger(inputStream);
          listPayload.filter_text = getString(inputStream, 1);
          parsedRequest.payload = listPayload;
          return parsedRequest;
        case SEND_MESSAGE:
          Data.SendMessageRequest sendPayload = new Data.SendMessageRequest();
          sendPayload.recipient = getString(inputStream, 1);
          sendPayload.message = getString(inputStream, 2);
          parsedRequest.payload = sendPayload;
          return parsedRequest;
        case REQUEST_MESSAGES:
          parsedRequest.payload = inputStream.read();
          return parsedRequest;
        case DELETE_MESSAGES:
          int count = inputStream.read();
          ArrayList<Integer> message_ids = new ArrayList<>(count);
          for (int i = 0; i < count; i++) {
            message_ids.add(getFourByteInteger(inputStream));
          }
          parsedRequest.payload = message_ids;
          return parsedRequest;
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
