from flask import (
  Blueprint, render_template
)
import os

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    return render_template('pages/index.html')

@home_bp.route('/about')
def about():
    return render_template('pages/about.html')

@home_bp.route('/contact')
def contact():
    return render_template('pages/contact.html')