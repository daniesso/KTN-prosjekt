# -*- coding: utf-8 -*-
import SocketServer
import json
import datetime

"""
Variables and functions that must be used by all the ClientHandler objects
must be written here (e.g. a dictionary for connected clients)
"""

class ClientHandler(SocketServer.BaseRequestHandler):
    """
    This is the ClientHandler class. Everytime a new client connects to the
    server, a new ClientHandler object will be created. This class represents
    only connected clients, and not the server itself. If you want to write
    logic for the server, you must write it outside this class
    """

    _history = []
    _client_list = {}
    _commands = {'login': self.handle_login, 'logout': self.handle_logout, 'message': self.handle_message,
                 'names': self.handle_names, 'help': self.handle_help}

    def handle(self):
        """
        This method handles the connection between a client and the server.
        """
        self.ip = self.client_address[0]
        self.port = self.client_address[1]
        self.connection = self.request

        # Loop that listens for messages from the client
        while True:
            received_string = self.connection.recv(4096)
            req = json.loads(received_string)
            command = req.get('request', 'help')
            content = req.get('content', '')
            if command not in self._commands:
                command = 'help'
            response = self._commands.get(command)(content)

    def handle_login(self, content):
        if content.isalpha():
            if content not in self._client_list:
                self._client_list[content] = self

    def handle_names(self, content):
        pass

    def handle_message(self, content):
        pass

    def handle_logout(self, content):
        pass

    def handle_help(self, content):
        self.send_info("""This server supports requests in the following format:
        1. login(user name) - attempts to log in with user name
        2. logout() - logs the user out
        3. msg(message) - sends message to everyone in chat room
        4. names() - lists all users in chatroom
        5. chatroom(chatroom name) - changes chatroom to chatroom name.
        6. help() - shows help.
        7. info() - session information.
        """)

    def get_connected_clients(self):
        pass

    def _create_json(self, sender, response, content):
        return json.dumps({'timestamp': timestamp, 'sender': sender,
                           'response': response,
                           'timestamp': str(datetime.datetime.now().timestamp())})

    def _logged_in(self, username):
        return username in self._client_list

    def _send_info(self, info):
        self.connection.send(json.dumps({
        'timestamp' : str(datetime.datetime.now().timestamp()),
        'sender' : "server",
        'response' : "info",
        'content' : info
        }))

    def _send_error(self, error):
        self.connection.send(json.dumps({
        'timestamp' : str(datetime.datetime.now().timestamp()),
        'sender' : "server",
        'response' : "error",
        'content' : error
        }))




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
    print 'Server running...'

    # Set up and initiate the TCP server
    server = ThreadedTCPServer((HOST, PORT), ClientHandler)
    server.serve_forever()
