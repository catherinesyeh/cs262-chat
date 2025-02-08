package edu.harvard;

import java.io.IOException;
import java.net.Socket;

import edu.harvard.Data.JSONProtocol;
import edu.harvard.Data.Protocol;
import edu.harvard.Data.WireProtocol;
import edu.harvard.Data.Protocol.Operation;
import edu.harvard.Data.Protocol.Request;

public class AppThread extends Thread {
  private Socket socket = null;

  public AppThread(Socket socket) {
    super("AppThread");
    this.socket = socket;
  }

  public void run() {
    while (true) {
      int firstByte = 0;
      Protocol protocol = null;
      try {
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

        try {
          Request request = protocol.parseRequest(firstByte, socket.getInputStream());
        } catch (Protocol.ParseException e) {
          // todo handle
        }
      } catch (IOException e) {
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
