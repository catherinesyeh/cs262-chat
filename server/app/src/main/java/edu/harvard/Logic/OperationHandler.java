package edu.harvard.Logic;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.List;

import at.favre.lib.crypto.bcrypt.BCrypt;
import edu.harvard.Data.Data.Account;
import edu.harvard.Data.Data.AccountLookupResponse;
import edu.harvard.Data.Data.ListAccountsRequest;
import edu.harvard.Data.Data.LoginCreateRequest;
import edu.harvard.Data.Data.Message;
import edu.harvard.Data.Data.MessageResponse;
import edu.harvard.Data.Data.SendMessageRequest;
import edu.harvard.Data.Protocol.HandleException;

/*
 * Higher-level logic for all operations.
 */
public class OperationHandler {
  private Database db;

  public OperationHandler(Database db) {
    this.db = db;
  }

  public static class LoginResponse {
    public boolean success;
    public int account_id;
    public int unread_messages;
  }

  public AccountLookupResponse lookupAccount(String username) throws HandleException {
    AccountLookupResponse response = new AccountLookupResponse();
    Account account = db.lookupAccountByUsername(username);
    if (account == null) {
      response.exists = false;
      return response;
    }
    response.exists = true;
    response.bcrypt_prefix = account.client_bcrypt_prefix;
    return response;
  }

  /*
   * Returns ID of created account, or 0 for failure.
   */
  public int createAccount(LoginCreateRequest request) throws HandleException {
    Account account = new Account();
    account.client_bcrypt_prefix = request.password_hash.substring(0, 29);
    account.username = request.username;
    account.password_hash = BCrypt.withDefaults().hashToString(12, request.password_hash.toCharArray());
    return db.createAccount(account);
  }

  public LoginResponse login(LoginCreateRequest request) throws HandleException {
    LoginResponse response = new LoginResponse();
    // Get account
    Account account = db.lookupAccountByUsername(request.username);
    if (account == null) {
      response.success = false;
      return response;
    }
    BCrypt.Result result = BCrypt.verifyer().verify(request.password_hash.toCharArray(), account.password_hash);
    if (!result.verified) {
      response.success = false;
      return response;
    }
    int unreadCount = db.getUnreadMessageCount(account.id);
    response.success = true;
    response.account_id = account.id;
    response.unread_messages = unreadCount;
    return response;
  }

  public List<Account> listAccounts(ListAccountsRequest request) throws HandleException {
    ArrayList<Account> list = new ArrayList<>(request.maximum_number);
    Collection<Account> allAccounts = db.getAllAccounts();
    for (Account account : allAccounts) {
      boolean include = true;
      if (account.id < request.offset_account_id) {
        include = false;
      }
      if (!account.username.contains(request.filter_text)) {
        include = false;
      }
      if (include) {
        list.add(account);
      }
    }
    return list;
  }

  public int sendMessage(int sender_id, SendMessageRequest request) throws HandleException {
    // Look up sender
    Account sender = db.lookupAccount(sender_id);
    if (sender == null) {
      throw new HandleException("Sender does not exist!");
    }
    // Look up recipient
    Account account = db.lookupAccountByUsername(request.recipient);
    if (account == null) {
      throw new HandleException("Recipient does not exist!");
    }
    // Build Message
    Message m = new Message();
    m.message = request.message;
    m.recipient_id = account.id;
    m.sender_id = sender_id;
    // Add message to database
    int id = db.createMessage(m);
    // Auto-send message if possible
    Database.SocketWithProtocol s = db.getSocket(account.id);
    if (s == null) {
      m.read = false;
    } else {
      m.read = true;
      try {
        MessageResponse sendableMessage = new MessageResponse();
        sendableMessage.id = id;
        sendableMessage.sender = sender.username;
        sendableMessage.message = request.message;
        s.socket.getOutputStream()
            .write(s.protocol.generateRequestMessagesResponse(Arrays.asList(sendableMessage)));
      } catch (IOException e) {
        m.read = false;
      }
    }
    return id;
  }

  public List<MessageResponse> requestMessages(int user_id, int maximum_number) throws HandleException {
    List<Message> unreadMessages = db.getUnreadMessages(user_id, maximum_number);
    ArrayList<MessageResponse> responseMessages = new ArrayList<>(unreadMessages.size());
    for (Message message : unreadMessages) {
      MessageResponse messageResponse = new MessageResponse();
      messageResponse.id = message.id;
      messageResponse.message = message.message;
      messageResponse.sender = db.lookupAccount(message.sender_id).username;
      responseMessages.add(messageResponse);
    }
    return responseMessages;
  }

  // returns success boolean
  public boolean deleteMessages(int user_id, List<Integer> ids) {
    for (Integer i : ids) {
      Message m = db.getMessage(i);
      if (m.recipient_id != user_id && m.sender_id != user_id) {
        return false;
      }
      db.deleteMessage(i);
    }
    return true;
  }

  public void deleteAccount(int user_id) {
    db.deleteAccount(user_id);
  }
}
