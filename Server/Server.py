# -*- coding: utf-8 -*-
import SocketServer
import json
import datetime
import logging

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

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

    def handle(self):
        """
        This method handles the connection between a client and the server.
        """
        self.ip = self.client_address[0]
        self.port = self.client_address[1]
        self.connection = self.request
        self.username = None
        self._commands = {'login': self.handle_login, 'logout': self.handle_logout, 'message': self.handle_message,
                          'names': self.handle_names, 'help': self.handle_help}


        # Loop that listens for messages from the client
        while True:
            received_string = self.connection.recv(4096)
            logging.debug("Received string %s" % received_string)
            req = json.loads(received_string)
            command = req.get('request', 'help')
            content = req.get('content', None)
            if command not in self._commands:
                command = 'help'
            self._commands.get(command)(content)
            if command == 'logout':
                break

    def handle_login(self, content):
        logging.debug("Trying to log in user: %s" % content)
        content = content.strip()
        if content and content.isalpha():
            if self.username is not None:
                self._send_error("You're already logged in as {user}".format(user=self.username))
            elif not self._logged_in(content):
                self._client_list[content] = self
                self._send_info("You are now logged in as {user}".format(user=content))
                self.connection.send(self._create_json("server", "history", self._history))
            else:
                self._send_error("Username already taken!")
        else:
            self._send_error("Invalid username")

    def handle_names(self, content):
        logging.debug("Names requested")
        self._send_info("\n".join(self._client_list.keys()))

    def handle_message(self, content):
        logging.debug("Trying to send message %s" % content)
        msg = self._create_json(self.username, "message", content)
        self._history.append(msg)
        for x in self._client_list.keys():
            self._client_list[x].connection.send(msg)

    def handle_logout(self, content):
        logging.debug("Logging out")
        self._send_info("Successfully logged out")
        self.connection.close()
        self._client_list.pop(self.username)

    def handle_help(self, content):
        self._send_info("""This server supports requests in the following format:
        1. login(user name) - attempts to log in with user name
        2. logout() - logs the user out
        3. msg(message) - sends message to everyone in chat room
        4. names() - lists all users in chatroom
        5. chatroom(chatroom name) - changes chatroom to chatroom name.
        6. help() - shows help.
        7. info() - session information.
        """)

    def get_connected_clients(self):
        return self._client_list.values()

    def _create_json(self, sender, response, content):
        return json.dumps({'content': content, 'sender': sender,
                           'response': response,
                           'timestamp': str((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds())})

    def _logged_in(self, username):
        return username in self._client_list

    def _send_info(self, info):
        self.connection.send(self._create_json("server", "info", info))

    def _send_error(self, error):
        self.connection.send(self._create_json("server", "error", error))


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
    HOST, PORT = '', 9998
    print 'Server running...'

    # Set up and initiate the TCP server
    server = ThreadedTCPServer((HOST, PORT), ClientHandler)
    server.serve_forever()
