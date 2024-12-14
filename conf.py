import os

# Database configuration constants
DB_TYPE = 'sqlite3'  # Options: 'sqlite3', 'mysql', 'postgres'
DB_PATH = 'data.sqlite'  # Default path for SQLite3
DB_HOST = 'localhost'  # Host for MySQL/Postgres
DB_USER = 'username'  # Username for MySQL/Postgres
DB_PASSWORD = 'password'  # Password for MySQL/Postgres
DB_NAME = 'database_name'  # Database name for MySQL/Postgres
DB_TABLE_MEME = 'meme'  # Default table name for meme data
DB_TEST_DIR = os.path.dirname(os.path.abspath(__file__))