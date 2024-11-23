# Database configuration constants
DB_TYPE = 'sqlite3'        # Options: 'sqlite3', 'mysql', 'postgres'
DB_PATH = 'data.sqlite'    # Default path for SQLite3
DB_HOST = 'localhost'      # Host for MySQL/Postgres
DB_USER = 'username'       # Username for MySQL/Postgres
DB_PASSWORD = 'password'   # Password for MySQL/Postgres
DB_NAME = 'database_name'  # Database name for MySQL/Postgres
DB_TABLE_MEME = 'meme'     # Default table name for meme data


def meme_sql_db(sql_query):
    """
    Executes the SQL query based on the database type configured in DB_TYPE.
    """
    if DB_TYPE == 'sqlite3':
        return meme_sqlite3(sql_query)
    elif DB_TYPE == 'mysql':
        return meme_mysql(sql_query)
    elif DB_TYPE == 'postgres':
        return meme_postgres(sql_query)
    else:
        raise Exception(f"Unsupported database type: {DB_TYPE}")


def meme_sqlite3(sql_query):
    """
    Executes a query on an SQLite3 database.
    """
    import sqlite3

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            results = [dict(row) for row in cursor.fetchall()]
            return results
    except sqlite3.Error as e:
        raise Exception(f"SQLite3 query failed: {e}")


def meme_mysql(sql_query):
    """
    Executes a query on a MySQL database.
    """
    import pymysql

    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(sql_query)
            results = cursor.fetchall()
            return results
    except pymysql.MySQLError as e:
        raise Exception(f"MySQL query failed: {e}")
    finally:
        connection.close()


def meme_postgres(sql_query):
    """
    Executes a query on a PostgreSQL database.
    """
    import psycopg2
    from psycopg2.extras import DictCursor

    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        with connection.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(sql_query)
            results = cursor.fetchall()
            return [dict(row) for row in results]
    except psycopg2.Error as e:
        raise Exception(f"PostgreSQL query failed: {e}")
    finally:
        connection.close()
