import os

from dotenv import load_dotenv

from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import requests

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
    if session.get('username') is None:
        return redirect(url_for('login'))
    return render_template('home.html', on={'title': 'checked'}, home="true")

@app.route('/', methods=['POST'])
def search():
    if session.get('username') is None:
        return redirect(url_for('login'))
    search = request.form.get('search')
    option = request.form.get('option')
    if len(search) == 0:
        return render_template('home.html', on={option: 'checked'}, home="true")
    selection = {option: 'checked'}
    results = db.execute("SELECT * FROM books WHERE LOWER(" + option + ") LIKE LOWER(:search)", {'search': f'%{search}%'}).fetchmany(30)
    count = len(results)
    return render_template('home.html', results=results, search=search, on=selection, count=count, option=option)

@app.route('/books/<isbn>')
def book(isbn, error=None):
    if session.get('username') is None:
        return redirect(url_for('login'))
    if error == "empty":
        error = "Please select a rating and write a review before submitting."
    elif error == "multiple":
        error = "Please only submit one review per book."
    dbinfo = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).first()
    reviews = db.execute("SELECT * FROM reviews WHERE book_isbn = :isbn", {"isbn": isbn}).fetchall()
    # goodreads data
    r = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": API_KEY, "isbns": isbn})
    r = r.json()['books'][0]
    return render_template('book.html', book=dbinfo, err=error, reviews=reviews, data=r)

@app.route('/books/<isbn>', methods=["POST"])
def review(isbn):
    if session.get('username') is None:
        return redirect(url_for('login'))
    rating = request.form.get("rating")
    text = request.form.get("text")
    if rating is None or len(text) == 0:
        return book(isbn, error="empty")
    author_username = session.get('username')
    reviewauthors = db.execute("SELECT reviewer_username FROM reviews WHERE book_isbn = :isbn", {"isbn": isbn}).fetchall()
    if (author_username,) in reviewauthors:
        print("FOUND REVIEW ALREADY")
        return book(isbn, error="multiple")
    db.execute("INSERT INTO reviews (book_isbn, reviewer_username, rating, body) VALUES (:isbn, :author, :rating, :text)", {"isbn": isbn, "author": author_username, "rating": int(rating), "text": text})
    db.commit()
    return book(isbn)

@app.route('/api/<isbn>')
def api(isbn):
    dbinfo = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn})
    if dbinfo.rowcount == 0:
        return jsonify({"error": "invalid isbn"}), 404
    else:
        dbinfo = dbinfo.first()
    title = dbinfo[1]
    author = dbinfo[2]
    year = dbinfo[3]
    numratings = db.execute("SELECT COUNT(*) FROM reviews WHERE book_isbn = :isbn", {"isbn": isbn}).first()[0]
    avg = db.execute("SELECT AVG(rating) FROM reviews WHERE book_isbn = :isbn", {"isbn": isbn}).first()[0]
    print("---------------------", avg, "--------------------------")
    avgrating = float(avg) if avg is not None else 0
    return jsonify({
        "title": title,
        "author": author,
        "year": year,
        "isbn": isbn,
        "review_count": numratings,
        "average_score": avgrating
    })

@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    register = None
    if (request.args.get('reg')):
        register = "You have succesfully created an account. Type in your credentials to continue."
    if request.method == "POST":
        un = request.form.get('username')
        pw = request.form.get('password')
        if len(un) == 0 or len(pw) == 0:
            flash("Please enter a username and password")
        elif db.execute("SELECT * FROM users WHERE username = :username AND password = :password", {"username": un, "password": pw}).rowcount == 0:
            flash("Incorrect username or password. Please try again.", 'error')
        else:
            session['username'] = un
    if session.get('username') is not None:
        return redirect('/')
    return render_template('login.html', reg=register)

@app.route('/logout')
def logout():
    if session.get('username') is None:
        return redirect(url_for('login'))
    session['username'] = None
    return redirect(url_for('login'))

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
        if db.execute("SELECT * FROM users WHERE username = :user", {"user": u}).rowcount > 0:
            return render_template('signup.html', err="Signup failed: Username is already taken")
        db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username": u, "password": pw})
        db.commit()
        return redirect('/login?reg=yes')
