import logging, datetime, functools
from flask import (
  Blueprint, render_template, redirect, url_for, flash, request, session, g
)
import sqlalchemy
from storage_explorer.db import get_db

from werkzeug.security import check_password_hash, generate_password_hash

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Perform login logic here
        if not username or not password:
            flash('Username and password are required!', 'validation')
            return redirect(url_for('auth.login'))
        user = get_user(username, True)
        logger.info(user)
        if user == -1:
            flash('An error occurred while retrieving the user. Please try again or ask admin to investigate.', 'error')
            return redirect(url_for('auth.login'))
        if not user:
            flash('Invalid username or password!', 'validation')
            return redirect(url_for('auth.login'))
        if not check_password_hash(user['password'], password):
            flash('Invalid username or password!', 'validation')
            return redirect(url_for('auth.login'))
        # If login is successful, you can set session variables or tokens here
        session.clear()  # Clear any existing session data
        session['username'] = user['username']
        flash('Login successful!', 'success')
        return redirect(url_for('home.index'))
    return render_template('pages/auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        fullname = request.form.get('fullname')
        password = request.form.get('password')
        invite_token = request.form.get('invite_token')

        # validate and save user registration logic here
        if not username or not fullname or not password or not invite_token:
            flash('All fields are required!', 'validation')
            return redirect(url_for('auth.register'))
        
        # valid username with regex
        if not username.isalnum():
            flash('Username must be alphanumeric!', 'validation')
            return redirect(url_for('auth.register'))
        
        # valid full name, e.g. "John Doe"
        if not fullname.replace(" ", "").isalpha():
            flash('Full name must contain only letters and spaces!', 'validation')
            return redirect(url_for('auth.register'))
        
        # validate strength of password
        if len(password) < 8 or not any(char.isdigit() for char in password):
            flash('Password must be at least 8 characters long and contain at least one digit!', 'validation')
            return redirect(url_for('auth.register'))
        else:
            # hash the password before saving
            password = generate_password_hash(password)

        # check if user already exists
        existing_user = get_user(username)
        if existing_user and existing_user != -1:
            flash('Username already exists. Please choose a different username.', 'validation')
            return redirect(url_for('auth.register'))
        elif existing_user == -1:
            flash('An error occurred while checking the username. Please try again or ask admin to investigate.', 'error')
            return redirect(url_for('auth.register'))
        
        # check if invite token is valid
        invite_token_data = get_invite_token(invite_token)
        if invite_token_data == -1:
            flash('An error occurred while checking the invite token. Please try again or ask admin to investigate.', 'error')
            return redirect(url_for('auth.register'))
        if not invite_token_data:
            flash('Invalid invite token. Please check the token and try again.', 'validation')
            return redirect(url_for('auth.register'))
        
        # save user to database
        res = save_user(username, fullname, password, invite_token)
        if res == 0:
            return redirect(url_for('auth.login'))
        elif res == -1:
            return redirect(url_for('auth.register'))
    return render_template('pages/auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home.index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user.get('username') is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

@auth_bp.before_app_request
def load_logged_in_user():
    username = session.get('username')

    if username is None:
        g.user = None
    else:
        user = get_user(username)
        if user == -1:
            flash('An error occurred while retrieving the user. Please try again or ask admin to investigate.', 'error')
            g.user = None
        else:
            g.user = user

# Database operations
def save_user(username, fullname, password, invite_token):
    """Save a new user to the database."""
    # Assuming get_db() returns a database connection
    db = get_db()

    stmt = sqlalchemy.text(
        "INSERT INTO users (username, name, password, gcp_bucket_name, created_at) VALUES (:username, :name, :password, :gcp_bucket_name, :created_at)"
    )

    remove_token_smt = sqlalchemy.text(
        "DELETE FROM invite_tokens WHERE invite_token_id = :invite_token_id"
    )

    try:
        with db.connect() as conn:
            conn.execute(stmt, parameters={
                'username': username,
                'name': fullname,
                'password': password,  # In a real application, hash the password!
                'gcp_bucket_name': generate_bucket_name_from_user_info(username),  # Generate a unique bucket name
                'created_at': datetime.datetime.now(datetime.timezone.utc)
            })
            # Remove the invite token after successful registration
            conn.execute(remove_token_smt, parameters={
                'invite_token_id': invite_token
            })
            conn.commit()
        flash('User registered successfully!', 'success')
        return 0
    except Exception as e:
        logger.exception(e)
        flash('An error occurred while saving the user. Please try again or ask admin to investigate.', 'error')
        return -1

def get_user(username, with_pw = False) -> dict:
    """Retrieve a user from the database by username."""
    db = get_db()
    stmt = sqlalchemy.text(
        "SELECT TOP 1 user_id, username, name FROM users WHERE username = :username"
    )

    if with_pw:
        stmt = sqlalchemy.text(
            "SELECT TOP 1 user_id, username, name, password FROM users WHERE username = :username"
        )
    try:
        with db.connect() as conn:
            result = conn.execute(stmt, parameters={'username': username}).fetchone()
        if result:
            if with_pw:
                return {
                    'user_id': result[0],
                    'username': result[1],
                    'name': result[2],
                    'password': result[3]  # Include password if requested
                }
            return {
                'user_id': result[0],
                'username': result[1],
                'name': result[2]
            }
        return {}
    except Exception as e:
        logger.exception(e)
        flash('An error occurred while retrieving the user. Please try again or ask admin to investigate.', 'error')
    return -1

def get_invite_token(token_id: str) -> dict:
    """Retrieve an invite token from the database by token ID."""
    db = get_db()
    stmt = sqlalchemy.text(
        "SELECT TOP 1 invite_token_id, created_at FROM invite_tokens WHERE invite_token_id = :token_id"
    )
    try:
        with db.connect() as conn:
            result = conn.execute(stmt, parameters={'token_id': token_id}).fetchone()
        if result:
            return {
                'invite_token_id': result[0],
                'created_at': result[1]
            }
        return {}
    except Exception as e:
        logger.exception(e)
        flash('An error occurred while retrieving the invite token. Please try again or ask admin to investigate.', 'error')
    return -1

# Utils
def generate_bucket_name_from_user_info(username: str) -> str:
    """Generate a unique bucket name from the username."""
    return f"bucket-{username}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"