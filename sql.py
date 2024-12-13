import re
from conf import *
from const import *
from parse import decode, encode
from collections import defaultdict

# Example constant (must define properly)
MEME_BID_AS_AID = 'm0.bid AS aid'

def sql(meme_string, table=DB_TABLE_MEME):
	meme_commands = decode(meme_string)
	queries = []
	for meme_command in meme_commands:
		queries.append(sql_cmd(meme_command, table))
	return ' UNION '.join(queries)


def sql_cmd(meme_command, table=DB_TABLE_MEME):
	querySettings = {'all': False}
	trueGroup = {}
	falseGroup = []
	getGroup = []
	orGroups = defaultdict(list)

	trueCount = 0
	orCount = 0
	falseCount = 0
	getCount = 0

	# Process each statement
	for memeStatement in meme_command:
		if memeStatement and memeStatement[0][0] == MEME_A and memeStatement[0][1] == 'qry':
			querySettings[memeStatement[1][1]] = True
			continue

		lastexp = memeStatement[-1] if memeStatement else None
		if not lastexp:
			continue

		# Handle =f (false)
		if lastexp[0] == MEME_EQ and lastexp[1] == MEME_FALSE:
			falseCount += 1
			# all but last expression
			falseGroup.append(memeStatement[:-1])
			continue

		# Handle =g (get)
		if lastexp[0] == MEME_EQ and lastexp[1] == MEME_GET:
			getCount += 1
			getGroup.append(memeStatement[:-1])
			continue

		# Handle =tn (OR groups)
		if lastexp[0] == MEME_ORG:
			orCount += 1
			orGroups[lastexp[1]].append(memeStatement[:-1])
			continue

		# Default: Add to true conditions
		aid = None
		rids = []
		bid = None
		for exp in memeStatement:
			if exp[0] == MEME_A:
				aid = exp[1]
			elif exp[0] == MEME_R:
				rids.append(exp[1])
			elif exp[0] == MEME_B:
				bid = exp[1]

		# Build nested dictionary structure:
		# $trueGroup[$aid][implode("\t", $rids)][$bid][] = $memeStatement;
		if aid not in trueGroup:
			trueGroup[aid] = {}
		rid_key = "\t".join("" if rid is None else rid for rid in rids)
		if rid_key not in trueGroup[aid]:
			trueGroup[aid][rid_key] = {}
		if bid not in trueGroup[aid][rid_key]:
			trueGroup[aid][rid_key][bid] = []
		trueGroup[aid][rid_key][bid].append(memeStatement)

		trueCount += 1

	# If querySettings['all'] and no true/false/or conditions
	if querySettings.get('all') and trueCount == 0 and falseCount == 0 and orCount == 0:
		return f"SELECT * FROM {table}"

	cteSQL = []
	cteOut = []
	cteCount = -1

	# Process AND conditions (trueGroup)
	for aidGroup in trueGroup.values():
		for ridGroup in aidGroup.values():
			for bidGroup in ridGroup.values():
				wheres = []
				cteCount += 1
				# Each bidGroup is a list of memeStatements
				for memeStatement in bidGroup:
					sql_select, sql_join, sql_where, sql_depth = sql_select_join_where(memeStatement, table)
					if not wheres:
						wheres.append(sql_where)
					else:
						wheres.append(sql_where[sql_where.find('qnt')-4])

				# If not the first CTE, link it to previous CTE
				if cteCount > 0:
					wheres.append(f"{sql_select[:6]} IN (SELECT aid FROM z{cteCount-1})")

				cteSQL.append(f"z{cteCount} AS (SELECT {sql_select} {sql_join} WHERE {' AND '.join(wheres)})")
				cteOut.append((cteCount, sql_depth))

	# Process OR groups
	# Each key in orGroups is an integer (the tn), orGroups[key] is a list of memeStatements
	for orGroup in orGroups.values():
		cteCount += 1
		max_depth = 0
		orSQL = []
		for memeStatement in orGroup:
			sql_select, sql_join, sql_where, sql_depth = sql_select_join_where(memeStatement, table)
			max_depth = max(max_depth, sql_depth)
			cond = sql_where
			
			if cteCount > 0:
				cond += f" AND m0.aid IN (SELECT a0 FROM z{cteCount-1})"
			
			orSQL.append(f"SELECT {sql_select} {sql_join} WHERE {cond}")
		
		cteSQL.append(f"z{cteCount} AS ({' UNION '.join(orSQL)})")
		cteOut.append((cteCount, max_depth))

	# Process NOT conditions (falseGroup)
	if falseCount:
		if trueCount < 1:
			raise Exception('A query with a false statements must contain at least one non-OR true statement.')

		falseSQL = []
		for memeStatement in falseGroup:
			sql_select, sql_join, sql_where, sql_depth = sql_select_join_where(memeStatement, table, True)
			falseSQL.append(f"aid NOT IN (SELECT {sql_select} {sql_join} WHERE {sql_where})")

		fsql = f"SELECT aid FROM z{cteCount} WHERE " + ' AND '.join(falseSQL)
		cteCount += 1
		cteSQL.append(f"z{cteCount} AS ({fsql})")

	selectSQL = []

	# select all data related to the matching As
	if querySettings.get('all'):
		selectSQL.append(f"SELECT aid as a0, rid as r0, bid as b0, qnt as q0 FROM {table} m0 WHERE m0.aid IN (SELECT a0 FROM z{cteCount})")
		selectSQL.append(f"SELECT bid AS a0, CONCAT(\"'\", rid) AS r0, aid AS b0, qnt AS q0 FROM {table} m0 WHERE m0.bid IN (SELECT a0 FROM z{cteCount})")

	else:
		for memeStatement in getGroup:
			sql_select, sql_join, sql_where, sql_depth = sql_select_join_where(memeStatement, table)
			selectSQL.append(f"SELECT {sql_select} {sql_join} WHERE {sql_where} AND m0.aid IN (SELECT a0 FROM z{cteCount})")

	for zmNum in cteOut:
		zNum, mNum = zmNum

		cWhere=[];
		if zNum < cteCount:
			cWhere.append(f"a0 IN (SELECT a0 FROM z{cteCount})")

		cg=0;
		while mNum>=cg:
			if cg>0:
				cWhere.append(f"a{cg} IS NOT NULL AND r{cg} NOT LIKE '?%'")

			selectSQL.append(f"SELECT DISTINCT a{cg}, r{cg}, b{cg}, q{cg} FROM z{zNum}" + ('' if len(cWhere)==0 else ' WHERE '+' AND '.join(cWhere) ))
			cg+=1


	return 'WITH ' + ', '.join(cteSQL) + ' ' + ' UNION '.join(selectSQL)


def sql_select_join_where(memeStatement, table=DB_TABLE_MEME, aidOnly=False):
	global OPRSTR

	wheres = []
	joins = [f"FROM {table} m0"]
	selects = ['m0.aid AS a0','m0.rid AS r0','m0.bid AS b0','m0.qnt AS q0']
	m = 0
	opr = '!='
	qnt = 0

	for i, exp in enumerate(memeStatement):
		# A
		if exp[0] == MEME_A:
			wheres.append(f"m0.aid='{exp[1]}'")

		# R
		elif exp[0] == MEME_R:
			if exp[1] is not None:
				wheres.append(f"m0.rid='{exp[1]}'")

		# RI
		elif exp[0] == MEME_RI:
			# flip the prior A to a B
			selects[0] = 'm0.bid AS a0'
			selects[1] = 'CONCAT("\'", m0.rid) AS r0'
			selects[2] = 'm0.aid AS b0'
			if i > 0:
				# the previous is presumably m0.aid=A
				prevVal = memeStatement[i-1][1]
				wheres[0] = f'm0.bid="{prevVal}"'

			if exp[1] is not None:
				wheres.append(f'm0.rid="{exp[1]}"')

		# B
		elif exp[0] == MEME_B:
			# inverse if previous was RI or BB
			if i > 0 and (memeStatement[i-1][0] == MEME_RI or memeStatement[i-1][0] == MEME_BB):
				wheres.append(f"m{m}.aid='{exp[1]}'")
			else:
				wheres.append(f"m{m}.bid='{exp[1]}'")

		# Q (operators)
		elif exp[0] >= MEME_EQ and exp[0] <= MEME_LSE:
			opr = '=' if exp[0] == MEME_DEQ else OPRSTR[exp[0]]
			qnt = exp[1]

		# JOINS (BA, BB, RA, RB)
		else:
			lm = m
			m += 1
			if exp[1] is not None:
				wheres.append(f'm{m}.rid="{exp[1]}"')

			wheres.append(f"m{lm}.qnt!=0")

			if exp[0] == MEME_BA:
				joins.append(f"JOIN {table} m{m} ON {selects[-2][:6]}=m{m}.aid")
				selects.append(f"m{m}.aid AS a{m}")
				selects.append(f"m{m}.rid AS r{m}")
				selects.append(f"m{m}.bid AS b{m}")
				selects.append(f"m{m}.qnt AS q{m}")
			elif exp[0] == MEME_BB:
				joins.append(f"JOIN {table} m{m} ON {selects[-2][:6]}=m{m}.bid")
				selects.append(f"m{m}.bid AS a{m}")
				selects.append(f'CONCAT("\'", m{m}.rid) AS r{m}')
				selects.append(f"m{m}.aid AS b{m}")
				selects.append(f"(CASE WHEN m{m}.qnt = 0 THEN 0 ELSE 1 / m{m}.qnt END) AS q{m}")
			elif exp[0] == MEME_RA:
				joins.append(f"JOIN {table} m{m} ON m{lm}.rid=m{m}.aid")
				selects.append(f"m{m}.aid AS a{m}")
				selects.append(f'CONCAT("?", m{m}.rid) AS r{m}')
				selects.append(f"m{m}.bid AS b{m}")
				selects.append(f"m{m}.qnt AS q{m}")
			elif exp[0] == MEME_RB:
				joins.append(f"JOIN {table} m{m} ON m{lm}.rid=m{m}.bid")
				selects.append(f"m{m}.bid AS a{m}")
				selects.append(f'CONCAT("\'", m{m}.rid) AS r{m}')
				selects.append(f"m{m}.aid AS b{m}")
				selects.append(f"(CASE WHEN m{m}.qnt = 0 THEN 0 ELSE 1 / m{m}.qnt END) AS q{m}")
			else:
				raise Exception('Error: unknown operator')

	# last qnt condition
	wheres.append(f"m{m}.qnt{opr}{qnt}")

	if aidOnly:
		selects = ['m0.aid AS a0']

	return [
		', '.join(selects),
		' '.join(joins),
		' AND '.join(wheres),
		m
	]
