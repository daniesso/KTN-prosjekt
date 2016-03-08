from tkinter import *
from threading import Thread
from time import sleep
import socket
import json
import tkinter.messagebox


class ChatClient:

    def __init__(self, server):
        self.root = Tk()
        self.root.title("ChatClient")

        self.windowHeight = 500
        self.windowWidth = 700
        self.theme = "#9999FF"
        self.root.geometry(str(self.windowWidth) +"x" + str(self.windowHeight))
        self.set_up_window()

        self.connected = False
        self.trigger_send = False
        self.login_name = ""
        self.server = server

        self.text_window.tag_configure("error", foreground = "red")
        self.text_window.tag_configure("info", foreground ="#FFAAAA")
        self.text_window.tag_configure("client_user", font=("bold"))

        self.legal_responses = {"info" : self.handle_info, "message" : self.handle_message,
                "error" : self.handle_error, "history" : self.handle_history,
                "control" : self.handle_control}

        self.connect()
        self.printed_connect_message = False
        self.periodic()
        self.root.mainloop()

    def connect(self):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.connection.settimeout(0.5) Fails: also applies to recv. Without it, might stuck on open
        try:
            self.connection.connect(self.server)
        except:
            return
        self.connected = True

        self.senderThread = Thread(target = self.handle_send)
        self.senderThread.daemon = True
        self.senderThread.start()
        self.receiverThread = Thread(target = self.handle_receive)
        self.receiverThread.daemon = True
        self.receiverThread.start()

    def periodic(self):
        self.root.after(1000, self.periodic)
        if self.connected and not self.printed_connect_message:
            self.print_message("[CLIENT] Successfully connected to server!")
            self.printed_connect_message = True
        elif not self.connected:
            self.print_message("[CLIENT] Couldn't connect to server. Trying again...")
            self.connect()
            return

        try:
            self.connection.send(json.dumps({"request" : "info", "content" : None}).encode("utf-8"))
        except BrokenPipeError:
            self.connected = False
            self.printed_connect_message = False


    def print_message(self, message, tag = None):
        self.text_window.config(state = NORMAL)
        self.text_window.insert(END, message+"\n", tag)
        self.text_window.config(state = DISABLED)


    def clear_textbox(self):
        self.text_window.config(state = NORMAL)
        self.text_window.delete('1.0', END)
        self.text_window.config(state = DISABLED)

    def handle_send(self):
        while True:
            if self.trigger_send:
                self.trigger_send = False
                
                toSend = {}
                inp = self.text_entry.get('1.0', END).strip()
                if len(inp) == 0:
                    continue
                elif inp[0] == "/":
                    inp = inp[1:]
                    words = list(map(str.strip, inp.strip().split()))
                    if len(words) == 1:
                        if words[0] == "logout":
                            pass # logout logic here
                        toSend["request"] = words[0]
                        toSend["content"] = None
                    elif len(words) == 2:
                        if words[0] == "login":
                            self.login_name = words[1]

                        toSend["request"] = words[0]
                        toSend["content"] = words[1]
                    elif len(words) == 3:
                        toSend["request"] = words[0]
                        toSend["content"] = words[1]
                        toSend["password"] = words[2]
                else:
                    toSend["request"] = "message"
                    toSend["content"] = inp

                self.connection.send(json.dumps(toSend).encode("utf-8"))
                self.text_entry.delete('1.0', END)
            sleep(0.1)

    def handle_receive(self):
        while True:
            try:
                recv_str = self.connection.recv(4096).decode("utf-8")
                strs = []
                while "{" in recv_str and "}" in recv_str:
                    ind1 = recv_str.find("{")
                    ind2 = ind1 + 1
                    depth = 0

                    while depth > 0 or recv_str[ind2] != "}":
                        if recv_str[ind2] == "{":
                            depth += 1
                        elif recv_str[ind2] == "}":
                            depth -= 1
                        ind2 += 1

                    strs.append(recv_str[ind1 : ind2 + 1])
                    recv_str = recv_str[:ind1] + recv_str[ind2+1:]
                
                for json_str in strs:
                    payload = json.loads(json_str)
                    if payload.get("response", None) in self.legal_responses:
                        self.legal_responses[payload["response"]](payload)
            except KeyboardInterrupt:
               tkinter.messagebox.showwarning("Error", "Error upon parsing received json")


    def handle_info(self, payload):
        self.print_message(
                "[Server] INFO: " + payload["content"], "info")
        
    def handle_error(self, payload):
        self.print_message(
                "[Server] ERROR: " + payload["content"], "error")

    def handle_message(self, payload):
        if payload["sender"] == self.login_name:
            tag = "client_user"
        else:
            tag = None
        self.print_message("["+self.time(payload["timestamp"])+"] " + \
                payload["sender"] + ": " + payload["content"], tag)

    def handle_history(self, payload):
        self.clear_textbox()
        for msg in payload["content"]:
            self.handle_message(msg)

    def handle_control(self, payload):
        self.info_box.config(state = NORMAL)
        self.names_window.config(state = NORMAL)

        self.info_box.delete(1.0, END)
        self.names_window.delete(1.0, END)
        if payload.get("name", None) is None:
            self.info_box.insert(END, 
                    """Status: not logged in\n\nChatroom: none\n\n\n\nLogged in as: \n\nLogged in for: """)
        else:
            self.info_box.insert(END, 
                    "Status: logged in!\n\n" + \
                            "Chatroom: " + payload.get("chatroom", "") + "\n\n\n\n" + \
                            "Logged in as: " + payload.get("name", "") + \
                            ("\n(admin)" if payload.get("admin", False) else "") + "\n\n" + \
                            "Logged in for: "+ str(int(payload.get("elapsed", "") / 60)) + " mins")
            self.names_window.insert(END,
                    "\n".join(payload["names"]))
        self.info_box.config(state = DISABLED)
        self.names_window.config(state = DISABLED)


    def time(self, payload):
        return payload[11:]

    def send_event(self):
        self.trigger_send = True

    def set_up_window(self):
        self.left_pane = Frame(self.root, bg = self.theme)
        self.input_pane = Frame(self.root, bg = self.theme)
        self.text_pane = Frame(self.root)

        self.left_pane.grid(row = 0, column = 0, rowspan=2, sticky = W+E+N+S)
        self.input_pane.grid(row = 1, column = 1, sticky = W+E+N+S)
        self.text_pane.grid(row = 0, column = 1, sticky = W+E+N+S)

        Grid.columnconfigure(self.root, 0, weight = 3)
        Grid.columnconfigure(self.root, 1, weight = 8)
        Grid.rowconfigure(self.root, 0, weight=4)
        Grid.rowconfigure(self.root, 1, weight=1)

        self.input_pane.grid_propagate(False)
        self.left_pane.pack_propagate(False)
        self.text_pane.pack_propagate(False)

        #INPUT PANE
        self.input_pane_fr1 = Frame(self.input_pane)
        self.input_pane_fr2 = Frame(self.input_pane)

        Grid.columnconfigure(self.input_pane, 0, weight=3)
        Grid.columnconfigure(self.input_pane, 1, weight=1)
        Grid.rowconfigure(self.input_pane, 0, weight=1)
        
        self.input_pane_fr1.grid(row = 0, column = 0, sticky = W+E+N+S, padx=(0, 3), pady=3)
        self.input_pane_fr2.grid(row = 0, column = 1, sticky = W+E+N+S, padx=3, pady=3)

        self.input_pane_fr1.pack_propagate(False)
        self.input_pane_fr2.pack_propagate(False)

        self.text_entry = Text(self.input_pane_fr1)
        self.text_entry.config(highlightthickness = 0)
        self.text_entry.bind("<Return>", lambda e : self.send_event())
        self.text_entry.bind("<Shift-Return>", lambda e : None)

               
        self.text_entry.pack(fill = BOTH, expand = 1, padx=3, pady=3)
        self.send_button = Button(self.input_pane_fr2, text = "Send", 
                foreground=self.theme, command = self.send_event)
        self.send_button.pack(fill=BOTH, expand=1)

        #TEXT PANE

        self.scrollbar = Scrollbar(self.text_pane)
        self.scrollbar.pack(side=RIGHT, fill = Y)
        self.text_window = Text(self.text_pane, wrap=WORD, yscrollcommand=self.scrollbar.set,
                highlightthickness = 0, state = DISABLED)
        self.text_window.pack(fill = BOTH, expand = 1, padx=3, pady=3)


        #LEFT PANE

        self.left_pane_fr1 = Frame(self.left_pane, bg = self.theme)
        self.left_pane_fr2 = Frame(self.left_pane, bg = self.theme)

        self.left_pane_fr1.pack(side=TOP, fill = BOTH, expand = 6)
        self.left_pane_fr2.pack(side=BOTTOM, fill = BOTH, expand = 5, padx = 20, pady=(0, 40))

        self.left_pane_fr1.pack_propagate(False)
        self.left_pane_fr2.pack_propagate(False)

        self.info_box = Text(self.left_pane_fr1, bg = self.theme, highlightthickness=0)
        self.info_box.insert(END, 
                """Status: not logged in\n\nChatroom: none\n\n\n\nLogged in as: \n\nLogged in for: """)
        self.info_box.config(state = DISABLED)
        self.info_box.pack(fill = BOTH, expand = 1, padx=10, pady=(30,0))


        self.usersLabel = Label(self.left_pane_fr2, text = "Users in chatroom", bg = self.theme)
        self.usersLabel.pack(side = TOP, pady=5)
        self.left_scrollbar = Scrollbar(self.left_pane_fr2)
        self.left_scrollbar.pack(side=RIGHT, fill = Y)
        self.names_window = Text(self.left_pane_fr2, wrap=WORD, yscrollcommand=self.left_scrollbar.set, highlightthickness = 0, state = DISABLED)
        self.names_window.pack(fill = X, expand = 1, side = BOTTOM)


class MessageReceiver(Thread):
    def __init__(self, connection):
        
        super(MessageReceiver, self).__init__()

        self.daemon = True
        self._running = True
        self.connection = connection

        self.handler = MessageParser()

    def run(self):
        while True:
            s = None 
            try: # Fix handle successive jsons
                s = self.connection.recv(4096)
                self.handler.parse(json.loads(s))
            except:
                pass

if __name__ == '__main__':
    client = ChatClient(("37.139.20.205", 9998))
