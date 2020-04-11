import os

from dotenv import load_dotenv

from flask import Flask, session, render_template, request, redirect, url_for, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

load_dotenv()

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

@app.route('/')
def home():
    if session.get('logged_in') is False:
        return redirect(url_for('login'))
    else:
        return render_template('home.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    register = None
    if (request.args.get('reg')):
        register = "You have succesfully created an account. Type in your credentials to continue."
    if request.method == "POST":
        if db.execute("SELECT * FROM users WHERE username = :username AND password = :password", {"username": request.form.get('username'), "password": request.form.get('password')}).rowcount == 0:
            error = "Incorrect username or password. Please try again."
        else:
            session['logged_in'] = True
    if session.get('logged_in') == True:
        return redirect(url_for('home'))
    return render_template('login.html', err=error, reg=register)

@app.route('/logout')
def logout():
    session['logged_in'] = False
    return redirect(url_for('home'))

@app.route('/signup', methods=["POST", "GET"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    else:
        u = request.form.get('username')
        pw = request.form.get('password')
        if u == "" or pw == "":
            return render_template('signup.html', err="Signup failed: Username or password cannot be empty")
        if len(u) > 20:
            return render_template('signup.html', err="Signup failed: Username may not be above 20 characters")
        if len(pw) > 200:
            return render_template('signup.html', err="Signup failed: Password may not be above 200 characters")
        db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username": u, "password": pw})
        db.commit()
        return redirect('/login?reg=yes')
