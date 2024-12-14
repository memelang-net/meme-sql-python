# meme-sql-python
These Python scripts receive [Memelang](https://memelang.net/) queries, convert them to SQL, then execute them on an SQLite, MySQL, or Postgres database (according to your configuration). Licensed under [Memelicense.net](https://memelicense.net/). Contact info@memelang.net.

Try the demo at https://demo.memelang.net/


## Files
* *conf.py* configuration file for database settings
* *data.sql* sample ARBQ data in SQL format
* *main.py* CLI interface for queries and testing
* *memelang.py* library to parse Memelang commands into SQL


## Installation

Installation on Ubuntu:

	# Install packages
	sudo apt install -y python3 pip git
	
	# Download files
	git clone https://github.com/memelang-net/meme-sql-python.git memelang
	cd memelang

For ***SQLite***, install libraries and create a database table using the included *data.sql*:

	sudo apt install -y sqlite3
	
	cat ./data.sql | sqlite3 ./data.sqlite

For ***Postgres***, install libraries and create a database table using the included *data.sql*:

	sudo apt install -y libpq-dev python-dev
	sudo pip install psycopg2

	psql -U DB_USER -d DB_NAME -a -f ./data.sql


For ***MySQL***, install libraries and create database table using the included *data.sql*:

	sudo apt install -y python-mysqldb

	mysql -u DB_USER -p DB_NAME < ./data.sql


Or, you can manually create a database meme table with this SQL:

	DROP TABLE IF EXISTS meme;
	CREATE TABLE meme (aid varchar(255), rid varchar(255), bid varchar(255), qnt DECIMAL(20,6));
	CREATE UNIQUE INDEX arb ON meme (aid,rid,bid);
	CREATE INDEX rid ON meme (rid);
	CREATE INDEX bid ON meme (bid);
	INSERT INTO meme (aid, rid, bid, qnt) VALUES ('george_washington', 'spouse', 'martha_washington', 1);


## Example CLI Usage

Execute a query:

	# python3 ./main.py query "john_adams.child"

Outputs:

	SQL: SELECT * FROM meme m0  WHERE m0.aid='john_adams' AND m0.rid='child' AND m0.qnt!=0
	
	+---------------------+---------------------+---------------------+------------+
	| A                   | R                   | B                   |          Q |
	+---------------------+---------------------+---------------------+------------+
	| john_adams          | child               | abigail_adams_smit  |          1 |
	| john_adams          | child               | charles_adams       |          1 |
	| john_adams          | child               | john_quincy_adams   |          1 |
	| john_adams          | child               | thomas_boylston_ad  |          1 |
	+---------------------+---------------------+---------------------+------------+

Generate a *test_data.tsv* file:

	# python3 ./main.py testmake

To later check that current results match those of *test_data.tsv*:

	# python3 ./main.py testcheck


## Example Code Usage

For SQLite:

	import os
	import sqlite3
	import memelang
	
	memelang_query='john_adams.child'

	sql_query=memelang.str2sql(memelang_query)
	with sqlite3.connect('data.sqlite') as conn:
		cursor = conn.cursor()
		cursor.execute(sql_query)
		print(cursor.fetchall())

For Postgres:

	import psycopg2
	import memelang
	
	memelang_query='john_adams.child'
	
	sql_query=memelang.str2sql(memelang_query)
	conn_str = f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"
	with psycopg2.connect(conn_str) as conn:
		cursor = conn.cursor()
		cursor.execute(sql_query)
		print(cursor.fetchall())

For MySQL:

	import mysql
	import memelang
	
	memelang_query='john_adams.child'
	
	sql_query=memelang.str2sql(memelang_query)
	with mysql.connector.connect(
		host=DB_HOST,
		user=DB_USER,
		password=DB_PASSWORD,
		database=DB_NAME
	) as conn:
		cursor = conn.cursor()
		cursor.execute(sql_query)
		print(cursor.fetchall())

