import os
from conf import *
from const import *
from sql import sql

# Import the required database library based on DB_TYPE
if DB_TYPE == 'sqlite3':
	import sqlite3
elif DB_TYPE == 'mysql':
	import mysql.connector
elif DB_TYPE == 'postgres':
	import psycopg2
else:
	raise ValueError(f"Unsupported database type: {DB_TYPE}")


def query(meme_string):
	sql_query = sql(meme_string)

	if DB_TYPE == 'sqlite3':
		return db_sqlite3(sql_query)
	elif DB_TYPE == 'mysql':
		return db_mysql(sql_query)
	elif DB_TYPE == 'postgres':
		return db_postgres(sql_query)
	else:
		raise Exception(f"Unsupported database type: {DB_TYPE}")


def db_sqlite3(sql_query):
	with sqlite3.connect(DB_PATH) as conn:
		cursor = conn.cursor()
		cursor.execute(sql_query)
		return cursor.fetchall()


def db_mysql(sql_query):
	with mysql.connector.connect(
		host=DB_HOST,
		user=DB_USER,
		password=DB_PASSWORD,
		database=DB_NAME
	) as conn:
		cursor = conn.cursor()
		cursor.execute(sql_query)
		return cursor.fetchall()


def db_postgres(sql_query):
	conn_str = f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"
	with psycopg2.connect(conn_str) as conn:
		cursor = conn.cursor()
		cursor.execute(sql_query)
		return cursor.fetchall()
