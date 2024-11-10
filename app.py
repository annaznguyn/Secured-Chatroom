'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for,  session
from flask_socketio import SocketIO
import db
import secrets
import bcrypt

# import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

app = Flask(__name__)

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
socketio = SocketIO(app)

# don't remove this!!
import socket_routes

# index page
@app.route("/")
def index():
    return render_template("index.jinja", username=None)

# login page
@app.route("/login")
def login():    
    return render_template("login.jinja", username=None)

# handles a post request when the user clicks the log in button
@app.route("/login/user", methods=["POST"])
def login_user():
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    password = request.json.get("password")

    user =  db.get_user(username)

    if user is None:
        return "Error: User does not exist!"
    
    bytes = password.encode('utf-8')
    salt = user.salt
    hash = bcrypt.hashpw(bytes, salt)

    if user.password != hash:
        return "Error: Password does not match!"
    
    token = secrets.token_hex()
    session["username"] = username
    session['token'] = token

    return url_for('friend', username=username)

# handles a get request to the signup page
@app.route("/signup")
def signup():
    return render_template("signup.jinja", username=None)

# handles a post request when the user clicks the signup button
@app.route("/signup/user", methods=["POST"])
def signup_user():
    if not request.is_json:
        abort(404)
    username = request.json.get("username")
    password = request.json.get("password")

    # hash password
    bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(bytes, salt)

    if db.get_user(username) is None:
        db.insert_user(username, hash, salt)
        
        token = secrets.token_hex()
        session["username"] = username
        session['token'] = token

        return url_for('friend', username=username)
    return "Error: User already exists!"

# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

@app.route("/start_chatting", methods=["POST"])
def start_chatting():
    if not request.is_json:
        abort(404)
    username = request.json.get("username")
    reciever = request.json.get("friend")
    return url_for('home', username=username, reciever=reciever)
    
@app.route("/home")
def home():
    if session.get('username') is None:
        abort(404)
            
    return render_template("home.jinja", username=session.get('username'), 
                           token=session.get('token'), reciever=request.args.get("reciever"))
    
  
@app.route("/friend_link", methods=["POST"])
def friend_link():
    if not request.is_json:
        abort(404)
    username = request.json.get("username")
    return url_for('friend', username=username)

@app.route("/friend")
def friend():
    if request.args.get("username") is None:
        abort(404)
    
    username = request.args.get("username")
    friendList = db.get_all_friends(username)

    return render_template("friend.jinja", username=username, friendList=friendList)

@app.route("/search_link", methods=["POST"])
def search_link():
    if not request.is_json:
        abort(404)
    username = request.json.get("username")
    return url_for('search', username=username)
    
@app.route("/search")
def search():
    if request.args.get("username") is None:
        abort(404)
    username = request.args.get("username")

    userList = db.get_all_users(username)
    friendRequestList = db.get_all_friend_requests(username)
    friendRequestList2 = db.get_all_friend_recieved_requests(username)
    for r in friendRequestList:
        if r in userList:
            userList.remove(r)
    for r in friendRequestList2:
        if r in userList:
            userList.remove(r)
    for r in db.get_all_friends(username):
        if r in userList:
            userList.remove(r)
    

    return render_template('search.jinja', username=username, friend_requests=friendRequestList, userList=userList)

@app.route("/send_request", methods=["POST"])
def send_request():
    
    if not request.is_json:
        abort(404)
   
    username = request.json.get("username")
    friend = request.json.get("friend")
    
    db.send_friend_request(username, friend)
    return url_for('search', username=username)
    

@app.route("/friend_request_link", methods=["POST"])
def friend_request_link():
    if not request.is_json:
        abort(404)
    username = request.json.get("username")
    return url_for('friend_req', username=username)

@app.route("/friend_request")
def friend_req():
    if request.args.get("username") is None:
        abort(404)
    username = request.args.get("username")

    friendRequestList = db.get_all_friend_recieved_requests(username)
    sent_friendRequestList  = db.get_all_friend_requests(username)
    
    return render_template('friend_request.jinja', username=username, 
                           friend_requests=friendRequestList, 
                           sent_friend_requests=sent_friendRequestList)


@app.route("/accept_request", methods=["POST"])
def accept_request():
    if not request.is_json:
        abort(404)
    
    username = request.json.get("username")
    friend = request.json.get("friend")

    db.accept_friend_request(friend, username)
    return url_for('friend_req', username=username)


@app.route("/retract_request", methods=["POST"])
def retract_request():
    if not request.is_json:
        abort(404)
    
    username = request.json.get("username")
    friend = request.json.get("friend")
    
    db.retract_friend_request(username, friend)
    return url_for('friend_req', username=username)


@app.route("/logout", methods=["POST"])
def logout():
    return url_for('index', username=None)


if __name__ == '__main__':
    socketio.run(app, ssl_context=('certs/cert.pem','certs/cert-key.pem'), debug=True)