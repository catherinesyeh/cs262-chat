package edu.harvard.Data;

public class Data {
  // Internal data types
  public class Account {
    int id;
    String username;
  }

  public class Message {
    int id;
    int sender_id;
    int recipient_id;
    String message;
  }

  // Multipart request/response types
  public class AccountLookupResponse {
    boolean exists;
    int bcrypt_cost;
    String bcrypt_salt;
  }

  public class LoginCreateRequest {
    String username;
    String password_hash;
  }

  public class ListAccountsRequest {
    int maximum_number;
    int offset_account_id;
    String filter_text;
  }

  public class SendMessageRequest {
    String recipient;
    String message;
  }

  public class MessageResponse {
    int id;
    String sender;
    String message;
  }
}
