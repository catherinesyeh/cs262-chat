package edu.harvard.Logic;

import at.favre.lib.crypto.bcrypt.BCrypt;
import edu.harvard.Data.Data.Account;
import edu.harvard.Data.Data.AccountLookupResponse;
import edu.harvard.Data.Data.LoginCreateRequest;
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
    account.password_hash = BCrypt.withDefaults().hashToString(16, request.password_hash.toCharArray());
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
}
