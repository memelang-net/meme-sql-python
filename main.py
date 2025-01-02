from conf import *
from cache import *
import sys
import os
import re
import db
import glob
import memelang
import memeterm

LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))


#### SEARCH ####

def sql(qry_sql):
	print(db.select(qry_sql, []))

# Search for memes from a memelang query string
def qry(mqry):

	try:
		marr = memelang.mqry2marr(mqry)
		qry_sql, qry_trms = memelang.marr2sql(marr)
	except Exception as e:
		print()
		sys.exit(e)
		print()

	# Execute query
	memeterm.tkey2tid(qry_trms)
	full_sql = memeterm.morfigy(qry_sql, qry_trms)
	memes = db.select(qry_sql, qry_trms)
	memeterm.meme2trm(memes)
	
	# Output data
	print(f"\nSQL: {full_sql}\n")
	memeprint(memes)

# Get an item
def get(aid):
	memes = memeterm.db2meme(aid)
	memeprint(memes)



#### ADD MEMES ####

# Add a single meme as set A R B [Q=1]
def put(meme):

	if len(meme) < 3: raise Exception("Too few arguements.")
	elif len(meme) > 4: raise Exception("Too many arguements.")
	elif len(meme) == 3: meme.append(1) # Empty Q defaults to 1

	memes=[meme]
	memeterm.meme2tid(rows, True)
	memeterm.meme2db(memes)
	memes.append(meme)
	memeprint(memes)


def putfile(file_path):
	tkeys = []
	terms = []
	memes = []
	with open(file_path, 'r', encoding='utf-8') as f:
		for ln, line in enumerate(f, start=1):

			if line.strip() == '' or line.strip().startswith('//'):
				continue

			line = re.sub(r'\s*//.*$', '', line, flags=re.MULTILINE)
			cols = re.split(r'\s+', line.strip())

			if cols[0] == 'TRM':
				if len(cols) < 3:
					raise Exception(f"Line {ln} missing columns")

				if re.match(r'[a-z]', cols[2]):
					cols[2]=TKEY2TID[cols[2]]
					if not cols[2]:
						raise Exception(f"Line {ln} invalid trd {col[2]}")


				# Self-referential term_key: TRM XYZ 98 XYZ
				if int(cols[2]) == TKEY2TID['key'] and cols[1]==cols[3]:
					tkeys.append(cols[1])

				else:
					terms.append([cols[1], int(cols[2]), ' '.join(cols[3:])])

			elif cols[0] == 'PUT':
				if len(cols) != 5:
					raise Exception(f"Line {ln} missing columns")
				cols[4]=float(cols[4])
				memes.append(cols[1:])

			else:
				raise Exception(f"Line {ln} unknown instruction")

	print()

	if tkeys:
		for trm in tkeys:
			tid = memeterm.trm2add(0, 0, trm)
			for term in terms:
				if term[0] == trm:
					term[0]=tid

	if terms:
		memeterm.trm2db(terms)
		termprint(terms)
		print()

	if memes:
		memeterm.meme2tid(memes, True)
		memeterm.meme2db(memes, True)
		memeterm.meme2trm(memes)
		memeprint(memes)
		print()


#### TERMS ####

# Add a term a TID TRD TRM
def tput (trt):
	if len(trt) != 3: raise Exception("Must pass 3 arguements.")

	trt[0]=int(trt[0])

	if trt[0] == 0:
		trt[0] = memeterm.tidmax()+1

	if re.match(r'[a-z]', trt[1]):
		trms=[trt[1]]
		memeterm.tkey2tid(trms)
		trt[1]=int(trms[0])
	else:
		trt[1]=int(trt[1])

	memeterm.trm2db([trt])
	print()
	termprint([trt])
	print()


# Add a term a TID TRD TRM
def tget (aid):

	aid = memeterm.trmget(aid)
	terms = memeterm.tid2term(aid)
	print()
	termprint(terms)
	print()



#### DB ADMIN ####

# Add database and user
def dbadd():
	commands = [
		f"sudo -u postgres psql -c \"CREATE DATABASE {DB_NAME};\"",
		f"sudo -u postgres psql -c \"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}'; GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} to {DB_USER};\"",
		f"sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} to {DB_USER};\""
	]

	for command in commands:
		print(command)
		os.system(command)


# Add database table
def tableadd():
	commands = [
		f"sudo -u postgres psql -d {DB_NAME} -c \"CREATE TABLE {DB_TABLE_MEME} (aid INTEGER, rid INTEGER, bid INTEGER, qnt DECIMAL(20,6)); CREATE UNIQUE INDEX {DB_TABLE_MEME}_arb_idx ON {DB_TABLE_MEME} (aid,rid,bid); CREATE INDEX {DB_TABLE_MEME}_rid_idx ON {DB_TABLE_MEME} (rid); CREATE INDEX {DB_TABLE_MEME}_bid_idx ON {DB_TABLE_MEME} (bid);\"",

		f"sudo -u postgres psql -d {DB_NAME} -c \"CREATE TABLE {DB_TABLE_TERM} (tid INTEGER, trd INTEGER, trm VARCHAR(511)); CREATE INDEX {DB_TABLE_TERM}_tid_idx ON {DB_TABLE_TERM} (tid); CREATE INDEX {DB_TABLE_TERM}_trd_idx ON {DB_TABLE_TERM} (trd); CREATE INDEX {DB_TABLE_TERM}_trm_idx ON {DB_TABLE_TERM} (trm);\"",
		f"sudo -u postgres psql -d {DB_NAME} -c \"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {DB_TABLE_MEME} TO {DB_USER};\"",
		f"sudo -u postgres psql -d {DB_NAME} -c \"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {DB_TABLE_TERM} TO {DB_USER};\""
	]

	for command in commands:
		print(command)
		os.system(command)


# Delete database table
def tabledel():
	commands = [
		f"sudo -u postgres psql -d {DB_NAME} -c \"DROP TABLE {DB_TABLE_MEME};\"",
		f"sudo -u postgres psql -d {DB_NAME} -c \"DROP TABLE {DB_TABLE_TERM};\""
	]

	for command in commands:
		print(command)
		os.system(command)



def memeprint(memes):
	# Formatting the output
	br = f"+{'-' * 21}+{'-' * 21}+{'-' * 21}+{'-' * 12}+"

	print(br)
	print(f"| {'A':<19} | {'R':<19} | {'B':<19} | {'Q':<10} |")
	print(br)

	if not memes:
		print(f"| {'No matching memes':<76} |")
		
	else:
		for meme in memes:
			qnt_str = str(meme[3]).rstrip('0').rstrip('.')
			print(f"| {meme[0][:19]:<19} | {meme[1][:19]:<19} | {meme[2][:19]:<19} | {qnt_str[:10]:>10} |")

	print(br+"\n")


def termprint(terms):
	br = f"+{'-' * 21}+{'-' * 11}+{'-' * 44}+"

	print()
	print(br)
	print(f"| {'TID':<19} | {'TRD':<9} | {'TRM':<42} |")
	print(br)

	for term in terms:
		print(f"| {term[0]:<19} | {term[1]:<9} | {term[2][:29]:<42} |")
	print(br)
	print()



if __name__ == "__main__":
	if sys.argv[1] == 'sql':
		sql(sys.argv[2])
	elif sys.argv[1] == 'query' or sys.argv[1] == 'qry' or sys.argv[1] == 'q':
		qry(sys.argv[2])
	elif sys.argv[1] == 'get' or sys.argv[1] == 'g':
		get(sys.argv[2])
	elif sys.argv[1] == 'set' or sys.argv[1] == 'put':
		put(sys.argv[2:])
	elif sys.argv[1] == 'tput':
		tput(sys.argv[2:])
	elif sys.argv[1] == 'tget':
		tget(sys.argv[2])
	elif sys.argv[1] == 'file':
		putfile(sys.argv[2])
	elif sys.argv[1] == 'dbadd' or sys.argv[1] == 'adddb':
		dbadd()
	elif sys.argv[1] == 'tableadd' or sys.argv[1] == 'addtable':
		tableadd()
	elif sys.argv[1] == 'tabledel' or sys.argv[1] == 'deltable':
		tabledel()
	elif sys.argv[1] == 'coreadd' or sys.argv[1] == 'addcore':
		putfile(LOCAL_DIR+'/core.meme')
	elif sys.argv[1] == 'fileall' or sys.argv[1] == 'allfile':
		files = glob.glob(LOCAL_DIR+'/*.meme')
		for file in files:
			putfile(file)
	elif sys.argv[1] == 'recore':
		tabledel()
		tableadd()
		putfile(LOCAL_DIR+'/core.meme')
	else:
		sys.exit("MAIN.PY ERROR: Invalid command");