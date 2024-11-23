# meme-sql-python

These Python scripts receive [Memelang](https://memelang.net/) queries, convert them to SQL, then execute them on an SQLite, MySQL, or Postgres database (according to your configuration). Licensed under [Memelicense.net](https://memelicense.net/). Contact info@memelang.net.

Try the demo at http://demo.memelang.net/

## Files
* *data.sql* sample ARBQ data in SQL format
* *data.sqlite* sample ARBQ data in an SQLite binary file
* *meme_parse.py* parses Memelang commands into an array
* *meme_sql_conf.py* configuration file to establish database connection
* *meme_sql_lib.py* library to convert Memelang to SQL and execute on database