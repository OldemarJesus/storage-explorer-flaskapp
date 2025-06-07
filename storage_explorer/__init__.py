import os
import logging
from flask import Flask

def get_logger():
  # logging.basicConfig(level=logging.INFO)
  # Set up logging
  logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  )
  logger = logging.getLogger(__name__)
  return logger

def app(test_config=None):

  logger = get_logger()
  logger.info("Initializing Flask app...")

  # create and configure the app
  app = Flask(__name__, instance_relative_config=True)
  app.config.from_mapping(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
    DATABASE=os.environ.get("DATABASE", "storage-explorer.db")
  )

  if test_config is None:
    # Load the instance config, if it exists, when not testing
    app.config.from_pyfile('config.py', silent=True)
  else:
    app.config.from_mapping(test_config)

  # Ensure the instance folder exists
  try:
    os.makedirs(app.instance_path)
  except OSError:
    pass

  # Register blueprints
  from storage_explorer import db
  db.init_app(app)

  from storage_explorer.home import home_bp
  app.register_blueprint(home_bp)

  from storage_explorer.auth import auth_bp
  app.register_blueprint(auth_bp)

  from storage_explorer.bucket import bucket_bp
  app.register_blueprint(bucket_bp)
  
  return app