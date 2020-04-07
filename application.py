import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

API_KEY = os.getenv("API_KEY")

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/fail")
def login_fail():
    return render_template("login_fail")

@app.route("/register")
def signup():
    return render_template("signup.html")

@app.route("/register_sucess", methods=["POST"])
def register_success():
    return render_template("register_sucess.html")

@app.route("/home", methods=["POST"])
def home():
    if db.execute("SELECT * FROM users WHERE username = :username AND password = :password", {"username": request.form.get('username'), "password": request.form.get('password')}).rowcount != 0:
        return "Logged in"
    return login_fail()
