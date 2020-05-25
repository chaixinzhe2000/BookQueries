import os

from flask import Flask, session, render_template, request, redirect, url_for, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import requests
import math as m
from flask.json import jsonify

app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine("postgres://kzkwxxtxcphygl:d16a7a5a344ef446be22ffa78e9c061f095a361b25626b5ee3b41af1681ea30b@ec2-52-7-39-178.compute-1.amazonaws.com:5432/db71jubfass2dl")
db = scoped_session(sessionmaker(bind=engine))

log_out_sign = False;

@app.errorhandler(404)
def page_not_found(e):
	# note that we set the 404 status explicitly
	return render_template("404.html", log_out_sign = False), 404

@app.errorhandler(405)
def page_not_found(e):
	return render_template("405.html", log_out_sign = True), 405

@app.route("/")
def index():
	if session.get('login_in') is True:
		return redirect(url_for("search"))
	else:
		return render_template("index.html", log_out_sign = False)

@app.route("/idenfication", methods=["GET", "POST"])
def login_register():
	# if it is a GET request
	if request.method == "GET":
		abort(405)
	# if it is a POST request
	session.clear()
	username = request.form.get("username")
	password = request.form.get("password")
	full_name = request.form.get("full_name")
	text_split = full_name.split(" ")
	output_string = ""
	for text in text_split:
		cap_text = text.capitalize()
		output_string += cap_text + " "
	full_name = output_string
	potential_password = db.execute(
		"SELECT user_password FROM users WHERE user_username = (:username)", {"username": username}
	).fetchone()
	# if user_email is unregistered
	if potential_password is None or len(potential_password) == 0:
		# add new rows into the database
		db.execute(
			"INSERT INTO users (user_username, user_full_name, user_password) VALUES (:username, :fullname, :password)",
			{"username": username, "fullname": full_name, "password": password},
		)
		db.commit()
		user_id = db.execute("SELECT user_id, user_full_name FROM users WHERE (user_username, user_password) = (:username, :password)",
			{"username": username, "password": password}).fetchone()
		session['login_in'] = True
		session['user_id'] = user_id[0]
		session['full_name'] = user_id[1]
		return redirect("search")
	else:
		registered_user = db.execute(
			"SELECT user_password FROM users WHERE (user_username, user_password) = (:username, :password)",
			{"username": username, "password": password},
		).fetchone()
		# if user provided wrong password
		if registered_user is None or len(registered_user) == 0:
			return redirect(url_for("password_wrong"))
		else:
			session['login_in'] = True
			session.modified = True
			user_id = db.execute("SELECT user_id, user_full_name FROM users WHERE (user_username, user_password) = (:username, :password)",
			{"username": username, "password": password}).fetchone()
			session['user_id'] = user_id[0]
			session['full_name'] = user_id[1]
			return redirect(url_for("search"))

@app.route("/password-wrong")
def password_wrong():
	return render_template("login-failure.html", log_out_sign = False)

@app.route("/search")
def search():
	if session.get('login_in') is True:
		return render_template("search.html", log_out_sign = True)
	else:
		return abort(405)

@app.route("/search-result", methods=["GET", "POST"])
def search_result():
	if request.method == "GET":
		abort(405)
	keyword = request.form.get("search-text")
	keyword_capitalized = keyword.upper()
	returned_result = db.execute("SELECT * FROM books WHERE (book_isbn) ~* (:isbn) OR (book_title) ~* (:title) \
		OR (book_author) ~* (:author) OR (book_year) ~* (:year)", {"isbn": keyword, "title": keyword, "author": keyword, "year": keyword}).fetchall()
	result_length = len(returned_result)
	return render_template("search_result.html", log_out_sign = True, keyword = keyword_capitalized, result_length = result_length, result = returned_result)

@app.route("/logout")
def logout():
	session.clear()
	return redirect(url_for("index"))

@app.route("/detail/<string:isbn>", methods=["GET", "POST"])
def detail(isbn):
	# *** retrieving book data ***
	if len(isbn) != 10:
		abort(404)
	book_info = db.execute("SELECT * FROM books WHERE (book_isbn) ~* (:isbn)", {"isbn": isbn}).fetchone()
	if book_info is None or len(book_info) == 0:
		abort(404)
	key = "SSS7iIyGjukFDH1gUrxaw"
	isbn_array = []
	isbn_array.append(isbn)
	# from goodreads api
	rating_res = requests.get("https://www.goodreads.com/book/review_counts.json",
					   params={"key": key, "isbns": isbn_array})
	if rating_res.status_code != 200:
		raise Exception("ERROR: API request unsuccessful.")
	data = rating_res.json()
	isbn_13 = data["books"][0]["isbn13"]
	reviews_count = data["books"][0]["reviews_count"]
	average_rating = data["books"][0]["average_rating"]
	black_star = m.floor(float(average_rating))
	white_star = 5 - black_star
	# from openbooklibrary api
	open_url = "https://openlibrary.org/api/books?bibkeys=%s&jscmd=data&format=json" %isbn
	publisher_res = requests.get(open_url)
	if publisher_res.status_code != 200:
		raise Exception("ERROR: API request unsuccessful.")
	publisher_data = publisher_res.json()
	if len(publisher_data) == 0:
		publisher_name = "N/A"
		author_link = "https://www.google.com/search?q=%s" %book_info[3]
	else:
		publisher_name = publisher_data[isbn]["publishers"][0]["name"]
		author_link = publisher_data[isbn]["authors"][0]["url"]
	full_name = session.get('full_name')
	user_id = session.get('user_id')

	# *** adding comments ***
	if request.method == "POST":
		review_rating = request.form.get("review-rating")
		review_comment = request.form.get("review-comment")
		previous_comment = db.execute("SELECT * FROM review WHERE (review_isbn, review_user_id) = (:isbn, :id)", {"isbn": isbn, "id": user_id}).fetchall()
		# meaning there is previous comment from that user
		if len(previous_comment) != 0:
			db.execute(
				"UPDATE review SET (review_rating, review_writing) = (:rating, :writing) WHERE (review_isbn, review_user_id) = (:isbn, :id)",
				{
					"rating": review_rating,
					"writing": review_comment,
					"isbn": isbn,
					"id": user_id,
				}
			)
		else:
			db.execute(
				"INSERT INTO review (review_rating, review_writing, review_real_name, review_isbn, review_user_id) VALUES (:rating, :writing, :name, :isbn, :id)",
				{
					"rating": review_rating, 
					"writing": review_comment,
					"name": full_name,
					"isbn": book_info[1],
					"id": user_id
				}
			)
		db.commit()

	# **** fetching comments in database ****
	existing_comments = db.execute("SELECT * FROM review WHERE review_isbn = :isbn", {"isbn": book_info[1]}).fetchall()

	return render_template("book_detail.html", \
		log_out_sign = True, book_info = book_info, isbn_13 = isbn_13, average_rating = average_rating, reviews_count = reviews_count, \
		black_star = black_star, white_star = white_star, isbn = isbn, publisher = publisher_name, author_link = author_link, comments = existing_comments)

@app.route("/api/<string:isbn>")
def book_api(isbn):
	book = db.execute("SELECT * FROM books WHERE (book_isbn) = (:isbn)", {"isbn": isbn}).fetchone()
	if book is None or len(book) == 0:
		return abort(404)
	# extracting from GoodReads API
	key = "SSS7iIyGjukFDH1gUrxaw"
	isbn_array = []
	isbn_array.append(isbn)
	rating_res = requests.get("https://www.goodreads.com/book/review_counts.json",
					   params={"key": key, "isbns": isbn_array})
	if rating_res.status_code != 200:
		raise Exception("ERROR: API request unsuccessful.")
	data = rating_res.json()
	reviews_count = data["books"][0]["reviews_count"]
	average_rating = data["books"][0]["average_rating"]
	return jsonify({
			"title": book[2],
    		"author": book[3],
			"year": book[4],
    		"isbn": book[1],
    		"review_count": reviews_count,
    		"average_score": average_rating
		})