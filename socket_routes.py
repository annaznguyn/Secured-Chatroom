'''
socket_routes
file containing all the routes related to socket.io
'''


from flask_socketio import join_room, emit, leave_room
from flask import request

try:
    from __main__ import socketio
except ImportError:
    from app import socketio

from models import Room

import db

room = Room()
key_dict = {}
USERS_LIST = []

# when the client connects to a socket
# this event is emitted when the io() function is called in JS
@socketio.on('connect')
def connect():
    username = request.cookies.get("username")
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return
    # socket automatically leaves a room on client disconnect
    # so on client connect, the room needs to be rejoined
    
    join_room(int(room_id))
    
    msg = (f"{username} has connected", "green")
    emit("incoming", msg, to=int(room_id))
    

# event when client disconnects
# quite unreliable use sparingly
@socketio.on('disconnect')
def disconnect():
    username = request.cookies.get("username")
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return

    msg = (f"{username} has disconnected", "red")
    emit("incoming", msg, to=int(room_id))


@socketio.on("derive_chat_key")
def derive_chat_key(username, reciever, encrypt_or_decrypt):
    user = db.get_user(username)
    if encrypt_or_decrypt == "True":
        emit("get_chat", ((user.password), (user.salt), None, None, encrypt_or_decrypt))
    else:
        if len(db.get_history(username, reciever)) == 0:
            emit("get_chat", ((user.password), (user.salt), None, None, None))
        else:
            for r in db.get_history(username, reciever):
                emit("get_chat", ((user.password), (user.salt), r[0], r[1], encrypt_or_decrypt))

@socketio.on("store")
def store(username, reciever, msg, hmac, system_message):
    if (username in USERS_LIST and reciever in USERS_LIST):
        db.store(username, reciever, msg, hmac)
    elif (system_message == "True"):
        db.store(username, reciever, msg, hmac)
    

# send message event handler
@socketio.on("send")
def send(username, reciever, message, color, room_id):
    msg = (f"{username}: {message}")
    emit("incoming", (msg, color), to=room_id)

@socketio.on("keypair")
def k(username, pub_key):
    key_dict[username] = pub_key
    
@socketio.on("send_key")
def send_key(username, message, room_id):
    emit("initialization", (f"{username}: {message}"), to=room_id)
    
# join room event handler
# sent when the user joins a room
@socketio.on("join")
def join(sender_name, receiver_name):
    
    receiver = db.get_user(receiver_name)
    if receiver is None:
        return "Unknown receiver!"
    
    sender = db.get_user(sender_name)
    if sender is None:
        return "Unknown sender!"

    room_id = room.get_room_id(receiver_name)
    
    # if the user is already inside of a room 
    if room_id is not None:
        room.join_room(sender_name, room_id)
        join_room(room_id)
        
        # emit to everyone in the room except the sender
        emit("initialization", (f"{sender_name} has joined the room.", "green"), to=room_id, include_self=False)
        # emit only to the sender
        emit("initialization", (f"{sender_name} has joined the room. Now talking to {receiver_name}.", "green"))

        # send public key to get the symmetric key of the chat
        emit("initialization", (f"{sender_name}: {sender_name} pub_key {key_dict[sender_name]}"), to=room_id)
        USERS_LIST.append(sender_name)
        return room_id

    # if the user isn't inside of any room, 
    # perhaps this user has recently left a room
    # or is simply a new user looking to chat with someone
    room_id = room.create_room(sender_name, receiver_name)
    
    join_room(room_id)

    #msg = (f"{sender_name} has joined the room.", "green") 
    #emit("incoming", msg, to=room_id)

    emit("initialization", (f"{sender_name}: has joined the room :) Now talking to {receiver_name}.", "green"), to=room_id)
    # the first one to enter the room generates the secret key for everyone
    emit("generate_key", f"{sender_name} generate_key")
    if (sender_name not in USERS_LIST):
        USERS_LIST.append(sender_name)
    return room_id


# leave room event handler
@socketio.on("leave")
def leave(username, room_id):
    msg = (f"{username}: has left the room.", "red")
    emit("initialization", (msg), to=room_id)
    room.leave_room(username)
    leave_room(room_id)
    if username in USERS_LIST:
        USERS_LIST.remove(username)
