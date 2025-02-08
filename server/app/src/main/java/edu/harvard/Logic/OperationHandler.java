package edu.harvard.Logic;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

import at.favre.lib.crypto.bcrypt.BCrypt;
import at.favre.lib.crypto.bcrypt.IllegalBCryptFormatException;
import at.favre.lib.crypto.bcrypt.BCrypt.HashData;
import at.favre.lib.crypto.bcrypt.BCrypt.Version;
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
    response.bcrypt_cost = account.client_bcrypt_cost;
    response.bcrypt_salt = account.client_bcrypt_salt;
    return response;
  }

  /*
   * Returns ID of created account, or 0 for failure.
   */
  public int createAccount(LoginCreateRequest request) throws HandleException {
    try {
      Account account = new Account();
      HashData hashData = Version.VERSION_2A.parser.parse(request.password_hash.getBytes(StandardCharsets.UTF_8));
      account.client_bcrypt_cost = hashData.cost;
      account.client_bcrypt_salt = new String(Base64.getEncoder().encode(hashData.rawSalt));
      account.username = request.username;
      account.password_hash = BCrypt.withDefaults().hashToString(16, request.password_hash.toCharArray());
      return db.createAccount(account);
    } catch (IllegalBCryptFormatException ex) {
      System.err.println("Illegal bcrypt format in create account request:");
      System.err.println(ex.getMessage());
      throw new HandleException("The submitted password hash is corrupted.");
    }
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
