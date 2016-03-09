# -*- coding: utf-8 -*-
import socket
import json
import logging
import time
from threading import *
from Queue import Queue         # Queue for multithreading purposes
from datetime import datetime   # Format unix time

logging.basicConfig(level=logging.DEBUG)


class Client(Thread):

    def __init__(self, host, server_port):
        super(Client, self).__init__(name="Sender")

        self._host = host
        self._server_port = server_port
        self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self._out_queue = Queue()   # Queue for outgoing traffic
        self._in_queue = Queue()    # Queue for incoming traffic

        self.daemon = True

        self._exit_flag = Event()
        self._handle = {'message': self._handle_message,
                        'info': self._handle_message,
                        'error': self._handle_message,
                        'history': self._handle_history}

        self.start()

    def write(self, string):
        if self._exit_flag.is_set():
            raise Exception("Client has been closed")
        self._out_queue.put(string)

    def has_next(self):
        if self._exit_flag.is_set():
            raise Exception("Client has been closed")
        return not self._in_queue.empty()

    def get_next(self):
        if self._exit_flag.is_set():
            raise Exception("Client has been closed")

        # Blocks if queue is empty, so check first with has_next
        return self._in_queue.get()

    def run(self):
        self._connection.connect((self._host, self._server_port))
        logging.debug("Connected to server")

        self._receive_thread = Thread(target=self._receive_always, name="Receiver")
        self._receive_thread.daemon = True
        self._receive_thread.start()

        self._send_always()

    def disconnect(self):
        self._exit_flag.set()
        self._out_queue.put("")         # Trigger flag check

    def _send_always(self):
        while not self._exit_flag.is_set():
            string = self._out_queue.get()
            if not string:
                continue
            elif string[0] == "/":
                args = string[1:].split(" ", 1)  # Max two results
                if len(args) == 1:
                    self._send_payload(args[0], None)
                elif len(args) == 2:
                    self._send_payload(args[0], args[1])
            else:
                self._send_payload("message", string)

    def _receive_always(self):
        while not self._exit_flag.is_set():
            try:
                raw = self._connection.recv(4096)
                jsn = json.loads(raw)
            except ValueError as e:
                if raw == '':
                    self._exit_flag.set()
                    break
                logging.debug("Error while parsing json or receiving")
                time.sleep(0.3)
                continue
            logging.debug("Received from server NOW")

            response, time_stamp, sender, content = self._extract_fields(jsn)
            if response in self._handle:
                self._handle[response](time_stamp, sender, content)

    def _extract_fields(self, jsn):
            response = jsn.get('response', '')
            time_stamp = float(jsn.get('timestamp', time.time()))  # Default to now
            time_stamp = datetime.fromtimestamp(time_stamp).strftime("%H:%M:%S")
            sender = jsn.get('sender', '')
            content = jsn.get('content', '')
            return response, time_stamp, sender, content

    def _handle_message(self, time, sender, content):
        self._in_queue.put("[" + time + "] " + str(sender) + ": " + str(content))

    def _handle_history(self, time, sender, content):
        for jsn in content:
            jsn = json.loads(jsn)
            self._handle_message(*self._extract_fields(jsn)[1:])

    def _send_payload(self, request, content):
        logging.debug("Sending to server NOW")
        self._connection.send(json.dumps({"request": request,
                                          "content": content}))


def printer(client):  # To be replaced with GUI
    while 1:
        if client.has_next():
            print client.get_next()

if __name__ == '__main__':
    client = Client('162.243.253.165', 9998)
    t = Thread(target=printer, args=[client])
    t.daemon = True
    t.start()
    while 1:    # To be replaced with GUI
        client.write(raw_input("> "))
