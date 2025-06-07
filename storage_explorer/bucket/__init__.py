from flask import (
  Blueprint, g, render_template, url_for, redirect, request
)
from storage_explorer import get_logger
from storage_explorer.db import get_db
import sqlalchemy

from storage_explorer.auth import login_required
from storage_explorer.bucket.utils.operations import list_files, upload_file, allowed_file

from werkzeug.utils import secure_filename

from storage_explorer.utils import config

bucket_bp = Blueprint('bucket', __name__)

logger = get_logger()

@bucket_bp.route('/buckets', methods=['GET'])
@login_required
def list():
    """List all GCP buckets for the authenticated user."""
    error: list = []
    if g.user is None:
        return redirect(url_for('auth.login'))

    db = get_db()
    user_bucket_name = get_user_bucket_name(db)

    if not user_bucket_name:
        error.append("No GCP bucket found for the user.")
        return render_template('pages/bucket/index.html', bucket_name=None, files=[], errors=error)

    api_key = config.get_api_key()
    files = list_files(user_bucket_name, api_key=api_key)

    return render_template('pages/bucket/index.html', bucket_name=user_bucket_name, files=files, errors=error)

@bucket_bp.route('/buckets/upload', methods=['POST'])
@login_required
def upload():
    """Handle file upload to the user's GCP bucket."""
    errors = []
    if g.user is None:
        return redirect(url_for('auth.login'))
    
    if 'file' not in request.files:
      errors.append("No file part in the request.")
      return render_template('pages/bucket/index.html', errors=errors)
    
    file = request.files['file']
    if file.filename == '':
        errors.append("No selected file.")
        return render_template('pages/bucket/index.html', errors=errors)
    
    if not allowed_file(file.filename):
        errors.append("File type not allowed.")
        return render_template('pages/bucket/index.html', errors=errors)
    
    filename = secure_filename(file.filename)

    # Handle file upload logic here
    # This is a placeholder for the actual upload implementation
    # You would typically use a form to get the file and then upload it to the GCP bucket
    db = get_db()
    user_bucket_name = get_user_bucket_name(db)
    if not user_bucket_name:
        errors.append("No GCP bucket found for the user.")
        return render_template('pages/bucket/index.html', errors=errors)
    
    api_key = config.get_api_key()
    upload_file(user_bucket_name, filename=filename, file=file, api_key=api_key)

    return redirect(url_for('bucket.list'))

# Utils
def get_user_bucket_name(db: sqlalchemy.engine.base.Engine) -> str:
    """Get the GCP bucket name for the authenticated user."""
    # Fetch the user's GCP bucket information from the database
    with db.connect() as conn:
        query = sqlalchemy.text(
            "SELECT TOP 1 gcp_bucket_name FROM users WHERE username = :username",
        )
        result = conn.execute(query, parameters={"username": g.user['username']}).fetchone()
    
    user_bucket_name = result[0]
    return user_bucket_name