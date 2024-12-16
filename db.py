import os

# Database configuration constants
DB_TYPE = 'sqlite3'  # Options: 'sqlite3', 'mysql', 'postgres'
DB_PATH = 'data.sqlite'  # Default path for SQLite3
DB_HOST = 'localhost'  # Host for MySQL/Postgres
DB_USER = 'username'  # Username for MySQL/Postgres
DB_PASSWORD = 'password'  # Password for MySQL/Postgres
DB_NAME = 'database_name'  # Database name for MySQL/Postgres
DB_TABLE_MEME = 'meme'  # Default table name for meme data



# Import the required database library based on DB_TYPE
if DB_TYPE == 'sqlite3':
	import sqlite3
elif DB_TYPE == 'mysql':
	import mysql.connector
elif DB_TYPE == 'postgres':
	import psycopg2
else:
	raise ValueError(f"Unsupported database type: {DB_TYPE}")



def query(sql_query, sql_vals=[], table=DB_TABLE_MEME):

	if DB_TYPE == 'sqlite3':
		return query_sqlite3(sql_query, sql_vals)
	elif DB_TYPE == 'mysql':
		return query_mysql(sql_query, sql_vals)
	elif DB_TYPE == 'postgres':
		return query_postgres(sql_query, sql_vals)
	else:
		raise Exception(f"Unsupported database type: {DB_TYPE}")


def query_sqlite3(sql_query, sql_vals=[]):
	with sqlite3.connect(DB_PATH) as conn:
		cursor = conn.cursor()
		cursor.execute(sql_query, sql_vals)
		return cursor.fetchall()


def query_mysql(sql_query, sql_vals=[]):
	with mysql.connector.connect(
		host=DB_HOST,
		user=DB_USER,
		password=DB_PASSWORD,
		database=DB_NAME
	) as conn:
		cursor = conn.cursor()
		cursor.execute(sql_query, sql_vals)
		return cursor.fetchall()


def query_postgres(sql_query, sql_vals=[]):
	conn_str = f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"
	with psycopg2.connect(conn_str) as conn:
		cursor = conn.cursor()
		cursor.execute(sql_query, sql_vals)
		return cursor.fetchall()
