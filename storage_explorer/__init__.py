import os
from flask import Flask

def app(test_config=None):
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
  from storage_explorer.home import home_bp
  app.register_blueprint(home_bp)

  from storage_explorer.auth import auth_bp
  app.register_blueprint(auth_bp)
  
  return app