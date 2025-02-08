package edu.harvard;

import java.io.IOException;
import java.net.Socket;

import edu.harvard.Data.JSONProtocol;
import edu.harvard.Data.Protocol;
import edu.harvard.Data.WireProtocol;
import edu.harvard.Data.Data.AccountLookupResponse;
import edu.harvard.Data.Protocol.Operation;
import edu.harvard.Data.Protocol.Request;
import edu.harvard.Logic.Database;
import edu.harvard.Logic.OperationHandler;

public class AppThread extends Thread {
  private Socket socket = null;
  private Database db = null;

  public AppThread(Socket socket, Database db) {
    super("AppThread");
    this.socket = socket;
    this.db = db;
  }

  public void run() {
    System.out.println("New connection from " + socket.getInetAddress().toString());
    while (true) {
      int firstByte = 0;
      Protocol protocol = null;
      try {
        // Choose a protocol layer: JSON or wire
        firstByte = socket.getInputStream().read();
        if (firstByte == -1) {
          socket.close();
          break;
        }

        if (firstByte == 123) {
          // First byte is {, parse as JSON request
          protocol = new JSONProtocol();
        } else {
          protocol = new WireProtocol();
        }

        // Parse the request
        Request request;
        try {
          request = protocol.parseRequest(firstByte, socket.getInputStream());
        } catch (Protocol.ParseException e) {
          // todo handle
          continue;
        }

        // Handle the request
        try {
          OperationHandler handler = new OperationHandler(db);
          switch (request.operation) {
            case LOOKUP_USER:
              AccountLookupResponse response = handler.lookupAccount((String) request.payload);
              socket.getOutputStream().write(protocol.generateLookupUserResponse(response));
            default:
              throw new Protocol.HandleException("Operation not implemented: " + request.operation.toString());
          }
        } catch (Protocol.HandleException e) {
          // todo handle
          continue;
        }
      } catch (IOException e) {
        System.err.println("Unexpected I/O error in main thread:");
        // TODO return error message
        if (protocol != null) {
          protocol.generateUnexpectedFailureResponse(Operation.codeToOperation(firstByte),
              "Unexpected error in handling request!");
        }
        e.printStackTrace();
      }
    }
  }
}
