import random
import re
import db
from conf import *
from cache import *
import memelang

TKEY_REGEX = r'^[a-z0-9_]+$'


#### TERM DB ####

def trm2add (tid, trd, trm, table=DB_TABLE_TERM):

	if not tid:
		tid = tidmax()+1

	if not trd:
		trd=TKEY2TID['key']

	if trd == TKEY2TID['key']:
		if not re.match(TKEY_REGEX, trm):
			raise ValueError(f'Invalid term_key format for {trm}')

		elif trmget(trm):
			raise ValueError(f'Duplicate term_key for {trm}')

		TKEY2TID[trm] = tid
		TID2TKEY[tid] = trm

	db.insert(f"INSERT INTO {table} (tid, trd, trm) VALUES (%s, %s, %s)", [tid, trd, trm])

	return tid


def trm2ulw(trm):
	return re.sub(r'__+', '_', re.sub(r'[^a-z0-9]', '_', trm.lower()))


def trm2del (tid, trd, trm, table=DB_TABLE_TERM):
	db.insert(f"DELETE FROM {table} WHERE tid=%s AND trd=%s AND trm=%s", [tid, trd, trm])


def trm2wip (tid, trd, table=DB_TABLE_TERM):
	if not tid:
		raise ValueError('tid')
	elif trd:
		db.insert(f"DELETE FROM {table} WHERE tid=%s AND trd=%s", [tid, trd])
	else:
		db.insert(f"DELETE FROM {table} WHERE tid=%s", [tid])


def trmget(trm, trd=TKEY2TID['key'], table=DB_TABLE_TERM):

	if isinstance(trm, int):
		return trm

	if isinstance(trm, str) and re.match(r'^[0-9]+$', trm):
		return int(trm)

	terms=db.select(
		f"SELECT tid FROM {table} WHERE trd=%s AND trm=%s",
		[trd, trm]
	);
	return None if not terms else int(terms[0][0])


def tid2term(tid, trd=0, table=DB_TABLE_TERM):

	if trd:
		return db.select(
			f"SELECT tid, trd, trm FROM {table} WHERE tid=%s AND trd=%s",
			[tid, trd]
		);
	else:
		return db.select(
			f"SELECT tid, trd, trm FROM {table} WHERE tid=%s",
			[tid]
		);



# Write terms from an array of [[int TID, int RID, str TERM]]
def trm2db (terms, table=DB_TABLE_TERM):
	if not terms: return

	sql_inserts = []
	trm_inserts = []
	for tid, trd, trm in terms:

		tid=int(tid)

		if tid>TKEY2TID['cor']:
			if not re.search(r'[A-Za-z]', trm):
				raise ValueError(f"Term must contain an a-z letter {trm}")

			if trd == TKEY2TID['key'] and not re.match(TKEY_REGEX, trm):
				raise ValueError(f"Intrmid term key for {trm}")

		sql_inserts.append(f"({tid}, {trd}, %s)")
		trm_inserts.append(trm)

	# Join all insert trmues into one query
	db.insert(f"INSERT INTO {table} (tid, trd, trm) VALUES " + ','.join(sql_inserts) + " ON CONFLICT DO NOTHING;", trm_inserts)


def tidmax(table=DB_TABLE_TERM):
	tid = db.selnum(f"SELECT MAX(tid) FROM {table}")
	return tid if tid>0 else TKEY2TID['cor']


# Get TIDs for a list of terms
# Optionally assign new TIDs to new terms in the DB
def tkey2tid(trms, termput=False, table=DB_TABLE_TERM):
	global TKEY2TID, TID2TKEY

	# If trms is empty, return early
	if not trms: return

	# Determine which strings are not yet in the global dictionary
	missing_trms = [trm for trm in trms if trm not in TKEY2TID and isinstance(trm, str) and not trm.isdigit()]

	# Query missing strings from the database
	tid = 0
	put_terms = []
	if missing_trms:

		if termput:
			tid = tidmax()

		term_rows=db.select(
			f"SELECT tid, trm FROM {table} WHERE trd={TKEY2TID['key']} AND trm IN (" + ','.join(['%s'] * len(missing_trms)) + ")",
			missing_trms
		);

		for row in term_rows:
			TKEY2TID[row[1]] = int(row[0])
			TID2TKEY[int(row[0])] = row[1]

	# Now all strings should be in TKEY2TID
	for i, trm in enumerate(trms):
		if not isinstance(trm, str) or trm.isdigit(): 
			continue
		elif TKEY2TID.get(trm) is None:
			if termput:
				tid += 1
				put_terms.append([tid, TKEY2TID['key'], trm])
				trms[i]=trm
				TKEY2TID[trm] = tid
				TID2TKEY[tid] = trm
			else:
				raise KeyError(f"Error: Term not found for {trm}")
		else:
			trms[i]=TKEY2TID.get(trm)

	if put_terms:
		trm2db(put_terms, table)


# Get terms for a list of TIDs from the DB
def tid2tkey(tids, table=DB_TABLE_TERM):
	global TKEY2TID, TID2TKEY

	# If tids is empty, return early
	if not tids:
		return

	# Determine which tids are not yet in the global dictionary
	missing_tids = [abs(x) for x in tids if x not in TID2TKEY]


	# Query missing tids from the database
	if missing_tids:
		tid_rows=db.select(
			f"SELECT tid, trm FROM {table} WHERE trd={TKEY2TID['key']} AND tid IN (" + ','.join(['%s'] * len(missing_tids)) + ")",
			missing_tids
		);

		for row in tid_rows:
			TKEY2TID[row[1]] = int(row[0])
			TID2TKEY[int(row[0])] = row[1]


#### MEME DB ####

def db2meme (mqry, table=DB_TABLE_MEME):
	qry_sql, qry_trms = memelang.mqry2sql(mqry, table)
	tkey2tid(qry_trms)

	# Execute query
	memes = db.select(qry_sql, qry_trms)
	meme2trm(memes)
	return memes

def db2arbq (mqry, table=DB_TABLE_MEME):
	memes = db2meme(mqry, table)
	arbqs = {}

	for meme in memes:
		arbqs.setdefault(meme[0], {}).setdefault(meme[1], {})[meme[2]] = meme[3]

	return arbqs


# Write meme from an array of [[int A, int R, int B, float Q]]
def meme2db (rows, ignore=False, table=DB_TABLE_MEME):
	if not rows:
		return

	sql_inserts = []
	for aid, rid, bid, qnt in rows:

		if not isinstance(aid, int) or not isinstance(rid, int) or not isinstance(bid, int):
			raise TypeError("Error: meme2db vars are not ints")

		qnt = float(qnt)
		sql_inserts.append(f"({aid}, {rid}, {bid}, {qnt})")

	# Join all insert trmues into one query
	db.insert(f"INSERT INTO {table} (aid, rid, bid, qnt) VALUES " + ','.join(sql_inserts) + (" ON CONFLICT DO NOTHING;" if ignore else ''))


#### ARBQ ROW ####

# Replace the string terms with interger TIDs in a list like [[A, R, B, Q]]
def meme2tid(rows, termput=False, table=DB_TABLE_TERM):
	global TKEY2TID

	if not rows: return

	# Extract all strings from rows
	trms = [x for row in rows for x in row[:3]]

	# If trms is empty, return early
	if not trms:
		return

	tkey2tid(trms, termput, table);

	# Now all strings should be in TKEY2TID
	for row in rows:
		for i, trm in enumerate(row):
			if i>3: 
				raise KeyError(f"Col count too high")
			elif i == 3: 
				row[i] = float(trm)
				continue
			elif isinstance(trm, int):
				continue

			tid = TKEY2TID.get(trm)

			if tid is None: raise KeyError(f"Error: Term not found for {trm}")
			else: row[i] = tid


# Replace the interger TIDs with string terms in a list like [[A, R, B, Q]]
def meme2trm(rows, table=DB_TABLE_TERM):
	global TID2TKEY

	if not rows: return

	# Extract all tids from rows
	tids = [int(x) for row in rows for x in row[:3]]

	# If tids is empty, return early
	if not tids:
		return

	tid2tkey(tids, table)

	for row in rows:
		for i, tid in enumerate(row):
			if i==3: break
			tid = int(tid)
			tidabs = abs(tid)
			trm = TID2TKEY.get(tidabs)
			if trm is None:
				raise KeyError(f"Term not found for {tidabs}")
			row[i] = ("'" + trm) if tid < 0 else trm


#### ARR ####

# Replace the string terms with interger TIDs in a marr array
def marr2tid(marr, termput=False, table=DB_TABLE_TERM):
	global TKEY2TID, TID2TKEY

	trms = []

	for mstates in marr:
		for mstate in mstates:
			for mexp in mstate:
				trms[mexp[1]]=mexp[1]

	# If trms is empty, return early
	if not trms:
		return

	tkey2tid(trms, termput, table);

	# Now all strings should be in TKEY2TID
	for mstates in marr:
		for mstate in mstates:
			for mexp in mstate:
				tid = TKEY2TID.get(mexp[1])
				if trm is None:
					raise KeyError(f"Term not found for {mexp[1]}")
				else:
					mexp[1] = tid


# Replace the interger TIDs with string terms in a marr (meme commands) array
def marr2trm(marr, table=DB_TABLE_TERM):

	tids={}

	for mstates in marr:
		for mstate in mstates:
			for mexp in mstate:
				tids[mexp[1]]=mexp[1]

	tid2tkey(tids, table)

	# Now all strings should be in TID2TKEY
	for mstates in marr:
		for mstate in mstates:
			for mexp in mstate:
				tid = int(mexp[1])
				tidabs = abs(tid)
				trm = TID2TKEY.get(tidabs)
				if trm is None:
					raise KeyError(f"Term not found for {tid}")
				mexp[1] = ("'" + trm) if tid < 0 else trm




def morfigy(qry_sql, sql_trms):
	new_query = qry_sql
	for trm in sql_trms:
		if isinstance(trm, str):
			escaped_trm = trm.replace("'", "''")
			replacement = f"'{escaped_trm}'"
		else:
			replacement = str(trm)
		new_query = new_query.replace("%s", replacement, 1)
	return new_query