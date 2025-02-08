package edu.harvard.Data;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;

import org.json.JSONObject;

public class JSONProtocol implements Protocol {
  public Request parseRequest(int operation_code, InputStream inputStream) throws ParseException {
    try {
      // PrintWriter out = new PrintWriter(socket.getOutputStream(), true);
      BufferedReader in = new BufferedReader(
          new InputStreamReader(
              inputStream));
      String inputLine = "{".concat(in.readLine());
      JSONObject obj = new JSONObject(inputLine);
      Operation operation = Operation.valueOf(obj.getString("operation"));
      return null;
    } catch (IOException ex) {
      throw new ParseException("Unexpected JSON parsing error.");
    }
  }

  // Output building
  public byte[] generateUnexpectedFailureResponse(Operation operation, String message) {
    return new byte[1];
  }
}
