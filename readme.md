# memesql2

These Python scripts receive [Memelang](https://memelang.net/) queries, convert them to SQL, then execute them on a Postgres database. 
* Demo: https://demo.memelang.net/
* Contact: info@memelang.net
* License: Copyright HOLTWORK LLC. Patent pending.


## Files

* *cache.py* cache common terms in program memory
* *conf.py* database configurations
* *core.meme* core memelang terms and IDs
* *db.py* database configuration and library for CLI usage
* *main.py* CLI interface for queries and testing
* *memelang.py* library to parse Memelang commands into SQL
* *memeterm.py* library to convert string terms to integer IDs
* *presidents.meme* example terms and relations for the U.S. presidents


## Installation

Installation on Ubuntu:

	# Install packages
	sudo apt install -y git postgresql python3 python3-psycopg2
	systemctl start postgresql
	systemctl enable postgresql
	
	# Download files
	git clone https://github.com/memelang-net/memesql2.git memesql
	cd memesql

	# Configure the db.py file according for your Postgres settings
	# Create postgres DB and user from the CLI
	sudo python3 ./main.py dbadd

	# Create meme and term tables in the DB
	sudo python3 ./main.py tableadd

	# Load core terms
	python3 ./main.py file ./core.meme

	# Load example presidents data (optional)
	python3 ./main.py file ./presidents.meme


## Example CLI Usage

Execute a query:

	# python3 ./main.py get "john_adams.spouse"

Outputs:

	SQL: SELECT * FROM meme m0 WHERE m0.aid='john_adams' AND m0.rid='spouse' AND m0.qnt!=0
	
	+---------------------+---------------------+---------------------+------------+
	| A                   | R                   | B                   |          Q |
	+---------------------+---------------------+---------------------+------------+
	| john_adams          | spouse              | abigail_adams       |          1 |
	+---------------------+---------------------+---------------------+------------+


## Variable Naming Conventions

* `sql` is an SQL query string
* `mqry` is a Memelang string
* `mexp` is a meme expression comprising `[operator, operand]`
* `mstate` is a meme statement comprising a list of meme expressions (above)
* `mcmd` is list of meme statements (above)
* `marr` is list of meme commands (above)
* `meme` is a list in the form of `[A, R, B, Q]` typically a database row from the *meme* table
* `memes` is a list of `[A, R, B, Q]` 
* `trms` is a list of terms such as `['Alice', 'Bob']` typically strings but may also contain integers


## Library Functions

The library functions are in the *memelang.py* script.

* `memelang.mqry2sql()` receives a Memelang string like `john_adams.spouse` and returns an SQL query string.

* `memelang.mqry2marr()` receives a Memelang string and returns a parsed array called `marr`.

* `memelang.marr2mqry()` receives `marr` and returns a Memelang string.

* `memelang.marr2sql()` receives `marr` and returns an SQL query string.

* `memelang.meme2mqry()` receives database results in the form of an array of `[A, R, B, Q]` tuples and returns a Memelang string.
