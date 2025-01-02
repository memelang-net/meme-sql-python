import psycopg2
from conf import *

def select(sql_query, sql_vals=[]):
	conn_str = f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"
	with psycopg2.connect(conn_str) as conn:
		cursor = conn.cursor()
		cursor.execute(sql_query, sql_vals)
		rows=cursor.fetchall()
		return [list(row) for row in rows]


def insert(sql_query, sql_vals=[]):
	conn_str = f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"
	with psycopg2.connect(conn_str) as conn:
		cursor = conn.cursor()
		cursor.execute(sql_query, sql_vals)

def selnum(sql_query):
	result = select(sql_query)
	return int(result[0][0] if result and result[0] else 0)
