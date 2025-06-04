from flask import (
  Blueprint, render_template, redirect, url_for
)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    return render_template('pages/auth/login.html')

@auth_bp.route('/register')
def register():
    return render_template('pages/auth/register.html')

@auth_bp.route('/logout')
def logout():
    return redirect(url_for('home.index'))