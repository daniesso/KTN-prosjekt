import json
import re
from datetime import datetime
from threading import RLock
from hashlib import md5

users = {}              # username : socket
chatroom = {}           # username : chatroom
history = {"all" : []}  # chatroom : list of messages
admins = {}             # username : password - Loaded from file
login_time = {}         # username : datetime
banned = set()          # set of banned ip addresses

noneType = type(None)
legal_requests = {"login" : unicode, "logout" : noneType, "names" : noneType, 
        "message" : unicode, "help" : noneType, "chatroom" : unicode, 
        "password" : unicode, "info" : noneType, "kick" : unicode,
        "ban" : unicode}

def handle_login(socket, username, password = ""):
    if username in users:
        send_error(socket, "Sorry, username is taken. Try again")
    elif socket in users.values():
        send_error(socket, "Sorry, you're already loggedi in")
    elif not re.match("\w+", username):
        send_error(socket, "Sorry, username must be alphanumeric")
    elif username in admins and password == "":
        send_error(socket, "Sorry, "+username+" is an admin name, but you provided no password")
    elif username in admins and not auth_pass(username, password):
        send_error(socket, "Sorry, wrong password")
    else:
        users[username] = socket
        chatroom[username] = "all"
        login_time[username] = datetime.now()
        send_info(socket, 
                ("[ADMIN] " if username in admins else "") +
                "You're successfully logged in, " + username)
        send_history(socket, "all")

def handle_logout(socket):
    if auth(socket):
        send_info(socket, "You're successfully logged out")

        user = get_corr_name(socket)
        socket.close()

        del chatroom[user]
        del users[user]
        del login_time[user]

def handle_names(socket):
    if auth(socket):
        user = get_corr_name(socket)
        room = chatroom[user]
        send_info(socket, "Currently in " + room + ":\n" + "\n".join(room_members(room)))

def handle_message(socket, message):
    if auth(socket):
        #send_info(socket, "Message sent")

        user = get_corr_name(socket)
        room = chatroom[user]
        msg = get_json(user, "message", message)

        history[room].append(json.loads(msg))
        for userSocket in [users[usr] for usr in room_members(room)]:
            userSocket.send(msg)

def handle_help(socket):
    send_info(socket,
        """This server supports requests in the following format:
        1. login(user name) - attempts to log in with user name
        2. logout() - logs the user out
        3. msg(message) - sends message to everyone in chat room
        4. names() - lists all users in chatroom
        5. chatroom(chatroom name) - changes chatroom to chatroom name.
        6. help() - shows help.
        7. info() - session information.
        """)

def handle_info(socket):
    base = json.loads(get_json("server", "control", "Session information"))

    if socket in users.values():
        user = get_corr_name(socket)
        base["name"] = user
        base["names"] = room_members(chatroom[user])
        base["chatroom"] = chatroom[user]
        base["login_time"] = login_time[user].__str__()[:-7]
        base["elapsed"] = int((datetime.now() - login_time[user]).total_seconds())
        base["admin"] = (user in admins)
    else:
        base.update({"name" : None, "names" : None, "chatroom" : None, "login_time" : None,
                "elapsed" : None, "admin" : None})

    socket.send(json.dumps(base))

def handle_chatroom(socket, room):
    if not auth(socket):
        return
    elif not re.match("\w+", room):
        send_error(socket, "Sorry, chatroom must be alphanumeric")
    else:
        user = get_corr_name(socket)
        chatroom[user] = room
        if room not in history:
            history[room] = []
        send_info(socket, "Successfully changed room to " + room)
        send_history(socket, room)

def handle_kick(socket, user, ban = False):
    if not auth(socket):
        return
    elif user not in users:
        send_error(socket, 'Sorry, there is no user "' + user + '"')
    elif get_corr_name(socket) not in admins:
        send_error(socket, "Sorry, you're not admin")
    else:
        if ban:
            banned.add(users[user].getpeername()[0])
            send_info(users[user], "You were banned by " + get_corr_name(socket))
        else:
            send_info(users[user], "You were kicked by " + get_corr_name(socket))

        tmp = users[user]
        del users[user]
        del chatroom[user]
        del login_time[user]
        handle_info(tmp)
        tmp.close()

def handle_ban(socket, user):
    handle_kick(socket, user, ban = True)

def send_history(socket, chatroom):
    socket.send(get_json(
        "server",
        "history",
        history[chatroom]))

def send_error(socket, error):
    socket.send(get_json( "server",
        "error",
        error))
    
def send_info(socket, info):
    socket.send(get_json( "server",
        "info",
        info))

def auth(socket):
    """Check that the user is currently logged on"""
    if socket in users.values():
        return True
    else:
        send_error(socket, "Sorry, you're not logged in.")
        return False

def auth_pass(username, socket):
    gen = md5()
    gen.update(socket)
    hsh = gen.hexdigest()
    return username in admins and admins[username] == hsh


def get_json(username, response, content):
    """Get json string in protocol format"""
    return json.dumps({
        'timestamp' : datetime.now().__str__()[:-7],
        'sender' : username,
        'response' : response,
        'content' : content
        })

def get_corr_name(socket):
    hits = [key for key in users if users[key] is socket]
    return hits[0] if len(hits) > 0 else None

def room_members(room):
    return [user for user in chatroom if chatroom[user] == room]
