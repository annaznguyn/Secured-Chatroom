'''
db
database file, containing all the logic to interface with the sql database
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import *

from pathlib import Path

# creates the database directory
Path("database") \
    .mkdir(exist_ok=True)

# "database/main.db" specifies the database file
# change it if you wish
# turn echo = True to display the sql output
engine = create_engine("sqlite:///database/main.db", echo=False)

# initializes the database
Base.metadata.create_all(engine)

# inserts a user to the database
def insert_user(username: str, password: str, salt: str):
    with Session(engine) as session:
        user = User(username=username, password=password, salt=salt)
        session.add(user)
        session.commit()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)
    
def get_all_users(username: str):
    userList = []
    with Session(engine) as session:
        for r in session.query(User).all():
            userList.append(r.username)
    if (username in userList):
        userList.remove(username)
    return userList

def send_friend_request(user1: str, user2: str):
    exist = send_friend_request_exist(user1, user2)
    if (exist == True):
        with Session(engine) as session:
            for r in session.query(Friend).all():
                if (r.user1 == user2 and r.user2 == user1):
                    r.is_friend = "True"
                    r.requested = "False"
                    session.commit()
    else:
        with Session(engine) as session:
            f = Friend(user1=user1, user2=user2, is_friend="False", requested="True")
            session.add(f)
            session.commit()
    
def send_friend_request_exist(user1: str, user2: str):
    with Session(engine) as session:
        for r in session.query(Friend).all():
            if (r.user1 == user2 and r.user2 == user1):
                return True
    return False
    
def accept_friend_request(friend: str, username: str):
    with Session(engine) as session:
        for r in session.query(Friend).all():
            if (r.user1 == friend and r.user2 == username):
                r.is_friend = "True"
                r.requested = "False"
                create_chat(username, friend)
                create_chat(friend, username)
                session.commit()

def retract_friend_request(user1: str, user2: str):
    with Session(engine) as session:
        for r in session.query(Friend).all():
            if (r.user1 == user1 and r.user2 == user2):
                    if (r.requested == "True"):
                        session.delete(session.query(Friend).get(r.id))
                        session.commit()

def get_all_friends(username: str):
    friendList = []
    with Session(engine) as session:
        for r in session.query(Friend).all():
            if r.user1 == username:
                if (r.is_friend == "True"):
                    friendList.append(r.user2)
            if r.user2 == username:
                if (r.is_friend == "True"):
                    friendList.append(r.user1)
            
    return friendList

def get_all_friend_recieved_requests(username: str):
    friendRequestList = []
    with Session(engine) as session:
        for r in session.query(Friend).all():
            if r.user2 == username:
                if (r.requested == "True"):
                    friendRequestList.append(r.user1)
            
    if (username in friendRequestList):
        friendRequestList.remove(username)
    return friendRequestList


def get_all_friend_requests(username: str):
    friendRequestList = []
    with Session(engine) as session:
        for r in session.query(Friend).all():
            if r.user1 == username:
                if (r.requested == "True"):
                    friendRequestList.append(r.user2)
            
    if (username in friendRequestList):
        friendRequestList.remove(username)
    return friendRequestList

# inserts a user to the database
def create_chat(username: str, friend: str, msg=None, hmac=None):
    with Session(engine) as session:
        user = ChatHistory(user1=username, user2=friend, chat=msg, hmac=hmac)
        session.add(user)
        session.commit()

# gets a user from the database
def get_chat(username: str, reciever: str):
    return_val = []
    with Session(engine) as session:
        for r in session.query(ChatHistory).all():
            if (r.user1 == username and r.user2 == reciever):
                return_val.append((r.chat, r.hmac))
            
    x = []
    for r in return_val:
        if r[0] != None:
            x.append(r)
    return x
            
        
def get_history(username, reciever):
    return_val = []
    return_val = get_chat(username, reciever)
    return return_val

def store(username, reciever, msg, hmac):
    create_chat(username, reciever, msg, hmac)
