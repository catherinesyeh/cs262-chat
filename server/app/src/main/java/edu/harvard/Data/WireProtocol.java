package edu.harvard.Data;

import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

import edu.harvard.Data.Data.AccountLookupResponse;

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

  private static byte[] buildTwoByteInteger(int number) {
    byte[] bytes = new byte[2];
    bytes[0] = (byte) ((number >> 8) & 0xFF);
    bytes[1] = (byte) (number & 0xFF);
    return bytes;
  }

  // Loads a string into an output ByteBuffer.
  public static void loadStringToBuffer(ByteBuffer buffer, String str, int length_field_size) {
    if (length_field_size == 2) {
      buffer.put(buildTwoByteInteger(str.length()));
    }
    buffer.put((byte) ((str.length()) & 0xFF));
    for (byte b : str.getBytes(StandardCharsets.UTF_8)) {
      buffer.put(b);
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
  public byte[] generateLookupUserResponse(AccountLookupResponse internalResponse) {
    if (internalResponse.exists) {
      ByteBuffer buffer = ByteBuffer.allocate(31);
      buffer.put((byte) Operation.LOOKUP_USER.getId());
      buffer.put((byte) 1);
      buffer.put(internalResponse.bcrypt_prefix.getBytes(StandardCharsets.UTF_8));
      return buffer.array();
    } else {
      ByteBuffer buffer = ByteBuffer.allocate(2);
      buffer.put((byte) Operation.LOOKUP_USER.getId());
      buffer.put((byte) 0);
      return buffer.array();
    }
  }

  public byte[] generateLoginResponse(boolean success, int unread_messages) {
    if (success) {
      ByteBuffer buffer = ByteBuffer.allocate(4);
      buffer.put((byte) Operation.LOGIN.getId());
      buffer.put((byte) 1);
      buffer.put(buildTwoByteInteger(unread_messages));
      return buffer.array();
    } else {
      ByteBuffer buffer = ByteBuffer.allocate(2);
      buffer.put((byte) Operation.LOGIN.getId());
      buffer.put((byte) 0);
      return buffer.array();
    }
  }

  public byte[] generateCreateAccountResponse(boolean success) {
    ByteBuffer buffer = ByteBuffer.allocate(2);
    buffer.put((byte) Operation.CREATE_ACCOUNT.getId());
    buffer.put((byte) (success ? 1 : 0));
    return buffer.array();
  }

  public byte[] generateUnexpectedFailureResponse(Operation operation, String message) {
    return new byte[1];
  }
}
