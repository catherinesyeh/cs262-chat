package edu.harvard.Data;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;

import org.json.JSONException;
import org.json.JSONObject;

public class JSONProtocol implements Protocol {
  public Request parseRequest(int operation_code, InputStream inputStream) throws ParseException {
    try {
      // PrintWriter out = new PrintWriter(socket.getOutputStream(), true);
      BufferedReader in = new BufferedReader(
          new InputStreamReader(
              inputStream));
      String inputLine = "{".concat(in.readLine());
      JSONObject obj = null;
      Operation operation;
      try {
        obj = new JSONObject(inputLine);
        operation = Operation.valueOf(obj.getString("operation"));
        if (operation == null || operation.equals(Operation.UNKNOWN)) {
          throw new ParseException("Invalid operation code.");
        }
      } catch (JSONException ex) {
        throw new ParseException("Could not parse operation code.");
      }
      JSONObject payload = null;
      try {
        // All other operations require some payload.
        if (!operation.equals(Operation.DELETE_ACCOUNT)) {
          payload = obj.getJSONObject("payload");
        }
      } catch (JSONException ex) {
        throw new ParseException("JSON requests must include a payload field.");
      }
      try {
        Request parsedRequest = new Request();
        parsedRequest.operation = operation;
        switch (operation) {
          case LOOKUP_USER:
            parsedRequest.payload = payload.getString("username");
            return parsedRequest;
          case LOGIN:
          case CREATE_ACCOUNT:
            Data.LoginCreateRequest loginCreatePayload = new Data.LoginCreateRequest();
            loginCreatePayload.username = payload.getString("username");
            loginCreatePayload.password_hash = payload.getString("password_hash");
            parsedRequest.payload = loginCreatePayload;
            return parsedRequest;
          case LIST_ACCOUNTS:
            Data.ListAccountsRequest listPayload = new Data.ListAccountsRequest();
            listPayload.maximum_number = payload.getInt("maximum_number");
            listPayload.offset_account_id = payload.getInt("offset_account_id");
            try {
              listPayload.filter_text = payload.getString("filter_text");
            } catch (JSONException ex) {
              listPayload.filter_text = "";
            }
            parsedRequest.payload = listPayload;
            return parsedRequest;
          case SEND_MESSAGE:
            Data.SendMessageRequest sendPayload = new Data.SendMessageRequest();
            sendPayload.recipient = payload.getString("recipient");
            sendPayload.message = payload.getString("message");
            parsedRequest.payload = sendPayload;
            return parsedRequest;
          case REQUEST_MESSAGES:
            parsedRequest.payload = payload.getInt("maximum_number");
            return parsedRequest;
          case DELETE_MESSAGES:
            parsedRequest.payload = payload.getJSONArray("message_ids").toList();
            return parsedRequest;
          default:
            // DELETE_ACCOUNT or others with no payload to parse
            return parsedRequest;
        }
      } catch (JSONException ex) {
        System.err.println("JSON parse error:");
        System.err.println(operation);
        System.err.println(ex.getMessage());
        throw new ParseException("Your JSON request did not include a required field.");
      }
    } catch (IOException ex) {
      throw new ParseException("Unexpected JSON parsing error.");
    }
  }

  // Output building
  public byte[] generateUnexpectedFailureResponse(Operation operation, String message) {
    return new byte[1];
  }
}
