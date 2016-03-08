# -*- coding: utf-8 -*-
import socket
from threading import *
#from MessageReceiver import MessageReceiver
#from MessageParser import MessageParser

class Client:

    def __init__(self, host, server_port):

        # Set up the socket connection to the server
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.server_port = server_port
        
        self.run()

    def run(self):
        # Initiate the connection to the server
        self.connection.connect((self.host, self.server_port))
        
    def disconnect(self):
        # TODO: Handle disconnection
        pass

    def receive_message(self):
        while True:
            message = clientSocket.recvfrom(1024)
            print(message)

    def send_payload(self, data):
        clientSocket.sendto(data, self.host, self.server_port)

    def take_and_send_input():
        while True:
            send_payload(input(": "))
        
if __name__ == '__main__':
    """
    This is the main method and is executed when you type "python Client.py"
    in your terminal.

    No alterations are necessary
    """
    client = Client('localhost', 1337)
    client.run()
    Thread(target=take_and_send_input).start()
    Thread(target=recieve_message)
