import sass
import sqlite3
import random, string
from flask import Flask, render_template, request, session, redirect
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import generate_password_hash, check_password_hash
# upujp

from helpers import login_required

# Configure application
app = Flask(__name__, template_folder='templates')

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
db = sqlite3.connect('database.sqlite')


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

sass.compile(dirname=('static/sass', 'static/css'), output_style='compressed', source_map_embed=True)
with open('static/css/styles.css') as example_css:
    print('sass compiled')


def random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not request.form.get("email"):
            message = 'Вы не ввели электронную почту!'
            return render_template("register.html", message=message)

        with sqlite3.connect("database.sqlite") as con:
            email = request.form.get("email").lower()

            cur = con.cursor()
            cur.execute("SELECT email FROM accounts WHERE email = :email", {
                'email': email
            })

            if cur.fetchone() is not None:
                message = 'Пользователь с такой электронной почтой уже существует! Вы можете войти, используя ' \
                          'свой пароль.'
                return render_template("login.html", message=message)
            else:
                password = random_string(5)
                password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

                print(password)
                cur.execute("INSERT INTO accounts (email, password_hash) VALUES (:email, :password_hash)", {
                    'email': email,
                    'password_hash': password_hash
                })

            con.commit()

        return render_template("register.html")
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        if not request.form.get("email"):
            message = 'Вы не ввели электронную почту!'
            return render_template("login.html", message=message)
        if not request.form.get("password"):
            message = 'Вы не ввели пароль!'
            return render_template("login.html", message=message)

        with sqlite3.connect("database.sqlite") as con:
            email = request.form.get("email").lower()
            password = request.form.get("password")
            password_hash = ''

            cur = con.cursor()
            cur.execute("SELECT * FROM accounts WHERE email = :email", {
                'email': email
            })
            rows = cur.fetchone()

            if rows is not None:
                password_hash = rows[2]

            con.commit()

            if rows is None or not check_password_hash(password_hash, password):
                message = 'Неверный адрес электронной почты или пароль!'
                return render_template("login.html", message=message)
            else:
                session["user_id"] = rows[0]
                return redirect("/personal")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/personal")
@login_required
def personal():
    if not session.get("user_id"):
        return render_template("login.html")

    user_id = session["user_id"]
    with sqlite3.connect("database.sqlite") as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM accounts WHERE id = :user_id", {
            'user_id': user_id
        })
        rows = cur.fetchone()
        account = {'email': rows[1]}

        con.commit()

    return render_template("personal.html", account=account)
