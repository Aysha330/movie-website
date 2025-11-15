from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import errors
import urllib.parse as urlparse

auth_bp = Blueprint('auth', __name__)

# PostgreSQL connection
DATABASE_URL = "postgresql://ayisha:zz5ffyGUpRml2QhdMcAo2pQAGNlj8hxz@dpg-d4blgujipnbc73a65ug0-a.singapore-postgres.render.com/movienest_db"
url = urlparse.urlparse(DATABASE_URL)

mydb = psycopg2.connect(
    database=url.path[1:],       # "movienest_db"
    user=url.username,           # "ayisha"
    password=url.password,       # your password
    host=url.hostname,           # host
    port=url.port or 5432
)
mycursor = mydb.cursor(cursor_factory=RealDictCursor)

# Show registration form
@auth_bp.route('/register', methods=['GET'])
def register_form():
    return render_template('register.html')

# Handle registration form submission
@auth_bp.route('/register', methods=['POST'])
def register_user():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    try:
        mycursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, password)
        )
        mydb.commit()
        return redirect(url_for('auth.login_form'))
    except errors.UniqueViolation:
        mydb.rollback()  # reset transaction
        return "Username or email already exists!"
    except Exception as e:
        mydb.rollback()
        return str(e)

# Show login form
@auth_bp.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')

# Handle login submission
@auth_bp.route('/login', methods=['POST'])
def login_user():
    email = request.form['email']
    password = request.form['password']

    try:
        mycursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = mycursor.fetchone()
    except Exception as e:
        mydb.rollback()
        return str(e)

    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['email'] = user['email']
        return redirect(url_for('home'))
    else:
        return render_template('login.html', error="Invalid email or password!")
