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

# Main function to process Memelang query and return results
def query(db_string):
	try:
		sql_query = sql(db_string)

		if DB_TYPE == 'sqlite3':
			return db_sqlite3(sql_query)
		elif DB_TYPE == 'mysql':
			return db_mysql(sql_query)
		elif DB_TYPE == 'postgres':
			return db_postgres(sql_query)
	except Exception as e:
		return f"Error: {e}"

# SQLite3 database query function
def db_sqlite3(sql_query):
	db = sqlite3.connect(DB_PATH)
	results = []
	cursor = db.cursor()
	cursor.execute(sql_query)

	for row in cursor.fetchall():
		if '\t' not in row[COL_RID]:
			results.append(row)
		else:
			aid = row[COL_AID]
			rids = row[COL_RID].split('\t')
			bids = row[COL_BID].split('\t')
			qnts = row[COL_QNT].split('\t')
			for j, rid in enumerate(rids):
				if aid == 'UNK':
					break
				if rid.startswith('?'):
					continue
				results.append((aid, rid, bids[j], qnts[j]))
				aid = bids[j]

	db.close()
	return results

# MySQL database query function
def db_mysql(sql_query):
	connection = mysql.connector.connect(
		host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
	)
	results = []
	cursor = connection.cursor()
	cursor.execute(sql_query)

	for row in cursor.fetchall():
		if '\t' not in row[COL_RID]:
			results.append(row)
		else:
			aid = row[COL_AID]
			rids = row[COL_RID].split('\t')
			bids = row[COL_BID].split('\t')
			qnts = row[COL_QNT].split('\t')
			for j, rid in enumerate(rids):
				if aid == 'UNK':
					break
				if rid.startswith('?'):
					continue
				results.append((aid, rid, bids[j], qnts[j]))
				aid = bids[j]

	connection.close()
	return results

# PostgreSQL database query function
def db_postgres(sql_query):
	connection = psycopg2.connect(
		host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
	)
	results = []
	cursor = connection.cursor()
	cursor.execute(sql_query)

	for row in cursor.fetchall():
		if '\t' not in row[COL_RID]:
			results.append(row)
		else:
			aid = row[COL_AID]
			rids = row[COL_RID].split('\t')
			bids = row[COL_BID].split('\t')
			qnts = row[COL_QNT].split('\t')
			for j, rid in enumerate(rids):
				if aid == 'UNK':
					break
				if rid.startswith('?'):
					continue
				results.append((aid, rid, bids[j], qnts[j]))
				aid = bids[j]

	connection.close()
	return results
