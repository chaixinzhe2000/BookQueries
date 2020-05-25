import os
import csv

from flask import Flask, session, render_template, request, redirect, url_for
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

# Set up the database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
	f = open("books.csv")
	reader = csv.reader(f)
	for isbn, title, author, year in reader:
		db.execute(
			"INSERT INTO books (book_isbn, book_title, book_author, book_year) VALUES (:isbn, :title, :author, :year)",
			{"isbn": isbn, "title": title, "author": author, "year": year},
		)
		print(
			f"Added book, ISBN is {isbn}, title is {title}, written by {author} in {year}."
		 )
	db.commit()

if __name__ == "__main__":
	main()
