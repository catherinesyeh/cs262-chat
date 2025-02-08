package edu.harvard.Data;

import java.io.InputStream;

public class WireProtocol implements Protocol {
  public Request parseRequest(int operation_code, InputStream inputStream) throws ParseException {
    return null;
  }

  // Output building
  public byte[] generateUnexpectedFailureResponse(Operation operation, String message) {
    return new byte[1];
  }
}
