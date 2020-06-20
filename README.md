# Project 1

Web Programming with Python and JavaScript

This is a user-friendly book database, where users can access information for the book and comment on it after they read it.
The main flask file is the `application.py`, where it acts as a hub to the pages of the website. In templates, there are multiple
html files that inherites from `main_template.html`. `404.html` and `405.html` are error pages, and `book_detail.html` dynamically 
presents the book information to the users. `index.html` is used for login/registration purposes. `login-failure.html` is the failure page, where the users are prompted to re-enter the passwords. `search.html` features a search bar, and leads to `search_result.html`, where another table is included. `style.css` file defines the style of the website, and multiple graphics resources are located in `static > images`.
`import.py` is included to import the book data into the data base. The tables I included in the database are books, users, and review.

The project is deployed at https://goodreads-premium.herokuapp.com/
