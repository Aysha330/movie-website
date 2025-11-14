from flask import Blueprint, request, jsonify, render_template, redirect, url_for
import mysql.connector

auth_bp = Blueprint('auth', __name__)
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse as urlparse

DATABASE_URL = "postgresql://ayisha:zz5ffyGUpRml2QhdMcAo2pQAGNlj8hxz@dpg-d4blgujipnbc73a65ug0-a.singapore-postgres.render.com/movienest_db"
url = urlparse.urlparse(DATABASE_URL)

mydb = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port or 5432
)
mycursor = mydb.cursor(cursor_factory=RealDictCursor)


# ✅ Show registration form
@auth_bp.route('/register', methods=['GET'])
def register_form():
    return render_template('register.html')

# ✅ Handle registration form submission
@auth_bp.route('/register', methods=['POST'])
def register_user():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    try:
        mycursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                         (username, email, password))
        mydb.commit()
        return redirect(url_for('auth.login_form'))
    except mysql.connector.IntegrityError:
        return "Username or email already exists!"

# ✅ Show login form
@auth_bp.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')
from flask import session
# ✅ Handle login submission
@auth_bp.route('/login', methods=['POST'])
def login_user():
    email = request.form['email']
    password = request.form['password']

    mycursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    user = mycursor.fetchone()

    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['email'] = user['email']
        return redirect(url_for('home'))
    else:
        # Instead of returning a new page, render login.html again with an error message
        return render_template('login.html', error="Invalid email or password!")
