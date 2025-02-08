package edu.harvard.Data;

import java.io.InputStream;

public interface Protocol {
  public class ParseException extends Exception {
    public ParseException(String errorMessage) {
      super(errorMessage);
    }
  }

  public enum Operation {
    UNKNOWN(0),
    LOOKUP_USER(1),
    LOGIN(2),
    CREATE_ACCOUNT(3),
    LIST_ACCOUNTS(4),
    SEND_MESSAGE(5),
    REQUEST_MESSAGES(6),
    DELETE_MESSAGES(7),
    DELETE_ACCOUNT(8);

    private final int id;

    Operation(int id) {
      this.id = id;
    }

    int getId() {
      return id;
    }

    public static Operation codeToOperation(int operation_code) {
      switch (operation_code) {
        case 1:
          return Operation.LOOKUP_USER;
        case 2:
          return Operation.LOGIN;
        case 3:
          return Operation.CREATE_ACCOUNT;
        case 4:
          return Operation.LIST_ACCOUNTS;
        case 5:
          return Operation.SEND_MESSAGE;
        case 6:
          return Operation.REQUEST_MESSAGES;
        case 7:
          return Operation.DELETE_MESSAGES;
        case 8:
          return Operation.DELETE_ACCOUNT;
        default:
          return Operation.UNKNOWN;
      }
    }
  }

  public class Request {
    Operation operation;
    Object payload;
  }

  // Input parsing
  public Request parseRequest(int operation_code, InputStream inputStream) throws ParseException;

  // Output building
  public byte[] generateUnexpectedFailureResponse(Operation operation, String message);
}
