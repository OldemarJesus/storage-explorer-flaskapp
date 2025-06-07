from __future__ import annotations
import os, uuid, click, logging, datetime

from flask import (
    Blueprint
)

import sqlalchemy
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import MetaData
from sqlalchemy.sql import func

from sqlalchemy import Table

from storage_explorer.utils.db_connector import connect_with_connector, connect_tcp_socket

# create a Flask blueprint for database operations
db_bp = Blueprint('db', __name__)

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_connection_pool() -> sqlalchemy.engine.base.Engine:
    # use a TCP socket when INSTANCE_HOST (e.g. 127.0.0.1) is defined
    if os.environ.get("INSTANCE_HOST"):
        return connect_tcp_socket()

    # use the connector when INSTANCE_CONNECTION_NAME (e.g. project:region:instance) is defined
    if os.environ.get("INSTANCE_CONNECTION_NAME"):
        return connect_with_connector()

    raise ValueError(
        "Missing database connection type. Please define one of INSTANCE_HOST or INSTANCE_CONNECTION_NAME"
    )

# create 'users' table in database if it does not already exist
def migrate_db(db: sqlalchemy.engine.base.Engine) -> None:
    inspector = sqlalchemy.inspect(db)
    if not inspector.has_table("users"):
        metadata = MetaData()
        Table(
            "users",
            metadata,
            Column("user_id", Integer, primary_key=True, nullable=False),
            Column("username", String(100), nullable=False),
            Column("name", String(100), nullable=False),
            Column("password", String(255), nullable=False),
            Column("gcp_bucket_name", String(255), nullable=False),
            Column("created_at", DateTime, default=func.now(), nullable=False)
        )
        metadata.create_all(db)
    if not inspector.has_table("invite_tokens"):
        metadata = MetaData()
        Table(
            "invite_tokens",
            metadata,
            Column("invite_token_id", String(255), primary_key=True, nullable=False),
            Column("created_at", DateTime, default=func.now(), nullable=False)
        )
        metadata.create_all(db)

# This global variable is declared with a value of `None`, instead of calling
# `init_db()` immediately, to simplify testing. In general, it
# is safe to initialize your database connection pool when your script starts
# -- there is no need to wait for the first request.
db = None

# init_db lazily instantiates a database connection pool. Users of Cloud Run or
# App Engine may wish to skip this lazy instantiation and connect as soon
# as the function is loaded. This is primarily to help testing.
def init_db() -> None:
    """Initialize the database connection pool if it is not already initialized."""
    logger.info("Initializing database connection pool...")
    global db
    if db is None:
        db = init_connection_pool()
        migrate_db(db)

def get_db() -> sqlalchemy.engine.base.Engine:
    """Get the database connection pool."""
    if db is None:
        init_db()
    return db

@click.command('generate-token')
@click.argument('quantity', type=int, default=1)
def generate_token_command(quantity: int):
    """Generate a new invite token."""
    init_db()
    db = get_db()

    with db.connect() as connection:
        for _ in range(quantity):
            invite_token = uuid.uuid4().hex
            connection.execute(
                sqlalchemy.text("INSERT INTO invite_tokens (invite_token_id, created_at) VALUES (:invite_token, :created_at)"),
                {"invite_token": invite_token, "created_at": datetime.datetime.now(datetime.timezone.utc)}
            )
            connection.commit()
            click.echo(f"Generated invite token: {invite_token}")
    

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(generate_token_command)

    @app.before_request
    def run_init_db():
        """Initialize the database connection pool."""
        init_db()
        logger.info("Database connection pool initialized.")