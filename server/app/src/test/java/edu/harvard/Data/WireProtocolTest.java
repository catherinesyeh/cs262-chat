package edu.harvard.Data;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import static edu.harvard.Data.WireProtocol.loadStringToBuffer;
import edu.harvard.Data.Data.ListAccountsRequest;
import edu.harvard.Data.Data.LoginCreateRequest;
import edu.harvard.Data.Data.SendMessageRequest;
import edu.harvard.Data.Protocol.Operation;
import edu.harvard.Data.Protocol.Request;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.util.List;

public class WireProtocolTest {
  InputStream streamFromBuffer(ByteBuffer buffer) {
    return new ByteArrayInputStream(buffer.array());
  }

  Request parse(int opcode, ByteBuffer request) throws Protocol.ParseException {
    return new JSONProtocol().parseRequest(opcode, streamFromBuffer(request));
  }

  Request parseValid(int opcode, ByteBuffer request) {
    try {
      return new WireProtocol().parseRequest(opcode, streamFromBuffer(request));
    } catch (Exception ex) {
      throw new RuntimeException("Unexpecting parsing exception!");
    }
  }

  @Test
  void invalidOpcode() {
    assertThrows(Protocol.ParseException.class, () -> parse(0, ByteBuffer.allocate(1)));
  }

  @Test
  void lookupUser() {
    ByteBuffer buffer = ByteBuffer.allocate(5);
    loadStringToBuffer(buffer, "june", 1);
    Request req = parseValid(Operation.LOOKUP_USER.getId(), buffer);
    assertEquals(req.operation, Operation.LOOKUP_USER);
    assertEquals(req.payload, "june");
  }

  @Test
  void login() {
    ByteBuffer buffer = ByteBuffer.allocate(20);
    loadStringToBuffer(buffer, "june", 1);
    loadStringToBuffer(buffer, "example", 1);
    Request req = parseValid(Operation.LOGIN.getId(), buffer);
    assertEquals(req.operation, Operation.LOGIN);
    LoginCreateRequest payload = (LoginCreateRequest) req.payload;
    assertEquals(payload.username, "june");
    assertEquals(payload.password_hash, "example");
  }

  @Test
  void create() {
    ByteBuffer buffer = ByteBuffer.allocate(20);
    loadStringToBuffer(buffer, "june", 1);
    loadStringToBuffer(buffer, "example", 1);
    Request req = parseValid(Operation.CREATE_ACCOUNT.getId(), buffer);
    assertEquals(req.operation, Operation.CREATE_ACCOUNT);
    LoginCreateRequest payload = (LoginCreateRequest) req.payload;
    assertEquals(payload.username, "june");
    assertEquals(payload.password_hash, "example");
  }

  @Test
  void list() {
    ByteBuffer buffer = ByteBuffer.allocate(6);
    buffer.put((byte) 10);
    buffer.putInt(0);
    buffer.put((byte) 0);
    Request req = parseValid(Operation.LIST_ACCOUNTS.getId(), buffer);
    assertEquals(req.operation, Operation.LIST_ACCOUNTS);
    ListAccountsRequest payload = (ListAccountsRequest) req.payload;
    assertEquals(payload.maximum_number, 10);
    assertEquals(payload.offset_account_id, 0);
    assertEquals(payload.filter_text, "");
  }

  @Test
  void listWithFilter() {
    ByteBuffer buffer = ByteBuffer.allocate(10);
    buffer.put((byte) 10);
    buffer.putInt(10);
    loadStringToBuffer(buffer, "user", 1);
    Request req = parseValid(Operation.LIST_ACCOUNTS.getId(), buffer);
    assertEquals(req.operation, Operation.LIST_ACCOUNTS);
    ListAccountsRequest payload = (ListAccountsRequest) req.payload;
    assertEquals(payload.maximum_number, 10);
    assertEquals(payload.offset_account_id, 10);
    assertEquals(payload.filter_text, "user");
  }

  @Test
  void send() {
    ByteBuffer buffer = ByteBuffer.allocate(11);
    loadStringToBuffer(buffer, "june", 1);
    loadStringToBuffer(buffer, "test", 2);
    Request req = parseValid(Operation.SEND_MESSAGE.getId(), buffer);
    assertEquals(req.operation, Operation.SEND_MESSAGE);
    SendMessageRequest payload = (SendMessageRequest) req.payload;
    assertEquals(payload.recipient, "june");
    assertEquals(payload.message, "test");
  }

  @Test
  void sendLongMessage() {
    String longMessage = "1".repeat(50000);
    ByteBuffer buffer = ByteBuffer.allocate(50010);
    loadStringToBuffer(buffer, "june", 1);
    loadStringToBuffer(buffer, longMessage, 2);
    Request req = parseValid(Operation.SEND_MESSAGE.getId(), buffer);
    assertEquals(req.operation, Operation.SEND_MESSAGE);
    SendMessageRequest payload = (SendMessageRequest) req.payload;
    assertEquals(payload.recipient, "june");
    assertEquals(payload.message, longMessage);
  }

  @Test
  void requestMessages() {
    ByteBuffer buffer = ByteBuffer.allocate(1);
    buffer.put((byte) 10);
    Request req = parseValid(Operation.REQUEST_MESSAGES.getId(), buffer);
    assertEquals(req.operation, Operation.REQUEST_MESSAGES);
    assertEquals(req.payload, 10);
  }

  @SuppressWarnings("unchecked")
  @Test
  void deleteMessages() {
    ByteBuffer buffer = ByteBuffer.allocate(25);
    buffer.put((byte) 6);
    buffer.putInt(1);
    buffer.putInt(2);
    buffer.putInt(3);
    buffer.putInt(4);
    buffer.putInt(55);
    buffer.putInt(812);
    Request req = parseValid(Operation.DELETE_MESSAGES.getId(), buffer);
    assertEquals(req.operation, Operation.DELETE_MESSAGES);
    assertIterableEquals((List<Integer>) req.payload, List.of(1, 2, 3, 4, 55, 812));
  }

  @Test
  void deleteAccount() {
    ByteBuffer buffer = ByteBuffer.allocate(1);
    Request req = parseValid(Operation.DELETE_MESSAGES.getId(), buffer);
    assertEquals(req.operation, Operation.DELETE_MESSAGES);
  }
}
