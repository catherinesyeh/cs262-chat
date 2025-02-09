package edu.harvard.Logic;

import org.junit.jupiter.api.Test;

import edu.harvard.Data.Data.AccountLookupResponse;
import edu.harvard.Data.Data.LoginCreateRequest;
import edu.harvard.Data.Data.MessageResponse;
import edu.harvard.Data.Data.SendMessageRequest;
import edu.harvard.Data.Protocol.HandleException;
import edu.harvard.Logic.OperationHandler.LoginResponse;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Arrays;

public class OperationHandlerTest {
  @Test
  void operationTest() {
    try {
      Database db = new Database();
      OperationHandler handler = new OperationHandler(db);
      // Create two accounts
      LoginCreateRequest u1 = new LoginCreateRequest();
      u1.username = "june";
      u1.password_hash = "passwordpasswordpasswordpasswordpasswordpasswordpassword";
      LoginCreateRequest u2 = new LoginCreateRequest();
      u2.username = "catherine";
      u2.password_hash = "password2passwordpasswordpasswordpasswordpasswordpassword";
      assertEquals(1, handler.createAccount(u1));
      assertEquals(2, handler.createAccount(u2));
      // Log into one
      AccountLookupResponse lookup = handler.lookupAccount("june");
      assertEquals(true, lookup.exists);
      assertEquals(29, lookup.bcrypt_prefix.length());
      LoginResponse login = handler.login(u1);
      assertEquals(true, login.success);
      assertEquals(1, login.account_id);
      assertEquals(0, login.unread_messages);
      // Send a message
      SendMessageRequest msg = new SendMessageRequest();
      msg.recipient = "catherine";
      msg.message = "Hi!";
      assertEquals(1, handler.sendMessage(1, msg));
      // Receive a message
      LoginResponse login2 = handler.login(u2);
      assertEquals(1, login2.unread_messages);
      MessageResponse m = handler.requestMessages(2, 5).get(0);
      assertEquals(1, m.id);
      assertEquals("june", m.sender);
      assertEquals(msg.message, m.message);
      // Send another message
      assertEquals(2, handler.sendMessage(1, msg));
      // Delete it
      assertEquals(false, handler.deleteMessages(3, Arrays.asList(2)));
      assertEquals(true, handler.deleteMessages(1, Arrays.asList(2)));
      // Verify that this worked
      assertEquals(0, handler.requestMessages(2, 5).size());
      // Delete an account
      handler.deleteAccount(1);
    } catch (HandleException e) {
      throw new RuntimeException(e.getMessage());
    }
  }
}
