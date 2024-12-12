# meme-sql-python
These Python scripts receive [Memelang](https://memelang.net/) queries, convert them to SQL, then execute them on an SQLite, MySQL, or Postgres database (according to your configuration). Licensed under [Memelicense.net](https://memelicense.net/). Contact info@memelang.net.

Try the demo at https://demo.memelang.net/


## Installation

Installation on Ubuntu for SQLite:

	# Install packages
	sudo apt install -y python3 pip sqlite3 git
	sudo pip install pysqlite3
	
	# Download files
	git clone https://github.com/memelang-net/meme-sql-python.git
	cd meme-sql-python
	
	# Create database
	cat ./data.sql | sqlite3 ./data.sqlite
	
	# Execute in CLI
	python3 ./meme.py "john_adams.child"


## Example usage

	# python3 ./meme.py "john_adams.child"

	SQL: SELECT * FROM meme m0  WHERE m0.aid='john_adams' AND m0.rid='child' AND m0.qnt!=0
	
	+---------------------+---------------------+---------------------+------------+
	| A                   | R                   | B                   |          Q |
	+---------------------+---------------------+---------------------+------------+
	| john_adams          | child               | abigail_adams_smit  |          1 |
	| john_adams          | child               | charles_adams       |          1 |
	| john_adams          | child               | john_quincy_adams   |          1 |
	| john_adams          | child               | thomas_boylston_ad  |          1 |
	+---------------------+---------------------+---------------------+------------+

## Testing

	# python3 ./test.py make
	# python3 ./test.py check

## Files
* *conf.py* configuration file for database settings
* *const.py* list of constants
* *data.sql* sample ARBQ data in SQL format
* *db.py* library to establish database connections
* *main.py* CLI interface to make queries
* *parse.py* library to parse Memelang commands into an array
* *sql.py* library to convert Memelang to SQL queries
* *test.py* library for testing