# -*- coding: utf-8 -*-
import SocketServer
import socket
import json
import logging

import time
import calendar
from datetime import datetime

logging.basicConfig(filename='server.log', format='%(levelname)s: %(message)s', level=logging.DEBUG)

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

        while True:
            try:
                received_string = self.connection.recv(4096)
            except socket.error as e:
                logging.debug("Client disconnected %s" % e)
                if self.username is not None:
                    self._client_list.pop(self)
                break
            logging.debug("Received string:'%s'" % received_string)
            logging.debug("Host: '%s', Port: '%s'" % (self.ip, self.port))
            try:
                req = json.loads(received_string)
            except ValueError as e:
                logging.debug("Could not parse JSON-string: '%s'" % received_string)
                break
            command = req.get('request', 'help')
            content = req.get('content', None)
            if command not in self._commands:
                command = 'help'
            self._commands.get(command)(content)
            if command == 'logout':
                break

    def handle_login(self, content):
        logging.debug("Trying to log in user'%s', from '%s', port '%s'" % (content, self.ip, self.port))
        if content is None:
            self._send_error("You must specify a username")
            return
        content = content.strip()
        if content and content.isalnum():
            if self.username is not None:
                self._send_error("You're already logged in as {user}".format(user=self.username))
            elif not self._logged_in(content):
                self._client_list[content] = self
                self.username = content
                self._send_info("You are now logged in as {user}".format(user=content))
                self.connection.send(self._create_json("server", "history", self._history))
            else:
                self._send_error("Username already taken!")
        else:
            self._send_error("Invalid username")

    def handle_names(self, content):
        logging.debug("Names requested")
        logging.debug("Host: '%s', Port: '%s'" % (self.ip, self.port))
        self._send_info("\n".join(self._client_list.keys()))

    def handle_message(self, content):
        if not self._logged_in(self.username):
            logging.debug("User not logged in tried to send message: '%s'" % content)
            self._send_error("You are not logged in")
            return
        msg = self._create_json(self.username, "message", content)
        logging.debug("Trying to send message '%s'" % msg)
        logging.debug("Host: '%s', Port: '%s'" % (self.ip, self.port))
        self._history.append(msg)
        for username, client in self._client_list.items():
            try:
                client.connection.send(msg)
            except socket.error as e:
                logging.debug("Closing dead socket: %s" % e)
                self._client_list.pop(username)

    def handle_logout(self, content):
        if self.username is not None:
            logging.debug("Logging out")
            logging.debug("Host: '%s', Port: '%s'" % (self.ip, self.port))
            self._send_info("Successfully logged out")
            self.connection.close()
            self._client_list.pop(self.username)
        else:
            logging.debug("Not logged in user tried to log out")
            self._send_error("You are not logged in")

    def handle_help(self, content):
        self._send_info("""This server supports requests in the following format:
        1. login(username) - attempts to log in with username
        2. logout() - logs the user out
        3. msg(message) - sends message to everyone in chatroom
        4. names() - lists all users in chatroom
        5. help() - shows help.
        """)

    def get_connected_clients(self):
        return self._client_list.values()

    def _create_json(self, sender, response, content):
        return json.dumps({'content': content, 'sender': sender,
                           'response': response,
                           'timestamp': self._get_utc_timestamp()})

    def _logged_in(self, username):
        return username is not None and username in self._client_list

    def _send_info(self, info):
        json_string = self._create_json("server", "info", info)
        logging.debug("Sending info message:'%s'" % json_string)
        try:
            self.connection.send(json_string)
        except socket.error as e:
            logging.debug("Client disconnected: %s" % e)

    def _send_error(self, error):
        json_string = self._create_json("server", "error", error)
        logging.debug("Sending error message:'%s'" % json_string)
        try:
            self.connection.send(json_string)
        except socket.error as e:
            logging.debug("Client disconnected: %s" % e)

    @staticmethod
    def _get_utc_timestamp():
        #return str(calendar.timegm(time.gmtime()))
        return datetime.fromtimestamp(time.time()).strftime("%H:%M:%S")


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
    logging.info("Server running...")

    # Set up and initiate the TCP server
    server = ThreadedTCPServer((HOST, PORT), ClientHandler)
    server.serve_forever()
