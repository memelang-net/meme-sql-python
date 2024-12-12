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
	conn = sqlite3.connect(DB_PATH)
	cursor = conn.cursor()
	cursor.execute(sql_query)
	results = []

	rows = cursor.fetchall()

	if len(rows)>0 and len(rows[0])<4:
		raise Exception(f"DB ERROR: {rows[0][0]}")
		return

	for row in rows:
		rid_value = row[COL_RID]
		if "\t" not in rid_value:
			# Single entry
			# Convert to a tuple for deduplication
			results.append((row[COL_AID], row[COL_RID], row[COL_BID], row[COL_QNT]))
		else:
			# Multiple entries
			aid = row[COL_AID]
			rids = rid_value.split("\t")
			bids = row[COL_BID].split("\t")
			qnts = row[COL_QNT].split("\t")
			for j, rid in enumerate(rids):
				if aid == 'UNK':
					break
				if rid.startswith('?'):
					continue
				results.append((aid, rid, bids[j], qnts[j]))
				aid = bids[j]

	conn.close()

	# Deduplicate
	results = list(set(results))
	# Convert tuples back to dicts
	return [ {COL_AID: r[0], COL_RID: r[1], COL_BID: r[2], COL_QNT: r[3]} for r in results ]


def db_mysql(sql_query):
	conn = mysql.connector.connect(
		host=DB_HOST,
		user=DB_USER,
		password=DB_PASSWORD,
		database=DB_NAME
	)
	cursor = conn.cursor()
	cursor.execute(sql_query)
	results = []

	rows = cursor.fetchall()
	for row in rows:
		rid_value = row[COL_RID]
		if "\t" not in rid_value:
			results.append((row[COL_AID], row[COL_RID], row[COL_BID], row[COL_QNT]))
		else:
			aid = row[COL_AID]
			rids = rid_value.split("\t")
			bids = row[COL_BID].split("\t")
			qnts = row[COL_QNT].split("\t")
			for j, rid in enumerate(rids):
				if aid == 'UNK':
					break
				if rid.startswith('?'):
					continue
				results.append((aid, rid, bids[j], qnts[j]))
				aid = bids[j]

	conn.close()

	# Deduplicate and convert to dict
	results = list(set(results))
	return [ {COL_AID: r[0], COL_RID: r[1], COL_BID: r[2], COL_QNT: r[3]} for r in results ]


def db_postgres(sql_query):
	conn_str = f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"
	conn = psycopg2.connect(conn_str)
	cursor = conn.cursor()
	cursor.execute(sql_query)
	results = []

	rows = cursor.fetchall()
	for row in rows:
		rid_value = row[COL_RID]
		if "\t" not in rid_value:
			results.append((row[COL_AID], row[COL_RID], row[COL_BID], row[COL_QNT]))
		else:
			aid = row[COL_AID]
			rids = rid_value.split("\t")
			bids = row[COL_BID].split("\t")
			qnts = row[COL_QNT].split("\t")
			for j, rid in enumerate(rids):
				if aid == 'UNK':
					break
				if rid.startswith('?'):
					continue
				results.append((aid, rid, bids[j], qnts[j]))
				aid = bids[j]

	conn.close()

	# Deduplicate and convert to dict
	results = list(set(results))
	return [ {COL_AID: r[0], COL_RID: r[1], COL_BID: r[2], COL_QNT: r[3]} for r in results ]
