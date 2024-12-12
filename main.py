import sys
from const import *
from parse import decode, encode
from sql import sql
from db import query

def main():

	if len(sys.argv)<2:
		sys.exit("\nNo query provided\n")

	try:
		meme_string = sys.argv[1]
		sql_string = sql(meme_string)
	except Exception as e:
		sys.exit(f"\n{e}\n")


	# Execute query
	rows = query(meme_string)

	# Formatting the output
	br = f"+{'-' * 21}+{'-' * 21}+{'-' * 21}+{'-' * 12}+"


	# Output data
	print(f"\nSQL: {sql_string}\n")
	print(br)
	print(f"| {'A':<19} | {'R':<19} | {'B':<19} | {'Q':>10} |")
	print(br)

	if not rows:
		print(f"| {'No matching memes':<76} |")
	else:
		for row in rows:
			print(f"| {row[0][:19]:<19} | {row[1][:19]:<19} | {row[2][:19]:<19} | {row[3]:>10} |")

	print(br+"\n")


if __name__ == "__main__":
	main()