__authors__ = "Uday Cheedella"
__version__ = "1.0"

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import send_file
from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy
from jinja2 import *
from sqlalchemy.orm import relationship
from sqlalchemy import desc
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
#from datetime import datetime
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///library_mgmt_project_database.sqlite3"
db = SQLAlchemy()
db.init_app(app)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
app.app_context().push()


#DB model
class admin(db.Model):
    __tablename__ = 'admin'
    admin_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    admin_name = db.Column(db.String, unique=True, nullable=False, default="admin")
    password = db.Column(db.String, nullable=False)

class users(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_name = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String)
    book_issue_cascade = relationship("bookIssue", cascade="all, delete-orphan")
    book_request_cascade = relationship("bookRequest", cascade="all, delete-orphan")
    user_notifications_cascade = relationship("userNotifications", cascade="all, delete-orphan")
    user_book_rating_cascade = relationship("userBookRating", cascade="all, delete-orphan")
    book_purchase_cascade = relationship("bookPurchase", cascade="all, delete-orphan")
    
    
class sections(db.Model):
    __tablename__ = 'sections'
    section_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    section_name = db.Column(db.String, unique=True, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False)
    section_description = db.Column(db.String)
    books_cascade = relationship("books", cascade="all, delete-orphan")
    
class books(db.Model):
    __tablename__ = 'books'
    book_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    book_name = db.Column(db.String, unique=True, nullable=False)
    book_content = db.Column(db.String, nullable=False)
    book_author = db.Column(db.String, nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.section_id'))
    date_created = db.Column(db.DateTime, nullable=False)
    book_price = db.Column(db.Integer, nullable = False)
    book_issue_cascade = relationship("bookIssue", cascade="all, delete-orphan")
    book_request_cascade = relationship("bookRequest", cascade="all, delete-orphan")
    user_book_rating_cascade = relationship("userBookRating", cascade="all, delete-orphan")
    book_rating_cascade = relationship("bookRating", cascade="all, delete-orphan")
    book_purchase_cascade = relationship("bookPurchase", cascade="all, delete-orphan")

class bookIssue(db.Model):
    __tablename__ = "bookIssue"
    issue_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'))
    date_issued = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime, nullable=False)

class bookRequest(db.Model):
    __tablename__ = "bookRequest"
    request_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id')) 
    no_of_days = db.Column(db.Integer, nullable=False)
    
class userNotifications(db.Model):
    __tablename__ = "userNotifications"
    notification_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    notification = db.Column(db.String, nullable=False)
    date_of_notification = db.Column(db.DateTime, nullable=False)

class userBookRating(db.Model):
    __tablename__ = "userBookRating"
    rating_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'))
    rating = db.Column(db.Integer)

class bookRating(db.Model):
    __tablename__ = "bookRating"
    rating_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'))
    avg_rating = db.Column(db.Integer)
    count = db.Column(db.Integer)

class bookPurchase(db.Model):
    __tablename__ = "bookPurchase"
    purchase_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'))

class adminTools(db.Model):
    __tablename__ = "adminTools"
    tool_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    max_book_requests_per_user = db.Column(db.Integer, default=5)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup/', methods = ["GET", "POST"])
def signup():
    first_name, last_name, uname, password = "", "", "", ""
    if request.method == "POST":
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        uname = request.form['username']
        password = request.form['password']
        
        # #print(uname, password)
        found = users.query.filter_by(user_name=uname).first()
        if not found:
            add_user = users(user_name = uname, first_name = first_name, last_name = last_name, password = password)
            db.session.add(add_user)
            db.session.commit()
            welcome_message = f"Welcome User: {uname}"
            createNotification(uname, datetime.datetime.now(), welcome_message)
            return render_template("user_created.html", user_name = uname)
        else:
            error_message = f"Error: Username '{uname}' already exists! Please choose a different username!"
            return render_template("signup_page.html", error_message=error_message, first_name= first_name, last_name= last_name, username = uname, password = password)
    return render_template('signup_page.html')

@app.route('/user_login/', methods = ["GET", "POST"])
def user_login():
    if request.method == "POST":
        uname = request.form['username']
        password = request.form['password']
        
        # #print(uname, password)
        found = users.query.filter_by(user_name=uname).first()
        if not found:
            return render_template("user_not_exist.html")
        else:
            if found.password == password:
                return redirect("/users/" + uname)
            else:
                return render_template('login_page.html', error_message = "Error: Password Incorrect, Please try again.")
    return render_template('login_page.html', error_message = "")

def init_admin(uname, password):
    new_admin = admin(admin_name = uname, password = password)
    db.session.add(new_admin)
    new_tool = adminTools(max_book_requests_per_user = 5)
    db.session.add(new_tool)
    db.session.commit()

@app.route('/admin_login/', methods = ["GET", "POST"])
def admin_login():
    if request.method == "POST":
        uname = request.form['username']
        password = request.form['password']
        
        # #print(uname, password)
        details = admin.query.filter_by(admin_name=uname).first()
        if details:
            if details.admin_name != uname:
                return render_template('admin_login.html', error_message = "Error: Admin name Incorrect, Please try again.")
            else:
                if details.password == password:
                    return redirect("/librarian/dashboard")
                else:
                    return render_template('admin_login.html', error_message = "Error: Password Incorrect, Please try again.")
        else:
            init_admin(uname="admin", password = "password")
            return render_template('admin_login.html', error_message = "Error: Admin not configured, Please try again after sometime.")

    return render_template('admin_login.html')

@app.route("/librarian")
def admin_def_page():
    return redirect("/librarian/dashboard")

@app.route("/librarian/dashboard", methods = ["GET", "POST"])
@app.route("/sections/", methods = ["GET", "POST"])
def admin_dashboard():
    sections_details_all = sections.query.all()
    sections_details = []
    
    search_string = request.args.get('search_string', '')

    for section in sections_details_all:
        if search_string in section.section_name:
            sections_details.append(section)

    return render_template('librarian_dashboard.html', sections_details = sections_details, search_string = search_string)

@app.route("/librarian/tools/", methods = ["GET", "POST"])
def admin_tools():
    admin_tools = adminTools.query.first()
    if admin_tools:
        curr_max_requests = admin_tools.max_book_requests_per_user
    else:
        curr_max_requests = '-'
    error_message, success_message = '', ''
    if request.method == "POST":
        max_book_requests_per_user = request.form.get('max_book_requests_per_user')

        if admin_tools:
            admin_tools.max_book_requests_per_user = max_book_requests_per_user
            db.session.commit()
            success_message = "Success: Changes Saved!"
        else:
            error_message = "Error: Error saving changes!"

    return render_template('admin_tools.html', error_message = error_message, success_message = success_message, curr_max_requests = curr_max_requests)

@app.route("/librarian/stats", methods = ["GET", "POST"])
def admin_stats():
    user_count = getUsersCount()
    section_count = getSectionsCount()
    books_count = getBooksCount()
    book_requests_count = getBookRequestsCount()
    book_issue_count = getBookIssueCount()

    return render_template('librarian_stats.html', user_count = user_count, section_count = section_count, books_count = books_count,
                           book_requests_count = book_requests_count, book_issue_count = book_issue_count)


@app.route("/librarian/change_password", methods = ["GET", "POST"])
def admin_change_pass():
    if request.method == "POST":
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']
        if new_password != confirm_new_password:
            return render_template('librarian_changepass.html', error_message = "Error: Passwords do not match.")
        # #print(uname, password)
        details = admin.query.all()
        details[0].password = new_password
        db.session.commit()
        return render_template('librarian_changepass.html', success_message = "Success: Admin password Changed Successfully.")
    return render_template('librarian_changepass.html')

@app.route("/sections/create", methods = ["GET", "POST"])
def section_create():
    if request.method == "POST":
        section_name = request.form.get('section_name')
        section_description = request.form.get('section_description')
        
        found = sections.query.filter_by(section_name=section_name).first()
        if not found:
            new_section = sections(section_name = section_name, section_description = section_description, date_created = datetime.datetime.now())
            db.session.add(new_section)
            db.session.commit()
            return redirect('/librarian')
        else:
            return render_template('section_create.html', error_message = "Error: " + section_name + " already exists!")
    return render_template('section_create.html')

@app.route("/sections/<section_id>/update", methods = ["GET", "POST", "PUT"])
def section_update(section_id):
    if request.method == "POST":
        section_name = request.form.get('section_update_name')
        section_description = request.form.get('section_update_description')
        section_details = sections.query.filter_by(section_id = section_id).first()
        if not section_details:
            return redirect('/sections')
        else:
            # section_details.section_name = section_name
            section_details.section_description = section_description
            db.session.commit()
            return redirect('/sections')

    section_details = sections.query.filter_by(section_id = section_id).first()
    print(section_details.section_description)
    return render_template("section_update.html", section_details = section_details, section_id = section_id)


@app.route("/sections/<section_id>/delete", methods = ["GET", "POST"])
def section_delete(section_id):
    section_details = sections.query.filter_by(section_id=section_id).first()
    
    # Get the search parameters from the URL
    search_string = request.args.get('search_string', '')

    if not section_details:
        return redirect(f'/sections?search_string={search_string}')
    db.session.delete(section_details)
    db.session.commit()
    return redirect(f'/sections?search_string={search_string}')

@app.route("/sections/<section_id>", methods = ["GET", "POST"])
def section_view(section_id):
    
    # Get the search parameters from the URL
    search_string = request.args.get('search_string', '')
    search_select = request.args.get('search_select', '')
    section_list_select = request.args.get('section_list_select')

    noFilter = False
    if search_select == "" and search_string == "":
        noFilter = True
    books_details_all = books.query.filter_by(section_id=section_id)
    section_all = sections.query.all()
    section_list = []
    for section in section_all:
        section_list.append(section)
    section_name = sections.query.filter_by(section_id = section_id).first().section_name
    books_details = []
    for book in books_details_all:
        found = bookRating.query.filter_by(book_id = book.book_id).first()
        if found:
            avg_rating= found.avg_rating
            count = found.count
        else:
            avg_rating= '--'
            count = '--'
        addEntry = {
            "book_id": book.book_id,
            "book_name": book.book_name,
            "section_id": book.section_id,
            "book_author": book.book_author,
            "book_price": book.book_price,
            "avg_rating": avg_rating,
            "count": count,
        }
        if search_select == 'book_name' and search_string in book.book_name:
            books_details.append(addEntry)
        elif search_select == 'book_author' and search_string in book.book_author:
            books_details.append(addEntry)
        if noFilter:            
            books_details.append(addEntry)
    return render_template('section_view.html', section_list = section_list, section_id = section_id, section_name = section_name, books_details = books_details, search_string=search_string, search_select = search_select)

@app.route("/sections/<section_id>/books/create", methods = ["GET", "POST"])
def book_create(section_id):
    if request.method == "POST":
        book_name = request.form.get('book_name')
        book_author = request.form.get('book_author')
        book_content = request.form.get('book_content')
        book_price = request.form.get('book_price')
        
        found = books.query.filter_by(book_name=book_name).first()
        if not found:
            new_book = books(book_name = book_name, book_author = book_author, book_content = book_content, section_id = section_id, date_created = datetime.datetime.now(), book_price = book_price)
            db.session.add(new_book)
            db.session.commit()
            return redirect('/sections/' + section_id)
        else:
            return render_template('book_create.html', error_message = "Error: " + book_name + " already exists!", section_id = section_id)
    return render_template("book_create.html", section_id = section_id)

@app.route("/move_to_another_section/<book_id>/<org_section_id>")
def move_book_to_another_section(book_id, org_section_id):
    
    # Get the search parameters from the URL
    search_string = request.args.get('search_string', '')
    search_select = request.args.get('search_select', '')
    section_id = request.args.get('section_list_select')
    book_details = books.query.filter_by(book_id = book_id).first()
    book_details.section_id = section_id
    db.session.commit()
    
    return redirect(f'/sections/{org_section_id}?search_string={search_string}&search_select={search_select}&section_list_select={section_id}')


@app.route("/books/<book_id>/update", methods = ["GET", "POST", "PUT"])
def book_update(book_id):
    if request.method == "POST":
        book_name = request.form.get('book_name')
        book_author = request.form.get('book_author')
        book_content = request.form.get('book_content')
        book_price = request.form.get('book_price')
        book_details = books.query.filter_by(book_id = book_id).first()
        try:
            section_id = book_details.section_id
        except:
            return redirect('/sections/')
        if not book_details:
            return redirect('/sections/' + section_id)
        else:
            book_details.book_author = book_author
            book_details.book_content = book_content
            book_details.book_price = book_price
            db.session.commit()
            return redirect('/sections/' + str(section_id))
        
    book_details = books.query.filter_by(book_id = book_id).first()
    section_id = book_details.section_id
    return render_template("book_update.html", book_details = book_details, section_id = section_id)

@app.route("/books/<book_id>/user_view/<user_id>", methods = ["GET", "POST"])
def user_book_view(book_id, user_id):
    user_details = users.query.filter_by(user_id = user_id).first()
    book_details = books.query.filter_by(book_id=book_id).first()
    window = request.args.get("mybooks")
    section_id = book_details.section_id
    return render_template("user_book_view.html", username = user_details.user_name, book_details = book_details, window = window)

@app.route("/books/<book_id>/librarian_view", methods = ["GET", "POST"])
def librarian_book_view(book_id):
    book_details = books.query.filter_by(book_id=book_id).first()
    if not book_details:
        return render_template('book_view.html', error_message = "Error: " + book_details.book_name + " does not exist!")
    section_id = book_details.section_id
    return render_template("librarian_book_view.html", section_id = section_id, book_details = book_details)

@app.route("/books/<book_id>/delete", methods = ["GET", "POST"])
def book_delete(book_id):
    book_details = books.query.filter_by(book_id=book_id).first()
    section_id = book_details.section_id
    
    # Get the search parameters from the URL
    search_string = request.args.get('search_string', '')
    search_select = request.args.get('search_select', '')
    if not book_details:
        return redirect(f'/sections/{section_id}?search_string={search_string}&search_select={search_select}')
    db.session.delete(book_details)
    db.session.commit()
    return redirect(f'/sections/{section_id}?search_string={search_string}&search_select={search_select}')

@app.route("/books/requests/", methods = ["GET", "POST"])
def book_requests():
    book_request_all = bookRequest.query.all()
    book_details = books.query.all()
    user_details = users.query.all()
    book_request_details = []
    
    # Get the search parameters from the URL
    search_string = request.args.get('search_string', '')
    search_select = request.args.get('search_select', '')

    noFilter = False
    if search_select == "" and search_string == "":
        noFilter = True

    for req in book_request_all:
        user_name = users.query.filter_by(user_id = req.user_id).first().user_name
        book_name = books.query.filter_by(book_id = req.book_id).first().book_name
        addEntry = {
                    "user_name": user_name,
                    "book_name": book_name,
                    "request_id": req.request_id,
                    "user_id": req.user_id,
                    "book_id": req.book_id,
                    "requested_days": req.no_of_days
                    }
        if search_select == 'book_name' and search_string in book_name:
            book_request_details.append(addEntry)
        elif search_select == 'user_name' and search_string in user_name:
            book_request_details.append(addEntry)
        if noFilter:            
            book_request_details.append(addEntry)
    return render_template("book_requests.html", book_request_list = book_request_details, search_select=search_select, search_string=search_string)

@app.route("/books/issuance", methods = ["GET", "POST"])
def book_issuance():
    book_issue_all = bookIssue.query.order_by(bookIssue.return_date).all()
    book_issue_details = []

    # Get the search parameters from the URL
    search_string = request.args.get('search_string', '')
    search_select = request.args.get('search_select', '')

    noFilter = False
    if search_select == "" and search_string == "":
        noFilter = True

    for issue in book_issue_all:
        user_name = users.query.filter_by(user_id = issue.user_id).first().user_name
        book_name = books.query.filter_by(book_id = issue.book_id).first().book_name
        addEntry = {
                    "user_name": user_name,
                    "book_name": book_name,
                    "issue_id": issue.issue_id,
                    "user_id": issue.user_id,
                    "book_id": issue.book_id,
                    "doi": issue.date_issued,
                    "dor": issue.return_date
                    }
        if search_select == 'book_name' and search_string in book_name:
            book_issue_details.append(addEntry)
        elif search_select == 'user_name' and search_string in user_name:
            book_issue_details.append(addEntry)
        if noFilter:   
            book_issue_details.append(addEntry)

    
    
    datenow = datetime.datetime.now()
    issued_book_details = []
    for book in book_issue_details:
        if book["dor"] <= datenow + datetime.timedelta(days=1):
            book["color"] = "red"
        elif book["dor"] <= datenow + datetime.timedelta(days=2):
            book["color"] = "orange"
        else:
            book["color"] = "green"
        issued_book_details.append(book)

    return render_template("book_issuance.html", issued_book_details = issued_book_details, search_string = search_string, search_select = search_select)


@app.route("/books/<book_id>/request/<user>", methods = ["GET", "POST"])
def user_book_request(book_id, user):
    user_details = users.query.filter_by(user_name = user).first()
    user_id = user_details.user_id
    found = bookRequest.query.filter_by(book_id = book_id).filter_by(user_id = user_id).first()
    all_user_requests = bookRequest.query.filter_by(user_id = user_id)
    count = 0
    for req in all_user_requests:
        count += 1
    
    no_of_days = request.args.get('no_of_days', 5)

    max_req_tool = adminTools.query.first()
    if max_req_tool:
        max_req = max_req_tool.max_book_requests_per_user
    
    error_message, success_message = '', ''
    if count >= max_req:
        error_message = "Error: Maximum book Requests for this user reached!"
    else:
        book_name = books.query.filter_by(book_id = book_id).first().book_name
        success_message = f"Success: Request for Book: '{book_name}' raised successfully"

    if not found and count < max_req:
        new_request = bookRequest(book_id = book_id, user_id=user_id, no_of_days = int(no_of_days))
        db.session.add(new_request)
        db.session.commit()
        
        notification = "Request raised for Book: '" + books.query.filter_by(book_id = book_id).first().book_name + "' for " + str(no_of_days) + " days!"
        createNotification(users.query.filter_by(user_id = user_id).first().user_name, datetime.datetime.now(), notification) 

    
    # Get the search parameters from the form
    search_string = request.args.get('search_string', '')
    search_select = request.args.get('search_select', '')
    window = request.args.get('window')
    section_list_select = request.args.get('section_list_select', '')

    #Redirect with the search parameters
    return redirect(f'/users/{user}/{window}?search_string={search_string}&search_select={search_select}&error_message={error_message}&success_message={success_message}&section_list_select={section_list_select}')


@app.route("/books/<book_id>/request/<user_id>/reject", methods = ["GET", "POST"])
def user_book_request_reject(book_id, user_id):
    found = bookRequest.query.filter_by(book_id = book_id).filter_by(user_id = user_id).first()

    notification = "Request for Book: '" + books.query.filter_by(book_id = book_id).first().book_name + "' for " + str(found.no_of_days) + " days has been Rejected!"
    createNotification(users.query.filter_by(user_id = user_id).first().user_name, datetime.datetime.now(), notification)
     
 
    if found:
        db.session.delete(found)
        db.session.commit()

    
    # Get the search parameters from the form
    search_string = request.args.get('search_string', '')
    search_select = request.args.get('search_select', '')
    
    #Redirect with the search parameters
    return redirect(f'/books/requests?search_string={search_string}&search_select={search_select}')


@app.route("/books/<book_id>/request/<user_id>/grant", methods = ["GET", "POST"])
def user_book_request_grant(book_id, user_id):
    found = bookRequest.query.filter_by(book_id = book_id).filter_by(user_id = user_id).first()
    no_of_days = found.no_of_days
    
    notification = "Request for Book: '" + books.query.filter_by(book_id = book_id).first().book_name + "' for " + str(no_of_days) + " days has been Granted!"
    createNotification(users.query.filter_by(user_id = user_id).first().user_name, datetime.datetime.now(), notification)
    
    if found:
        db.session.delete(found)
        newBookIssue = bookIssue(user_id = user_id, book_id = book_id, date_issued = datetime.datetime.today(), return_date = datetime.datetime.today() + datetime.timedelta(days=no_of_days))
        db.session.add(newBookIssue)
        db.session.commit()
    
    
    # Get the search parameters from the form
    search_string = request.args.get('search_string', '')
    search_select = request.args.get('search_select', '')

    #Redirect with the search parameters
    return redirect(f'/books/requests?search_string={search_string}&search_select={search_select}')
    


@app.route("/books/<book_id>/request/<user_id>/cancel", methods = ["GET", "POST"])
def user_book_request_cancel(book_id, user_id):
    found = bookRequest.query.filter_by(book_id = book_id).filter_by(user_id = user_id).first()
    no_of_days = found.no_of_days
    user_details = users.query.filter_by(user_id = user_id).first()
    
    notification = "Request for Book: '" + books.query.filter_by(book_id = book_id).first().book_name + "' for " + str(no_of_days) + " days has been Cancelled!"
    createNotification(users.query.filter_by(user_id = user_id).first().user_name, datetime.datetime.now(), notification)
    
    if found:
        db.session.delete(found)
        db.session.commit()
    
    
    # Get the search parameters from the form
    search_string = request.args.get('search_string', '')
    search_select = request.args.get('search_select', '')

    #Redirect with the search parameters
    return redirect(f'/users/{user_details.user_name}/mybooks/requested_books?search_string={search_string}&search_select={search_select}')
    


@app.route("/books/<book_id>/purchase/<user>", methods = ["GET", "POST"])
def user_book_purchase(book_id, user):
    user_details = users.query.filter_by(user_name = user).first()
    user_id = user_details.user_id
    found = bookPurchase.query.filter_by(book_id = book_id).filter_by(user_id = user_id).first()

    notification = "Purchase of Book: '" + books.query.filter_by(book_id = book_id).first().book_name + "' is Successful!"
    createNotification(users.query.filter_by(user_id = user_id).first().user_name, datetime.datetime.now(), notification) 

    if not found:
        new_purchase = bookPurchase(book_id = book_id, user_id=user_id)
        db.session.add(new_purchase)
        book_request = bookRequest.query.filter_by(book_id = book_id).filter_by(user_id = user_id).first()
        if book_request:
            notification = "Request for Book: '" + books.query.filter_by(book_id = book_id).first().book_name + "' has been Auto-Cancelled as you purchased this book!"
            createNotification(users.query.filter_by(user_id = user_id).first().user_name, datetime.datetime.now(), notification)
            db.session.delete(book_request)
        book_issue = bookIssue.query.filter_by(book_id = book_id).filter_by(user_id = user_id).first()
        if book_request:
            notification = "Issuance for Book: '" + books.query.filter_by(book_id = book_id).first().book_name + "' has been Auto-Revoked as you purchased this book!"
            createNotification(users.query.filter_by(user_id = user_id).first().user_name, datetime.datetime.now(), notification)
            db.session.delete(book_issue)
        book_name = books.query.filter_by(book_id = book_id).first().book_name
        success_message = f"Success: Purchased Book: '{book_name}' successfully"
        db.session.commit()
    
    # Get the search parameters from the form
    search_string = request.args.get('search_string', '')
    search_select = request.args.get('search_select', '')
    section_list_select = request.args.get('section_list_select', '')
    print(search_select)
    print(search_string)
    
    

    #Redirect with the search parameters
    return redirect(f'/users/{user}/books?search_string={search_string}&search_select={search_select}&success_message={success_message}&section_list_select={section_list_select}')



@app.route("/books/<book_id>/issue/<user_id>/revoke", methods = ["GET", "POST"])
def user_book_issue_revoke(book_id, user_id):
    found = bookIssue.query.filter_by(book_id = book_id).filter_by(user_id = user_id).first()
    
    notification = "Access for Book: '" + books.query.filter_by(book_id = book_id).first().book_name + "' has been revoked!"
    createNotification(users.query.filter_by(user_id = user_id).first().user_name, datetime.datetime.now(), notification)
    
    if found:
        db.session.delete(found)
        db.session.commit()
   
    # Get the search parameters from the form
    search_string = request.args.get('search_string', '')
    search_select = request.args.get('search_select', '')

    # Redirect with the search parameters
    return redirect(f'/books/issuance?search_string={search_string}&search_select={search_select}')


@app.route("/books/<book_id>/return/<user_id>", methods = ["GET", "POST"])
def user_book_return(book_id, user_id):
    user_details = users.query.filter_by(user_id = user_id).first()
    found = bookIssue.query.filter_by(book_id = book_id).filter_by(user_id = user_id).first()
    if found:
        db.session.delete(found)
        db.session.commit()

    # Get the search parameters from the form
    search_string = request.args.get('search_string', '')
    search_select = request.args.get('search_select', '')

    #Redirect with the search parameters
    return redirect(f'/users/{user_details.user_name}/mybooks?search_string={search_string}&search_select={search_select}')

@app.route('/users/<user>')
def user_def_page(user):
    return redirect("/users/" + user + "/dashboard")

@app.route('/users/<user>/dashboard')
def user_dashboard(user):

    error_message = request.args.get('error_message', '')
    success_message = request.args.get('success_message', '')
    
    top_rated_books = getTopRatedBooks(user)
    recently_added_books = getRecentlyAddedBooks(user)
    return render_template('user_dashboard.html', username = user, top_rated_books = top_rated_books,recently_added_books = recently_added_books, notification_count = getNotificationCount(user), error_message=error_message, success_message=success_message)

@app.route('/users/<user>/mybooks', methods=["GET", "POST"])
@app.route('/users/<user>/mybooks/issued_books', methods = ["GET", "POST"])
def user_mybooks_issued_books(user):
    user_details = users.query.filter_by(user_name = user).first()
    user_id = user_details.user_id
    book_issue_details = bookIssue.query.order_by(bookIssue.return_date).filter_by(user_id = user_id)
    user_issued_book_details = []
    
    # Get the search parameters from the URL
    search_string = request.args.get('search_string', '')
    search_select = request.args.get('search_select', '')
    error_message = request.args.get('error_message', '')
    success_message = request.args.get('success_message', '')

    noFilter = False
    if search_select == "" and search_string == "":
        noFilter = True
    for issue in book_issue_details:
        user_name = users.query.filter_by(user_id = issue.user_id).first().user_name
        book_details = books.query.filter_by(book_id = issue.book_id).first()
        book_name = book_details.book_name
        book_author = book_details.book_author
        book_price = book_details.book_price
        found = bookRating.query.filter_by(book_id = issue.book_id).first()
        section_name = sections.query.filter_by(section_id = book_details.section_id).first().section_name
        if found:
            avg_rating= found.avg_rating
            count = found.count
        else:
            avg_rating= '--'
            count = '--'
        user_rating = "select"
        found = userBookRating.query.filter_by(user_id = issue.user_id).filter_by(book_id = issue.book_id).first()
        if found:
            user_rating = found.rating
        addEntry = {
                    "user_name": user_name,
                    "book_name": book_name,
                    "book_author": book_author,
                    "issue_id": issue.issue_id,
                    "user_id": issue.user_id,
                    "book_id": issue.book_id,
                    "doi": issue.date_issued,
                    "dor": issue.return_date,
                    "section_name": section_name,
                    "avg_rating": avg_rating,
                    "count": count,
                    "user_rating": user_rating,
                    "book_price": book_price
                    }
        if search_select == 'book_name' and search_string in book_name:
            user_issued_book_details.append(addEntry)
        elif search_select == 'book_author' and search_string in book_author:
            user_issued_book_details.append(addEntry)
        if noFilter:            
            user_issued_book_details.append(addEntry)

    datenow = datetime.datetime.now()
    issued_book_details = []
    for book in user_issued_book_details:
        if book["dor"] <= datenow + datetime.timedelta(days=1):
            book["color"] = "red"
        elif book["dor"] <= datenow + datetime.timedelta(days=2):
            book["color"] = "orange"
        else:
            book["color"] = "green"
        issued_book_details.append(book)

    return render_template("user_mybooks_issued.html", username = user, issued_book_details = issued_book_details, error_message=error_message, success_message=success_message, search_string = search_string, search_select = search_select, notification_count = getNotificationCount(user))


@app.route('/users/<user>/mybooks/requested_books', methods = ["GET", "POST"])
def user_mybooks_requested_books(user):
    user_details = users.query.filter_by(user_name = user).first()
    user_id = user_details.user_id
    book_request_details = bookRequest.query.filter_by(user_id = user_id)
    user_requested_book_details = []
    
    # Get the search parameters from the URL
    search_string = request.args.get('search_string', '')
    search_select = request.args.get('search_select', '')
    error_message = request.args.get('error_message', '')
    success_message = request.args.get('success_message', '')

    noFilter = False
    if search_select == "" and search_string == "":
        noFilter = True
    for book in book_request_details:
        user_name = users.query.filter_by(user_id = book.user_id).first().user_name
        book_details = books.query.filter_by(book_id = book.book_id).first()
        book_name = book_details.book_name
        book_author = book_details.book_author
        book_price = book_details.book_price
        section_name = sections.query.filter_by(section_id = book_details.section_id).first().section_name
        found = bookRating.query.filter_by(book_id = book.book_id).first()
        if found:
            avg_rating= found.avg_rating
            count = found.count
        else:
            avg_rating= '--'
            count = '--'
        addEntry = {
                    "user_name": user_name,
                    "book_name": book_name,
                    "book_author": book_author,
                    "request_id": book.request_id,
                    "user_id": book.user_id,
                    "book_id": book.book_id,
                    "book_price": book_price,
                    "requested_days": book.no_of_days,
                    "avg_rating": avg_rating,
                    "count": count,
                    "section_name": section_name
                    }
        if search_select == 'book_name' and search_string in book_name:
            user_requested_book_details.append(addEntry)
        elif search_select == 'book_author' and search_string in book_author:
            user_requested_book_details.append(addEntry)
        if noFilter:            
            user_requested_book_details.append(addEntry)


    return render_template("user_mybooks_requested.html", username = user, requested_book_details = user_requested_book_details, error_message=error_message, success_message=success_message, search_string = search_string, search_select = search_select, notification_count = getNotificationCount(user))

@app.route('/users/<user>/mybooks/purchased_books', methods = ["GET", "POST"])
def user_mybooks_purchased_books(user):
    user_details = users.query.filter_by(user_name = user).first()
    user_id = user_details.user_id
    book_purchase_details = bookPurchase.query.filter_by(user_id = user_id)
    user_purchase_book_details = []
    
    # Get the search parameters from the URL
    search_string = request.args.get('search_string', '')
    search_select = request.args.get('search_select', '')
    error_message = request.args.get('error_message', '')
    success_message = request.args.get('success_message', '')

    noFilter = False
    if search_select == "" and search_string == "":
        noFilter = True
    for book in book_purchase_details:
        user_name = users.query.filter_by(user_id = book.user_id).first().user_name
        book_details = books.query.filter_by(book_id = book.book_id).first()
        book_name = book_details.book_name
        book_author = book_details.book_author
        section_name = sections.query.filter_by(section_id = book_details.section_id).first().section_name
        found = bookRating.query.filter_by(book_id = book.book_id).first()
        if found:
            avg_rating= found.avg_rating
            count = found.count
        else:
            avg_rating= '--'
            count = '--'
        user_rating = "select"
        found = userBookRating.query.filter_by(user_id = book.user_id).filter_by(book_id = book.book_id).first()
        if found:
            user_rating = found.rating
        addEntry = {
                    "user_name": user_name,
                    "book_name": book_name,
                    "book_author": book_author,
                    "purchase_id": book.purchase_id,
                    "user_id": book.user_id,
                    "book_id": book.book_id,
                    "avg_rating": avg_rating,
                    "count": count,
                    "user_rating": user_rating,
                    "section_name": section_name
                    }
        if search_select == 'book_name' and search_string in book_name:
            user_purchase_book_details.append(addEntry)
        elif search_select == 'book_author' and search_string in book_author:
            user_purchase_book_details.append(addEntry)
        if noFilter:            
            user_purchase_book_details.append(addEntry)


    return render_template("user_mybooks_purchased.html", username = user, purchased_book_details = user_purchase_book_details, error_message=error_message, success_message=success_message, search_string = search_string, search_select = search_select, notification_count = getNotificationCount(user))


@app.route('/users/<user>/books', methods = ["GET", "POST"])
def user_books(user):
    user_details = users.query.filter_by(user_name = user).first()
    section_list = sections.query.all()
    
    # Get the search parameters from the URL
    search_string = request.args.get('search_string', '')
    search_select = request.args.get('search_select', '')
    error_message = request.args.get('error_message', '')
    success_message = request.args.get('success_message', '')
    args_section_id = request.args.get("section_list_select")
    if args_section_id in ["all", "", None]:
        all_book_details = books.query.all()
        args_section_name = "All"
    else:
        all_book_details = books.query.filter_by(section_id = args_section_id)
        args_section_name = sections.query.filter_by(section_id = args_section_id).first().section_name
        
    already_user_books = bookIssue.query.filter_by(user_id = user_details.user_id)
    already_requested_books = bookRequest.query.filter_by(user_id = user_details.user_id)
    
    requested_books = []
    for book in already_requested_books:
        requested_books.append(str(book.book_id))
    
    book_list = []
    already_book_ids = []


    noFilter = False
    if search_select == "" and search_string == "":
        noFilter = True
    for book in already_user_books:
        already_book_ids.append(str(book.book_id))
    for book in all_book_details:
        have_access = False
        have_requested = False
        have_purchased = False
        section_name = sections.query.filter_by(section_id = book.section_id).first().section_name
        if str(book.book_id) in already_book_ids:
            have_access = True
        if str(book.book_id) in requested_books:
            have_requested = True
        found = bookPurchase.query.filter_by(book_id = book.book_id).filter_by(user_id = user_details.user_id).first()
        if found:
            have_purchased = True
        found = bookRating.query.filter_by(book_id = book.book_id).first()
        if found:
            avg_rating= found.avg_rating
            count = found.count
        else:
            avg_rating= '--'
            count = '--'
        addEntry = {
                "book_name": book.book_name,
                "book_author": book.book_author,
                "book_id": book.book_id,
                "avg_rating": avg_rating,
                "count": count,
                "have_access": have_access,
                "have_requested": have_requested,
                "have_purchased": have_purchased,
                "section_name": section_name,
                "book_price": book.book_price
                }
        if search_select == 'book_name' and search_string in book.book_name:
            book_list.append(addEntry)
        elif search_select == 'book_author' and search_string in book.book_author:
            book_list.append(addEntry)
        if noFilter:
            book_list.append(addEntry)
                
    return render_template('user_books.html', section_list = section_list, args_section_name=args_section_name, username = user, book_list = book_list, requested_books = requested_books, search_string = search_string, search_select = search_select, section_list_select = args_section_id, notification_count = getNotificationCount(user), error_message=error_message, success_message=success_message)


@app.route("/users/<user>/change_password", methods = ["GET", "POST"])
def user_change_pass(user):
    if request.method == "POST":
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']
        if new_password != confirm_new_password:
            return render_template('user_changepass.html', username = user, error_message = "Error: Passwords do not match.", notification_count = getNotificationCount(user))
        # #print(uname, password)
        details = users.query.filter_by(user_name = user).first()
        if details:
            details.password = new_password
        db.session.commit()
        notification = "User Password changed Successfully!"
        createNotification(user, datetime.datetime.now(), notification)
        return render_template('user_changepass.html', username = user, success_message = "Success: User password Changed Successfully.", notification_count = getNotificationCount(user))
    return render_template('user_changepass.html', username = user, notification_count = getNotificationCount(user))

def getNotificationCount(user):
    user_details = users.query.filter_by(user_name = user).first()
    notifications = userNotifications.query.filter_by(user_id = user_details.user_id)
    count = 0
    for noti in notifications:
        count += 1
    return count

def createNotification(user, date_of_notification, notification):
    user_details = users.query.filter_by(user_name = user).first()
    new_notification = userNotifications(user_id = user_details.user_id, date_of_notification = date_of_notification, notification = notification)
    db.session.add(new_notification)
    db.session.commit()

@app.route('/notifications/<user>')
def user_notifications(user):
    user_details = users.query.filter_by(user_name = user).first()
    notifications = userNotifications.query.filter_by(user_id = user_details.user_id)
    notification_count = getNotificationCount(user)

    return render_template('user_notifications.html', username = user, notification_count = notification_count, notifications = notifications)


@app.route('/notifications/<user>/<notification_id>/clear')
def user_notifications_clear(user, notification_id):
    user_details = users.query.filter_by(user_name = user).first()
    notification_to_clear = userNotifications.query.filter_by(notification_id = notification_id).first()
    db.session.delete(notification_to_clear)
    db.session.commit()

    return redirect("/notifications/" + user)

@app.route('/notifications/<user>/clearall')
def user_notifications_clearall(user):
    user_details = users.query.filter_by(user_name = user).first()
    notifications_to_clear = userNotifications.query.filter_by(user_id = user_details.user_id)
    for noti in notifications_to_clear:
        db.session.delete(noti)
    db.session.commit()

    return redirect("/notifications/" + user)

def getUsersCount():
    data = users.query.all()
    count = 0
    for user in data:
        count += 1
    return count

def getSectionsCount():
    data = sections.query.all()
    count = 0
    for section in data:
        count +=1
    return count


def getBooksCount():
    data = books.query.all()
    count = 0
    for book in data:
        count +=1
    return count

def getBookRequestsCount():
    data = bookRequest.query.all()
    count = 0
    for book in data:
        count +=1
    return count

def getBookIssueCount():
    data = bookIssue.query.all()
    count = 0
    for book in data:
        count +=1
    return count




def getTopRatedBooks(user):
    user_details = users.query.filter_by(user_name = user).first()
    rating_details = bookRating.query.order_by(desc(bookRating.avg_rating)).all()
    already_user_books = bookIssue.query.filter_by(user_id = user_details.user_id)
    all_book_details = books.query.all()
    already_requested_books = bookRequest.query.filter_by(user_id = user_details.user_id)
    all_book_details_dict = {}
    for book in all_book_details:
        all_book_details_dict[book.book_id] = book

    already_book_ids = []
    for book in already_user_books:
        already_book_ids.append(str(book.book_id))     
    
    requested_books = []
    for book in already_requested_books:
        requested_books.append(str(book.book_id))

    top_rated_books = []
    for book in rating_details:
        book_details = all_book_details_dict[book.book_id]
        section_name = sections.query.filter_by(section_id = book_details.section_id).first().section_name
        have_access = False
        have_requested = False
        have_purchased = False
        if str(book.book_id) in already_book_ids:
            have_access = True
        if str(book.book_id) in requested_books:
            have_requested = True
        found = bookPurchase.query.filter_by(book_id = book.book_id).filter_by(user_id = user_details.user_id).first()
        if found:
            have_purchased = True
        addEntry = {
                "book_name": book_details.book_name,
                "book_author": book_details.book_author,
                "book_id": book_details.book_id,
                "avg_rating": book.avg_rating,
                "count": book.count,
                "have_access": have_access,
                "have_requested": have_requested,
                "have_purchased": have_purchased,
                "section_name": section_name,
                "book_price": book_details.book_price
                }
        top_rated_books.append(addEntry)
        if len(top_rated_books) == 10:
            break
    return top_rated_books



def getRecentlyAddedBooks(user):
    user_details = users.query.filter_by(user_name = user).first()
    already_user_books = bookIssue.query.filter_by(user_id = user_details.user_id)
    all_book_details = books.query.order_by(desc(books.date_created)).all()
    already_requested_books = bookRequest.query.filter_by(user_id = user_details.user_id)

    already_book_ids = []
    for book in already_user_books:
        already_book_ids.append(str(book.book_id))    

    requested_books = []
    for book in already_requested_books:
        requested_books.append(str(book.book_id))
 
    recently_added_books = []
    for book in all_book_details:
        found = bookRating.query.filter_by(book_id = book.book_id).first()
        section_name = sections.query.filter_by(section_id = book.section_id).first().section_name
        if found:
            avg_rating= found.avg_rating
            count = found.count
        else:
            avg_rating= '--'
            count = '--'
        have_access = False
        have_requested = False
        have_purchased = False
        if str(book.book_id) in already_book_ids:
            have_access = True
        if str(book.book_id) in requested_books:
            have_requested = True
        found = bookPurchase.query.filter_by(book_id = book.book_id).filter_by(user_id = user_details.user_id).first()
        if found:
            have_purchased = True
        addEntry = {
                "book_name": book.book_name,
                "book_author": book.book_author,
                "book_id": book.book_id,
                "avg_rating": avg_rating,
                "count": count,
                "have_access": have_access,
                "have_requested": have_requested,
                "have_purchased": have_purchased,
                "section_name": section_name,
                "book_price": book.book_price
                }
        recently_added_books.append(addEntry)
    return recently_added_books



def updateBookRating(book_id):
    avg_rating, count = 0, 0
    sum = 0
    rating_details = userBookRating.query.filter_by(book_id = book_id)
    for book in rating_details:
        sum += book.rating
        count += 1
    avg_rating = sum/count
    avg_rating = int(avg_rating*100)
    avg_rating /= 100

    updateRating = bookRating.query.filter_by(book_id = book_id).first()
    if updateRating:
        updateRating.avg_rating = avg_rating
        updateRating.count = count
    else:
        new_rating = bookRating(book_id = book_id, avg_rating = avg_rating, count = count)
        db.session.add(new_rating)
    db.session.commit()


@app.route('/rating/<book_id>/<user>')
def user_book_rating(book_id, user):
    user_id = users.query.filter_by(user_name = user).first().user_id
    found = userBookRating.query.filter_by(user_id = user_id).filter_by(book_id = book_id).first()
    book_name = books.query.filter_by(book_id = book_id).first().book_name
    error_message, success_message = "", ""
    add_rate = True
    # Get the search parameters from the URL
    search_string = request.args.get('search_string', '')
    search_select = request.args.get('search_select', '')
    window = request.args.get('window')
    rating = request.args.get('mybooks_rating_select', '')
    if rating in ['', 'select']:
        add_rate = False
    if add_rate:
        if not found:
            new_rating = userBookRating(user_id = user_id, book_id = book_id, rating = int(rating))
            db.session.add(new_rating)
            success_message = f"Success: Rating Submmitted for Book: '{book_name}'!"
        else:
            found.rating = int(rating)
            success_message = f"Success: Rating updated for Book: '{book_name}'!"
        db.session.commit()
        updateBookRating(book_id)
    
    return redirect(f'/users/{user}/mybooks/{window}_books?search_string={search_string}&search_select={search_select}&error_message={error_message}&success_message={success_message}')
        
def generate_pdf(file_path, data):
    # Generate PDF
    c = canvas.Canvas(file_path, pagesize=letter)
    textobject = c.beginText(100, 700)
    textobject.setFont("Helvetica", 12)
    
    # Add data to the PDF
    for line in data:
        textobject.textLine(line)

    c.drawText(textobject)
    c.save()


@app.route('/download_pdf/<book_id>')
def download_pdf(book_id):

    book_details = books.query.filter_by(book_id = book_id).first()
    filepath = "books_download_pdf/" + book_details.book_name + ".pdf"
    
    try:
        return send_file(filepath, as_attachment=True)
    except:
        data = []
        data.append("Title: " + book_details.book_name)
        data.append("")
        data.append("Author: " + book_details.book_author)
        data.append("")
        data.append("Content: ")
        data.append(book_details.book_content)

        generate_pdf(filepath, data)
        
        return send_file(filepath, as_attachment=True)

def auto_revoke_books():
    with app.app_context():
        now = datetime.datetime.now()
        # Fetch and revoke books where date_of_return is less than or equal to now
        books_to_revoke = bookIssue.query.filter(bookIssue.return_date <= now).all()

        for book in books_to_revoke:
            user_details = users.query.filter_by(user_id = book.user_id).first()
            book_details = books.query.filter_by(book_id = book.book_id).first()
            notification = f"Book: {book_details.book_name} was auto revoked as it passed the return date!"
            createNotification(user_details.user_name, now, notification)
            db.session.delete(book)
        db.session.commit()



# Schedule the task to run every hour
@scheduler.task('interval', id='auto_revoke', minutes = 1)
def schedule_auto_revoke():
    auto_revoke_books()


@app.route('/logout')
def logout():
    return render_template('index.html')
    
def createDb():
    db.create_all()

if __name__ == "__main__":
    #createDb()
    app.run(debug=True)