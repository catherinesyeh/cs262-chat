package edu.harvard.Data;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import edu.harvard.Data.Data.ListAccountsRequest;
import edu.harvard.Data.Data.LoginCreateRequest;
import edu.harvard.Data.Data.SendMessageRequest;
import edu.harvard.Data.Protocol.Operation;
import edu.harvard.Data.Protocol.Request;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;

public class JSONProtocolTest {
  InputStream streamFromString(String string) {
    return new ByteArrayInputStream(string.substring(1).getBytes(StandardCharsets.UTF_8));
  }

  Request parse(String json) throws Protocol.ParseException {
    return new JSONProtocol().parseRequest(123, streamFromString(json));
  }

  Request parseValid(String json) {
    try {
      return new JSONProtocol().parseRequest(123, streamFromString(json));
    } catch (Exception ex) {
      throw new RuntimeException("Unexpecting parsing exception!");
    }
  }

  @Test
  void invalidJson() {
    assertThrows(Protocol.ParseException.class, () -> parse("invalid"));
  }

  @Test
  void noOperationCode() {
    assertThrows(Protocol.ParseException.class, () -> parse("{}"));
  }

  @Test
  void noPayloadWhereRequired() {
    String json = "{\"operation\":\"LOOKUP_USER\"}";
    assertThrows(Protocol.ParseException.class, () -> parse(json));
  }

  @Test
  void noRequiredField() {
    String json = "{\"operation\":\"LOOKUP_USER\", \"payload\": {}}";
    assertThrows(Protocol.ParseException.class, () -> parse(json));
  }

  @Test
  void wrongTypeRequiredField() {
    String json = "{\"operation\":\"LOOKUP_USER\", \"payload\": {\"username\": 1}}";
    assertThrows(Protocol.ParseException.class, () -> parse(json));
  }

  @Test
  void lookupUser() {
    String json = "{\"operation\":\"LOOKUP_USER\", \"payload\": {\"username\": \"june\"}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.LOOKUP_USER);
    assertEquals(req.payload, "june");
  }

  @Test
  void login() {
    String json = "{\"operation\":\"LOGIN\", \"payload\": {\"username\": \"june\", \"password_hash\": \"example\"}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.LOGIN);
    LoginCreateRequest payload = (LoginCreateRequest) req.payload;
    assertEquals(payload.username, "june");
    assertEquals(payload.password_hash, "example");
  }

  @Test
  void create() {
    String json = "{\"operation\":\"CREATE_ACCOUNT\", \"payload\": {\"username\": \"june\", \"password_hash\": \"example\"}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.CREATE_ACCOUNT);
    LoginCreateRequest payload = (LoginCreateRequest) req.payload;
    assertEquals(payload.username, "june");
    assertEquals(payload.password_hash, "example");
  }

  @Test
  void list() {
    String json = "{\"operation\":\"LIST_ACCOUNTS\", \"payload\": {\"maximum_number\": 10, \"offset_account_id\": 0}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.LIST_ACCOUNTS);
    ListAccountsRequest payload = (ListAccountsRequest) req.payload;
    assertEquals(payload.maximum_number, 10);
    assertEquals(payload.offset_account_id, 0);
    assertEquals(payload.filter_text, "");
  }

  @Test
  void listWithFilter() {
    String json = "{\"operation\":\"LIST_ACCOUNTS\", \"payload\": {\"maximum_number\": 10, \"offset_account_id\": 10, \"filter_text\": \"user\"}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.LIST_ACCOUNTS);
    ListAccountsRequest payload = (ListAccountsRequest) req.payload;
    assertEquals(payload.maximum_number, 10);
    assertEquals(payload.offset_account_id, 10);
    assertEquals(payload.filter_text, "user");
  }

  @Test
  void send() {
    String json = "{\"operation\":\"SEND_MESSAGE\", \"payload\": {\"recipient\": \"june\", \"message\": \"test\"}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.SEND_MESSAGE);
    SendMessageRequest payload = (SendMessageRequest) req.payload;
    assertEquals(payload.recipient, "june");
    assertEquals(payload.message, "test");
  }

  @Test
  void sendLongMessage() {
    String longMessage = "1".repeat(50000);
    String json = "{\"operation\":\"SEND_MESSAGE\", \"payload\": {\"recipient\": \"june\", \"message\": \""
        + longMessage + "\"}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.SEND_MESSAGE);
    SendMessageRequest payload = (SendMessageRequest) req.payload;
    assertEquals(payload.recipient, "june");
    assertEquals(payload.message, longMessage);
  }

  @Test
  void requestMessages() {
    String json = "{\"operation\":\"REQUEST_MESSAGES\", \"payload\": {\"maximum_number\": 10}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.REQUEST_MESSAGES);
    assertEquals(req.payload, 10);
  }

  @SuppressWarnings("unchecked")
  @Test
  void deleteMessages() {
    String json = "{\"operation\":\"DELETE_MESSAGES\", \"payload\": {\"message_ids\": [1,2,3,4,55,812]}}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.DELETE_MESSAGES);
    assertIterableEquals((List<Integer>) req.payload, List.of(1, 2, 3, 4, 55, 812));
  }

  @Test
  void deleteAccount() {
    String json = "{\"operation\":\"DELETE_ACCOUNT\"}";
    Request req = parseValid(json);
    assertEquals(req.operation, Operation.DELETE_ACCOUNT);
  }
}
