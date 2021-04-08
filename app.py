import random
import sqlite3
import string
from tempfile import mkdtemp

import sass
from flask import Flask, render_template, request, session, redirect
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash

from helpers import login_required
# upujp


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

# sass compile section
sass.compile(dirname=('static/sass', 'static/css'), output_style='compressed', source_map_embed=True)
with open('static/css/styles.css') as example_css:
    print('sass compiled')


def random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


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

        email = request.form.get("email").lower()

        with sqlite3.connect("database.sqlite") as con:
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

        email = request.form.get("email").lower()

        with sqlite3.connect("database.sqlite") as con:
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
    crew_variants = [
        'до 5 сотрудников',
        '5-10 сотрудников',
        '10-50 сотрудников',
        '50-100 сотрудников',
        '100-500 сотрудников',
        '500-3000 сотрудников',
        'более 3000 сотрудников'
    ]
    type_variants = [
        'Машиностроение',
        'Строительство',
        'Горно-рудная промышленность',
        'Нефть и газ',
    ]

    if not session.get("user_id"):
        return render_template("login.html")

    user_id = session["user_id"]
    with sqlite3.connect("database.sqlite") as con:
        cur = con.cursor()
        cur.execute("""
            SELECT * FROM accounts 
            JOIN organizations ON organizations.account_id = accounts.id 
            WHERE accounts.id = :account_id
            """, {'account_id': user_id})
        rows = cur.fetchone()

        if rows is None:
            return render_template("personal.html")
        else:
            account = {
                'email': rows[1],
                'inn': rows[4],
                'kpp': rows[5],
                'ogrn': rows[6],
                'title': rows[7],
                'full_title': rows[8],
                'address_legal': rows[9],
                'address_mail': rows[10],
                'crew': rows[11],
                'description': rows[12],
                'phone_public': rows[14],
                'website_url': rows[15],
                'address_public': rows[16],
                'email_public': rows[17],
            }

        con.commit()

    if not account:
        return render_template("personal.html")
    else:
        return render_template("personal.html",
                               account=account, crew_variants=crew_variants, type_variants=type_variants)


@app.route("/personal/organization_add", methods=["POST"])
@login_required
def organization_add():
    user_id = session["user_id"]

    if request.method == "POST":
        with sqlite3.connect("database.sqlite") as con:
            inn = int(request.form.get("inn"))

            cur = con.cursor()
            cur.execute("SELECT inn FROM organizations WHERE inn = :inn", {
                'inn': inn
            })

            if cur.fetchone() is not None:
                message = 'Такая организация уже существует'
                return render_template("personal.html", message=message)
            else:
                cur.execute("INSERT INTO organizations (inn, account_id) VALUES (:inn, :account_id)", {
                    'inn': inn,
                    'account_id': user_id
                })

            con.commit()

        return redirect("/personal")
    else:
        return render_template("personal.html")


@app.route("/personal/organization_legal_update", methods=["POST"])
@login_required
def organization_legal_update():
    user_id = session["user_id"]

    if request.method == "POST":
        with sqlite3.connect("database.sqlite") as con:
            inn = request.form.get("inn")
            kpp = request.form.get("kpp")
            ogrn = request.form.get("ogrn")
            title = request.form.get("title")
            full_title = request.form.get("full_title")
            address_legal = request.form.get("address_legal")
            address_mail = request.form.get("address_mail")

            cur = con.cursor()
            print(inn)
            print(kpp)
            print(ogrn)
            print(title)
            print(full_title)
            print(address_legal)
            print(address_mail)

            cur.execute("""
                UPDATE organizations 
                SET kpp = :kpp, ogrn = :ogrn, title = :title, full_title = :full_title, 
                    address_legal = :address_legal, address_mail = :address_mail
                WHERE account_id = :user_id AND inn = :inn;
                """, {
                'user_id': user_id,
                'inn': inn,
                'kpp': kpp,
                'ogrn': ogrn,
                'title': title,
                'full_title': full_title,
                'address_legal': address_legal,
                'address_mail': address_mail
            })

            con.commit()

        return redirect("/personal")
    else:
        print("GET organization_update")
        return render_template("personal.html")


@app.route("/personal/organization_about_update", methods=["POST"])
@login_required
def organization_about_update():
    user_id = session["user_id"]

    if request.method == "POST":
        with sqlite3.connect("database.sqlite") as con:
            inn = request.form.get("inn")
            crew = request.form.get("crew")
            description = request.form.get("description")

            cur = con.cursor()
            print(inn)
            print(crew)
            print(description)

            cur.execute("""
                UPDATE organizations 
                SET crew = :crew, description = :description
                WHERE account_id = :user_id AND inn = :inn;
                """, {
                'user_id': user_id,
                'inn': inn,
                'crew': crew,
                'description': description
            })

            con.commit()

        return redirect("/personal")
    else:
        print("GET organization_update")
        return render_template("personal.html")


@app.route("/personal/organization_contacts_update", methods=["POST"])
@login_required
def organization_contacts_update():
    user_id = session["user_id"]

    if request.method == "POST":
        with sqlite3.connect("database.sqlite") as con:
            inn = request.form.get("inn")
            phone_public = request.form.get("phone_public")
            website_url = request.form.get("website_url")
            email_public = request.form.get("email_public")
            address_public = request.form.get("address_public")

            cur = con.cursor()
            print(inn)
            print(phone_public)
            print(website_url)
            print(email_public)
            print(address_public)

            cur.execute("""
                UPDATE organizations 
                SET phone_public = :phone_public, website_url = :website_url, 
                    email_public = :email_public, address_public = :address_public
                WHERE account_id = :user_id AND inn = :inn;
                """, {
                'user_id': user_id,
                'inn': inn,
                'phone_public': phone_public,
                'website_url': website_url,
                'email_public': email_public,
                'address_public': address_public,
            })

            con.commit()

        return redirect("/personal")
    else:
        print("GET organization_update")
        return render_template("personal.html")


@app.route("/personal/password_change", methods=["POST"])
@login_required
def password_change():
    user_id = session["user_id"]

    if request.method == "POST":
        password_current = request.form.get("password_current")
        password_new = request.form.get("password_new")

        with sqlite3.connect("database.sqlite") as con:
            cur = con.cursor()
            cur.execute("""
                SELECT * FROM accounts 
                WHERE id = :user_id
                """, {'user_id': user_id})

            rows = cur.fetchone()
            password = rows[2]

            if rows is None or not check_password_hash(password, password_current):
                print('Error')
            else:
                password_hash_new = generate_password_hash(password_new, method='pbkdf2:sha256', salt_length=8)
                cur.execute("""
                UPDATE accounts SET password_hash = :password_hash WHERE id = :user_id;
                """, {
                    'password_hash': password_hash_new,
                    'user_id': user_id
                })
                print('Success')

            con.commit()

        return redirect("/personal")
    else:
        return render_template("personal.html")
