from flask import Flask, request, jsonify, render_template, url_for
from flask_jwt import JWT, jwt_required, current_identity
import hmac, datetime
import sqlite3
from flask import redirect
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from flask_cors import CORS, cross_origin


app = Flask(__name__)
app.debug = True
# CORS(app)


def create_tables():
    # CREATING A DATABASE
    conn = sqlite3.connect('dbHabituate.db')
    print("Opened database successfully")
    # CREATING TABLES
    conn.execute('CREATE TABLE IF NOT EXISTS tblCustomer (customer_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, surname TEXT, email TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS tblHistory (transaction_id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, isbn TEXT, book_Title TEXT, quantity TEXT,total_price REAL, order_date DATETIME, FOREIGN KEY (customer_id) REFERENCES tblCustomer (customer_id), FOREIGN KEY (isbn) REFERENCES tblBooks (isbn))')
    conn.execute('CREATE TABLE IF NOT EXISTS tblUser (user_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, surname TEXT, password TEXT, username TEXT)')
    conn.execute("CREATE TABLE IF NOT EXISTS tblBooks (isbn TEXT PRIMARY KEY, title TEXT, author TEXT, image TEXT, reviews TEXT, price REAL,genre TEXT)")
    print("Table created successfully")
    conn.close()


# create_tables()


# VALIDATION FOR STRINGS
def is_string(*args):
    for arg in args:
        if arg.isdigit() == False:
            flag = True
        else:
            flag = False
    return flag


# VALIDATION FOR INTEGERS
def is_number(*args):
    for arg in args:
        if arg.isdigit() == True:
            flag = True
        else:
            flag = False
    return flag


# VALIDATION FOR LENGTH OF MOBILE
def length(*args):
    for arg in args:
        if len(arg) > 0:
            flag = True
        else:
            flag = False
    return flag


# if length("hfvkh", "", "") == True and is_number("efv", "2455", "bvtt5") == True:
#     print('correct')
# else:
#     print('incorrect')


# FUNCTION TO GET AN EMAIL OF AN ADMIN THAT LAST LOGGED IN

def get_email(customer_id):
    with sqlite3.connect('dbHabituate.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT email FROM tblCustomer WHERE customer_id=?', customer_id)
        emails = cur.fetchone()
    return emails[0]


# REGISTRATION PAGE FOR NEW BOOKS
@app.route('/enter-new-books/')
def enter_new_books():
    return render_template('addNewBook.html')


# CREATING API OF BOOK DETAILS
@app.route('/booklist-api/', methods=['GET'])
def add_books_api():
     with sqlite3.connect('dbHabituate.db') as conn:
            cur = conn.cursor()
            # cur.execute('UPDATE tblBooks SET image= "https://images1.penguinrandomhouse.com/cover/9780140280197" WHERE author= "robert greene" ')
            # conn.commit()
            cur.execute('SELECT * FROM tblBooks')
            results = cur.fetchall()
            return jsonify(results)


# HOME PAGE OF THE BOOKSTORE WEBSITE
@app.route('/bookstore/')
def show_books():
    return render_template("bookstore.html")


# SIGN IN PAGE FOR A NEW ADMIN
@app.route('/sign-up/')
def sign_up():
    return render_template("sign_up.html")


# LOG IN PAGE FOR A NEW ADMIN
@app.route('/log-in/')
def log_in():
    return render_template("log_in.html")


# ========================================================================================================================================================================
# =================================================================== BACK END ===============================================================
# ========================================================================================================================================================================


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def fetch_users():
    with sqlite3.connect('dbHabituate.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tblUser")
        users = cursor.fetchall()
        new_data = []
        for data in users:
            new_data.append(User(data[0], data[4], data[3]))
    return new_data


users = fetch_users()
username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    id = payload['identity']
    return userid_table.get(id, None)


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'

jwt = JWT(app, authenticate, identity)


@app.route('/protected')
# @jwt_required()
def protected():
    return '%s' % current_identity


class clsUser:
    def __init__(self, name, surname, username, password):
        self.name = name
        self.surname = surname
        self.username = username
        self.password = password
        # self.email = email


    def user_registration(self):

            with sqlite3.connect("dbHabituate.db") as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO tblUser("
                               "name,"
                               "surname,"
                               "username,"
                               "password) VALUES(?, ?, ?, ?)", (self.name, self.surname, self.username, self.password))
                conn.commit()


@app.route('/user-registration/', methods=["POST"])
def user_register():
    response = {}
    if request.method == "POST":
        name = request.json['name']
        surname = request.json['surname']
        username = request.json['username']
        password = request.json['password']
        if is_string(name, surname) == True and length(name, surname, username, password) == True:

            objUser = clsUser(name, surname, username, password)
            objUser.user_registration()
            response["message"] = "success"
            response["status_code"] = 201
        else:
            response["message"] = "Unsuccessful. Incorrect credentials"
            response["status_code"] = 400
        return response


class clsCustomer:
    def __init__(self, name, surname, email):
        self.name = name
        self.surname = surname
        self.email = email


    def customer_registration(self):

        with sqlite3.connect("dbHabituate.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tblCustomer("
                           "name,"
                           "surname,"
                           "email) VALUES(?, ?, ?)", (self.name, self.surname, self.email))
            conn.commit()


# ADDING THE NEW customer ON THE TABLE
@app.route('/customer-registration/', methods=["POST"])
# @jwt_required()
def customer_registration():
    response = {}
    if request.method == "POST":
        name = request.json['name']
        surname = request.json['surname']
        email = request.json['email']
        if is_string(name, surname) == True or length(name, surname, email) == True:
            objCustomer = clsCustomer(name, surname, email)
            objCustomer.customer_registration()
            response["message"] = "customer successfully added"
            response["status_code"] = 201
        else:
            response['message'] = "Invalid characters"
            response['status_code'] = 400

        return response


class clsBooks:
    def __init__(self, isbn, title, author, image, reviews, price, genre):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.image = image
        self.reviews = reviews
        self.price = price
        self.genre = genre


    def add_new_books(self):
            with sqlite3.connect('dbHabituate.db') as conn:
                cur = conn.cursor()
                cur.execute('INSERT INTO tblBooks (isbn , title, author, image, reviews, price,genre) VALUES(?,?,?,?,?,?,?)', (self.isbn, self.title, self.author, self.image, self.reviews, self.price, self.genre))
                conn.commit()


# ADDING NEW BOOKS ON THE TABLE
@app.route('/add-new-books/', methods=["POST"])
# @jwt_required()
def add_new_books():
    response = {}

    if request.method == 'POST':
        title = request.json['title']
        reviews = request.json['reviews']
        author = request.json['author']
        image = request.json['image']
        strEncode = title[0:3] + title[-3:-1] + author[1:4]
        hex_string = strEncode.encode('utf-8')
        hex_value = hex_string.hex()
        isbn = hex_value
        price = request.json['price']
        genre = request.json['genre']
        if is_string(title, reviews, author, genre) == True or length(title, reviews, author, genre, image, price) == True or is_number(price):
            objBooks = clsBooks(isbn, title, author, image, reviews, price, genre)
            objBooks.add_new_books()
            response["status_code"] = 201
            response['description'] = "Book added succesfully"

        else:
            response["message"] = "Unsuccessful. Incorrect credentials"
            response["status_code"] = 400

        return response


# DISPLAYING ALL BOOKS
@app.route('/get-books/', methods=["GET"])
@cross_origin()
def get_books():
    response = {}
    with sqlite3.connect("dbHabituate.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tblBooks")
        posts = cursor.fetchall()
    response['status_code'] = 200
    response['data'] = posts
    return response


# DELETE A BOOK
@app.route("/delete-post/<id>/")
# @jwt_required()
def delete_book(id):
    response = {}
    with sqlite3.connect("dbHabituate.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tblBooks WHERE isbn=?", [id])
        conn.commit()
        response['status_code'] = 200
        response['message'] = "blog post deleted successfully."
    return response


# UPDATE A BOOK ROW
@app.route('/edit-book/<isbn>/', methods=["PUT"])
# @jwt_required()
def edit_book(isbn):
    response = {}

    if request.method == "PUT":
        with sqlite3.connect('dbHabituate.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}
            # ===================== UPDATING TITLE =================================
            if incoming_data.get("title") is not None:
                put_data["title"] = incoming_data.get("title")
                if is_number(put_data["title"]) == False:
                    with sqlite3.connect('dbHabituate.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE tblBooks SET title =? WHERE isbn=?", ([put_data["title"]], [isbn]))
                        cursor.execute("UPDATE tblHistory SET book_Title =? WHERE isbn=?", ([put_data["title"]], [isbn]))
                        conn.commit()
                        response['message'] = "Update was successfully"
                        response['status_code'] = 200
                else:
                    response['message'] = "Invalid characters"
                    response['status_code'] = 400
            # ===================== UPDATING AUTHOR =================================
            if incoming_data.get("author") is not None:
                put_data['author'] = incoming_data.get('author')
                if is_string(put_data["author"]) == True or length(put_data["author"]) == True:

                    with sqlite3.connect('dbHabituate.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE tblBooks SET author =? WHERE isbn=?", (put_data["author"], isbn))
                        conn.commit()

                        response["content"] = "author updated successfully"
                        response["status_code"] = 200
                else:
                    response['message'] = "Invalid characters"
                    response['status_code'] = 400
            # ===================== UPDATING IMAGE =================================
            if incoming_data.get("image") is not None:
                put_data["image"] = incoming_data.get("image")
                if length(put_data["image"]) == True:
                    with sqlite3.connect('dbHabituate.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE tblBooks SET image =? WHERE isbn=?", (put_data["image"], isbn))
                        conn.commit()
                        response['message'] = "Update was successfully"
                        response['status_code'] = 200
                else:
                    response['message'] = "Invalid characters"
                    response['status_code'] = 400
            # ===================== UPDATING REVIEWS =================================
            if incoming_data.get("reviews") is not None:
                put_data['reviews'] = incoming_data.get('reviews')
                if length(put_data["reviews"]) == True:

                    with sqlite3.connect('dbHabituate.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE tblBooks SET reviews =? WHERE isbn=?", (put_data["reviews"], isbn))
                        conn.commit()

                        response["content"] = "Content updated successfully"
                        response["status_code"] = 200
                else:
                    response['message'] = "Invalid characters"
                    response['status_code'] = 400
            # ===================== UPDATING PRICE =================================
            if incoming_data.get("price") is not None:
                put_data["price"] = incoming_data.get("price")
                if is_number(put_data["price"]) == True:
                    with sqlite3.connect('dbHabituate.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE tblBooks SET price =? WHERE isbn=?", (put_data["price"], isbn))
                        conn.commit()
                        response['message'] = "Update was successfully"
                        response['status_code'] = 200
                else:
                    response['message'] = "Invalid characters"
                    response['status_code'] = 400
            # ===================== UPDATING GENRE =================================
            if incoming_data.get("genre") is not None:
                put_data['genre'] = incoming_data.get('genre')
                if is_string(put_data['genre']) == True:

                    with sqlite3.connect('dbHabituate.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE tblBooks SET genre =? WHERE id=?", (put_data["genre"], isbn))
                        conn.commit()

                        response["content"] = "Content updated successfully"
                        response["status_code"] = 200
                else:
                    response['message'] = "Invalid characters"
                    response['status_code'] = 400
    return response


# DISPLAYING ALL USERS
@app.route('/get-user/<int:id>/', methods=["GET"])
# @jwt_required()
def get_user(id):
    response = {}

    with sqlite3.connect("dbHabituate.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tblUser WHERE user_id=" + str(id))

        response["status_code"] = 200
        response["description"] = "Blog post retrieved successfully"
        response["data"] = cursor.fetchone()

    return jsonify(response)


# DISPLAYING ALL USERS
@app.route('/filter-books/<genre>/')
def filter_books(genre):
    response = {}

    with sqlite3.connect("dbHabituate.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tblBooks WHERE genre=?", [genre])
        response["status_code"] = 200
        response["description"] = "Books filtered successfully"
        response["data"] = cursor.fetchall()

    return jsonify(response)


@app.route('/sort-books/<sort_by>/')
def sort_books(sort_by):
    response = {}

    with sqlite3.connect("dbHabituate.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tblBooks ORDER BY " + sort_by)
        response["status_code"] = 200
        response["description"] = "Books sorted successfully"
        response["data"] = cursor.fetchall()

    return jsonify(response)


# ========================================================= FOR HISTORY TABLE ==========================================================


# DISPLAYING ALL BOOKS
# @app.route('/get-books/', methods=["GET"])
# def get_books():
#     response = {}
#     with sqlite3.connect("dbHabituate.db") as conn:
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM tblBooks")
#         posts = cursor.fetchall()
#     response['status_code'] = 200
#     response['data'] = posts
#     return response


# DELETE A BOOK
@app.route("/delete-post/<id>/")
# @jwt_required()
def delete_books(id):
    response = {}
    with sqlite3.connect("dbHabituate.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tblBooks WHERE isbn=?", [id])
        conn.commit()
        response['status_code'] = 200
        response['message'] = "blog post deleted successfully."
    return response


@app.route("/delete-user/<id>/")
# @jwt_required()
def delete_user(id):
    response = {}
    with sqlite3.connect("dbHabituate.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tblUser WHERE user_id=?", [id])
        conn.commit()
        response['status_code'] = 200
        response['message'] = "blog post deleted successfully."
    return response

# with sqlite3.connect("dbHabituate.db") as conn:
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM tblBooks")
#     results = cursor.fetchall()
#     print(results)


# TOTAL PRICE OF A CUSTOMER
@app.route("/price-calculation/<int:customer_id>/")
def total_price(customer_id):
    with sqlite3.connect("dbHabituate.db") as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE tblHistory SET total_price=(quantity * (SELECT price FROM tblBooks WHERE tblBooks.isbn = tblHistory.isbn)) WHERE customer_id=3')
        cursor.execute("SELECT sum(total_price) AS total_price FROM tblHistory WHERE customer_id=?", str(customer_id))
        total = cursor.fetchone()
    return jsonify(total)


# OVERALL PRICE OF THE BOOKSTORE
@app.route("/bookstore_profit/")
def bookstore_income():
    with sqlite3.connect("dbHabituate.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sum(total_price) AS profit FROM tblHistory")
        results = cursor.fetchall()
    return jsonify(results)


# DISPLAYING ALL BOOKS
@app.route('/get-customers/', methods=["GET"])
# @jwt_required()
def get_customers():
    response = {}
    with sqlite3.connect("dbHabituate.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tblCustomer")
        customers = cursor.fetchall()
    response['status_code'] = 200
    response['data'] = customers
    return response


# DISPLAYING ALL transactions
@app.route('/get-all-transactions/', methods=["GET"])
# @jwt_required()
def get_transactions():
    response = {}
    with sqlite3.connect("dbHabituate.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tblHistory")
        transactions = cursor.fetchall()
    response['status_code'] = 200
    response['data'] = transactions
    return response


# IMAGE HOSTING
@app.route('/image-hosting/')
def image_hosting():
    with sqlite3.connect("dbHabituate.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT image FROM tblBooks WHERE isbn='34382077656f6265'")
        image = cursor.fetchone()
        for i in image:
            image1 = i
    return redirect(image1)


#  =================SENDING EMAIL TO THE ADMIN============
@app.route('/send-email/', methods=['POST'])
def send_email():
    response = {}
    if request.method == "POST":
        email = request.json['email']
        try:
            sender_email_id = 'lottowinners957@gmail.com'
            receiver_email_id = email
            password = "GETRICHWITHLOTTO"
            subject = "Profit for Habituate Reading Bookstore"
            msg = MIMEMultipart()
            msg['From'] = sender_email_id
            msg['To'] = receiver_email_id
            msg['Subject'] = subject
            with sqlite3.connect("dbHabituate.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT sum(total_price) AS profit FROM tblHistory")
                results = cursor.fetchone()
            body = f'Dear Admin\n \n This is the total profit we made today on {datetime.date.today()}:\n {results[0]}'
            msg.attach(MIMEText(body, 'plain'))
            text = msg.as_string()
            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.starttls()
            s.login(sender_email_id, password)
            s.sendmail(sender_email_id, receiver_email_id, text)
            s.quit()
            response['message'] = "Successfully sent an email"
        except:
            response['message'] = "Invalid email"
        return response


# with sqlite3.connect("dbHabituate.db") as conn:
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM tblHistory")
#         id = cursor.fetchone()
#         print(id)

#
# with sqlite3.connect('dbHabituate.db') as conn:
#             cur = conn.cursor()
#             cur.execute('UPDATE tblHistory SET total_price=(quantity * (SELECT total_price FROM tblBooks WHERE tblBooks.isbn = tblHistory.isbn)) WHERE customer_id=3')
#             conn.commit()
#             cur.execute('SELECT * FROM tblHistory')
#             book_details = cur.fetchall()
#             print(book_details)

if __name__ == "__main__":
    app.run()
    app.debug = True
