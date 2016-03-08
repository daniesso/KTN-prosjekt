# -*- coding: utf-8 -*-
import SocketServer
import json
import Serve as S
from threading import RLock

"""
Variables and functions that must be used by all the ClientHandler objects
must be written here (e.g. a dictionary for connected clients)
"""
lock = RLock()

class ClientHandler(SocketServer.BaseRequestHandler):
    """
    This is the ClientHandler class. Everytime a new client connects to the
    server, a new ClientHandler object will be created. This class represents
    only connected clients, and not the server itself. If you want to write
    logic for the server, you must write it outside this class
    """

    def handle(self):
        """
        This method handles the connection between a client and the server.
        """
        self.ip = self.client_address[0]
        self.port = self.client_address[1]
        self.connection = self.request

        try:
            lock.acquire()
            if self.ip in S.banned:
               return
        finally:
            lock.release()


        while True:
            try:
                payload = json.loads(self.connection.recv(4096))
            except:
                try:
                    lock.acquire()
                    S.handle_logout(self.connection)
                finally:
                    lock.release()
                break

            request = payload.get("request", None)

            if request in S.legal_requests:
                content = payload.get("content", None)
                pw = payload.get("password", u"")
                if type(content) is S.legal_requests[request] and \
                        type(pw) is S.legal_requests["password"]:
                    lock.acquire()
                    try: 
                        if request == "login":
                            S.handle_login(self.connection, content, password=pw)
                        elif request == "logout":
                            S.handle_logout(self.connection)
                            break
                        elif request == "message":
                            S.handle_message(self.connection, content)
                        elif request == "names":
                            S.handle_names(self.connection)
                        elif request == "help":
                            S.handle_help(self.connection)
                        elif request == "chatroom":
                            S.handle_chatroom(self.connection, content)
                        elif request == "info":
                            S.handle_info(self.connection)
                        elif request == "kick":
                            S.handle_kick(self.connection, content)
                        elif request == "ban":
                            S.handle_ban(self.connection, content)
                    except:
                        pass
                    finally:
                        lock.release()
                else:
                    S.send_error(self.connection, "Invalid argument for request " + request)
            else:
                S.send_error(self.connection, "Unknown request. See 'help' for legal requests")


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    """
    This class is present so that each client connected will be ran as a own
    thread. In that way, all clients will be served by the server.

    No alterations are necessary
    """
    allow_reuse_address = True

if __name__ == "__main__":
    """
    This is the main method and is executed when you type "python Server.py"
    in your terminal.

    No alterations are necessary
    """
    HOST, PORT = 'localhost', 9998
    for line in open(".admins", "r"):
        u, p = line.split()
        S.admins[u] = p
    print str(len(S.admins)) + " admins loaded successfully."
    print 'Server running...'

    # Set up and initiate the TCP server
    server = ThreadedTCPServer((HOST, PORT), ClientHandler)
    server.serve_forever()
