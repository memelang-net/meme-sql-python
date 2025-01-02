import re
import html
from collections import defaultdict

INVERSE = '*-1' # '-1'
NOTFALSE = '!=0'

# IDs for common values
MEME_FALSE = 0
MEME_TRUE = 1
MEME_UNK = 2

# IDs for operators
MEME_A = 3
MEME_B = 4
MEME_RI = 5
MEME_R = 6
MEME_EQ = 8
MEME_DEQ = 9
MEME_NEQ = 10

MEME_LST = 11
MEME_GRE = 12
MEME_LSE = 13
MEME_GRT = 14

MEME_BA = 20
MEME_BB = 21
MEME_AR = 22

MEME_GET = 30
MEME_ORG = 31

OPR = {
	MEME_A: {
		'long' : '',
		'shrt' : '',
		'grp1' : MEME_A
	},
	MEME_B: {
		'long' : ':',
		'shrt' : ':',
		'grp1' : MEME_B
	},
	MEME_RI: {
		'long' : '\'',
		'shrt' : '\'',
		'grp1' : MEME_R
	},
	MEME_R: {
		'long' : '.',
		'shrt' : '.',
		'grp1' : MEME_R
	},
	MEME_EQ: {
		'long' : '=',
		'shrt' : '=',
		'grp1' : MEME_EQ
	},
	MEME_DEQ: {
		'long' : '#=',
		'shrt' : '=',
		'grp1' : MEME_EQ
	},
	MEME_NEQ : {
		'long' : '!=',
		'shrt' : '!=',
		'grp1' : MEME_EQ
	},
	MEME_GRT : {
		'long' : '>',
		'shrt' : '>',
		'grp1' : MEME_EQ
	},
	MEME_GRE : {
		'long' : '>=',
		'shrt' : '>=',
		'grp1' : MEME_EQ
	},
	MEME_LST : {
		'long' : '<',
		'shrt' : '<',
		'grp1' : MEME_EQ
	},
	MEME_LSE : {
		'long' : '>=',
		'shrt' : '>=',
		'grp1' : MEME_EQ
	},
	MEME_BA : {
		'long' : '[ba]',
		'shrt' : '.',
		'grp1' : MEME_BA
	},
	MEME_BB : {
		'long' : '[bb]',
		'shrt' : '\'',
		'grp1' : MEME_BA
	},
	MEME_AR : {
		'long' : '[ar]',
		'shrt' : '?',
		'grp1' : MEME_BA
	}
}

OPRINT = {
	":": MEME_B,
	".": MEME_R,
	"'": MEME_RI,
	"=": MEME_EQ,
	"#=": MEME_DEQ,
	"!=": MEME_NEQ,
	">": MEME_GRT,
	">=": MEME_GRE,
	"<": MEME_LST,
	"<=" : MEME_LSE,
	"?": MEME_AR,
	"[ar]": MEME_AR,
	"[ba]": MEME_BA,
	"[bb]": MEME_BB,
}

OPRCHAR = {
	".": 1,
	":": 1,
	"'": 1,
	"?": 1,
	"=": 2,
	"!": 2,
	"#": 2,
	">": 2,
	"<": 2,
}


#### PARSE MEMELANG FUNCTIONS ####

# Input: Memelang string
# Output: marr Memelang Array
def mqry2marr(mqry):
	global OPR, OPRCHAR, OPRINT

	# Replace multiple spaces with a single space
	mqry = ' '.join(str(mqry).strip().split())

	# Remove spaces around opr_ids
	mqry = re.sub(r'\s*([!<>=]+)\s*', r'\1', mqry)

	# Prepend zero before decimals, such as =.5 to =0.5
	mqry = re.sub(r'([<>=])(\-?)\.([0-9])', lambda m: f"{m.group(1)}{m.group(2)}0.{m.group(3)}", mqry)

	if mqry == '' or mqry == ';':
		raise Exception("Error: Empty query provided.")

	marr = []
	mstates = []
	meme_expressions = []

	mqry_chars = list(mqry)
	mqry_cnt = len(mqry_chars)

	opr_grp_cnt = {MEME_A: 0, MEME_B: 0, MEME_R: 0, MEME_EQ: 0, MEME_BA: 0}
	opr_id = MEME_A
	opr_grp = MEME_A
	opr_str = ''

	i = 0
	while i < mqry_cnt:
		c = mqry_chars[i]
		operand = ''

		# Semicolon separates commands
		if c == ';':
			opr_id = MEME_A
			opr_grp = MEME_A
			opr_grp_cnt = {MEME_A: 0, MEME_B: 0, MEME_R: 0, MEME_EQ: 0, MEME_BA: 0}
			if opr_id and opr_id!=MEME_A:
				meme_expressions.append([opr_id, None])
			if meme_expressions:
				mstates.append(meme_expressions)
				meme_expressions = []
			if mstates:
				marr.append(mstates)
				mstates = []
			i += 1
			continue

		# Space separates statements
		elif c.isspace():
			opr_id = MEME_A
			opr_grp = MEME_A
			opr_grp_cnt = {MEME_A: 0, MEME_B: 0, MEME_R: 0, MEME_EQ: 0, MEME_BA: 0}
			if opr_id and opr_id!=MEME_A:
				meme_expressions.append([opr_id, None])
			if meme_expressions:
				mstates.append(meme_expressions)
				meme_expressions = []
			i += 1
			continue

		# Comment: skip until newline
		elif c == '/' and i+1 < mqry_cnt and mqry_chars[i+1] == '/':
			while i < mqry_cnt and mqry_chars[i] != '\n':
				i += 1
			i += 1
			continue

		# [xx] opr_id
		elif c == '[':
			if i+3 >= mqry_cnt:
				raise Exception(f"Memelang parse error: Erroneous bracket at char {i} in {mqry}")

			opr_str = mqry[i:i+4]
			if opr_str not in OPRINT:
				raise Exception(f"Memelang parse error: Operator {opr_str} not recognized at char {i} in {mqry}")

			opr_id = OPRINT[opr_str]
			opr_grp = opr_id
			i += 4
			continue

		# Operators
		elif c in OPRINT:

			# previous opr_id followed by empty string
			if opr_id and opr_id!=MEME_A:
				meme_expressions.append([opr_id, None])

			opr_str = ''
			j = 0
			while j < 3 and (i+j) < mqry_cnt:
				cc = mqry_chars[i+j]
				if cc in OPRINT and (j == 0 or OPRCHAR.get(cc) == 2):
					opr_str += cc
					j += 1
				else:
					break

			if opr_str not in OPRINT:
				raise Exception(f"Memelang parse error: Operator {opr_str} not recognized at char {i} in {mqry}")

			opr_id = OPRINT[opr_str]

			# ?A.R:B
			if opr_id == MEME_AR:
				meme_expressions.append([opr_id, None])
				opr_id = MEME_A

			# .R.R
			elif opr_id == MEME_R and opr_grp_cnt[MEME_R] > 1:
				opr_id=MEME_BA

			# 'R'R
			elif opr_id == MEME_RI and opr_grp_cnt[MEME_R] > 1:
				opr_id=MEME_BB

			opr_grp = OPR[opr_id]['grp1']
			opr_grp_cnt[opr_grp] += 1

			# error checks
			if opr_grp == MEME_R and opr_grp_cnt[MEME_B] > 0:
				raise Exception(f"Memelang parse error: Errant R after B at char {i} in {mqry}")

			if opr_grp == MEME_EQ and opr_grp_cnt[MEME_EQ] > 1:
				raise Exception(f"Memelang parse error: Extraneous equality opr_id at char {i} in {mqry}")

			i += j
			continue

		# String/number following equal sign
		elif opr_id == MEME_EQ:
			while i < mqry_cnt and re.match(r'[a-zA-Z0-9_\.\-]', mqry_chars[i]):
				operand += mqry_chars[i]
				i += 1

			# =t for true
			if operand == 't':
				meme_expressions.append([MEME_EQ, MEME_TRUE])
			
			# =f for false
			elif operand == 'f':
				meme_expressions.append([MEME_EQ, MEME_FALSE])

			# =g for get
			elif operand == 'g':
				meme_expressions.append([MEME_EQ, MEME_GET])
			
			# =tn for or-group
			elif operand.startswith('t'):
				tm = re.match(r't(\d+)$', operand)
				if tm:
					meme_expressions.append([MEME_EQ, MEME_TRUE])
					meme_expressions.append([MEME_ORG, int(tm.group(1))])
				else:
					raise Exception(f"Memelang parse error: Unrecognized =Q at char {i} in {mqry}")

			# =number
			else:
				# Validate number
				try:
					float_val = float(operand)
					meme_expressions.append([MEME_DEQ, float_val])
				except ValueError:
					raise Exception(f"Memelang parse error: Malformed number {operand} at char {i} in {mqry}")

			opr_id = 0
			opr_grp = 0
			continue

		# Number following inequal sign
		elif opr_grp == MEME_EQ:
			while i < mqry_cnt and re.match(r'[0-9.\-]', mqry_chars[i]):
				operand += mqry_chars[i]
				i += 1

			# Validate number
			try:
				float_val = float(operand)
				meme_expressions.append([opr_id, float_val])
			except ValueError:
				raise Exception(f"Memelang parse error: Malformed number {operand} at char {i} in {mqry}")

			opr_id = 0
			opr_grp = 0
			continue

		# String following A, R, B, or [xx]
		elif opr_grp == MEME_A or opr_grp == MEME_R or opr_grp == MEME_B or opr_grp == MEME_BA:
			while i < mqry_cnt and re.match(r'[a-zA-Z0-9_]', mqry_chars[i]):
				operand += mqry_chars[i]
				i += 1

			meme_expressions.append([opr_id, operand])

			opr_id = 0
			opr_grp = 0
			continue	

		# Unexpected character
		else:
			raise Exception(f"Memelang parse error: Unexpected character '{mqry_chars[i]}' at char {i} in {mqry}")

	# Finalize parsing
	if opr_id and opr_id!=MEME_A:
		meme_expressions.append([opr_id, None])
	if meme_expressions:
		mstates.append(meme_expressions)
	if mstates:
		marr.append(mstates)

	return marr


# Input: marr Memelang Array
# Output: Memelang string
def marr2mqry(marr, marr2mqry_set=None):
	if marr2mqry_set is None:
		marr2mqry_set = {}

	global OPR

	command_array = []

	for i, mstates in enumerate(marr):
		statement_array = []

		for mstate in mstates:
			marr2mqryd_statement = ''

			for mexp in mstate:
				# mexp is mexpected to be something like [opr_id, operand]
				opr_id = mexp[0]
				operand = mexp[1]

				# Determine the opr_id string
				if opr_id == MEME_EQ:
					opr_str = '='
					if operand == MEME_FALSE:
						operand = 'f'
					elif operand == MEME_TRUE:
						operand = 't'
					elif operand == MEME_GET:
						operand = 'g'
				elif opr_id == MEME_DEQ:
					opr_str = '='
					# Ensure operand is decimal
					if '.' not in str(operand):
						operand = str(operand) + '.0'
				else:
					opr_str = OPR[opr_id]['shrt'] if marr2mqry_set.get('short') else OPR[opr_id]['long'];

				# Append the marr2mqryd mexpression
				if marr2mqry_set.get('html'):
					marr2mqryd_statement += (html.escape(opr_str) +
					  '<var class="v' + str(opr_id) + '">' +
					  html.escape(str(operand)) +
					  '</var>')
				else:
					marr2mqryd_statement += opr_str + str(operand)

			statement_array.append(marr2mqryd_statement)

		command_array.append(' '.join(statement_array))

	if marr2mqry_set.get('html'):
		return '<code class="meme">' + ';</code> <code class="meme">'.join(command_array) + '</code>'
	else:
		return '; '.join(command_array)



#### ROW FUNCTIONS ####

# Input: Array of [A,R,B,Q] tuples
# Output: Memelang string
def meme2mqry(rows):
	result = []
	for row in rows:
		# Determine whether to prefix with '.' based on the first character of R
		prefix = '' if row[1].startswith("'") else '.'

		# Construct the segment for this row
		segment = f"{row[0]}{prefix}{row[1]}:{row[2]}={row[3]};"
		result.append(segment)

	return ''.join(result)


# Input: Memelang string
# Output: Array of [A,R,B,Q] tuples
def mqry2meme(mqry):
	rows = []
	pattern = r'^([A-Za-z0-9_]+)\.([A-Za-z0-9_]+):([A-Za-z0-9_]+)=([+-]?(?:\d+(?:\.\d+)?|\.\d+))$'
	parts = mqry.split(';')
	for part in parts:
		match = re.match(pattern, part)
		if match:
			A, R, B, Q = match.groups()
			rows.append([A, R, B, float(Q)])
		else:
			raise Exception(f'Error: mqry2meme parse fail for {part}')

	return rows


#### SQL FUNCTIONS ####

# Input: Memelang query string
# Output: SQL query string
def mqry2sql(mqry, table='meme'):
	marr = mqry2marr(mqry)
	sqls = []
	trms = []
	for mcmd in marr:
		sql, val = cmd2sql(mcmd, table)
		sqls.append(sql)
		trms.extend(val)
	return [' UNION '.join(sqls), trms]


# Input: marr Memelang command array
# Output: SQL query string
def marr2sql(marr, table='meme'):
	sqls = []
	trms = []
	for mcmd in marr:
		sql, val = cmd2sql(mcmd, table)
		sqls.append(sql)
		trms.extend(val)
	return [' UNION '.join(sqls), trms]


# Input: One memelang command string (;)
# Output: One SQL query string
def cmd2sql(mcmd, table='meme'):
	qry_set = {'all': False}
	true_groups = {}
	false_group = []
	get_statements = []
	or_groups = defaultdict(list)
	true_cnt = 0
	or_cnt = 0
	false_cnt = 0

	# Process each statement
	for mstate in mcmd:
		if not mstate or not mstate[0] or not mstate[0][0]:
			raise Exception('Error: invalid mstate')

		if mstate[0][0] == MEME_A and mstate[0][1] == 'qry':
			qry_set[mstate[1][1]] = True
			continue

		last_mexp = mstate[-1] if mstate else None
		if not last_mexp:
			continue

		# Handle =f (false)
		if last_mexp[0] == MEME_EQ and last_mexp[1] == MEME_FALSE:
			false_cnt += 1
			# all but last mexpression
			false_group.append(mstate[:-1])
			continue

		# Handle =g (get)
		if last_mexp[0] == MEME_EQ and last_mexp[1] == MEME_GET:
			get_statements.append(mstate[:-1])
			continue

		# Handle =tn (OR groups)
		if last_mexp[0] == MEME_ORG:
			or_cnt += 1
			or_groups[last_mexp[1]].append(mstate[:-1])
			continue

		# Default: Add to true conditions
		aid = None
		rids = []
		bid = None
		for mexp in mstate:
			tid=str(mexp[1])
			if mexp[0] == MEME_A:
				aid = tid
			elif mexp[0] == MEME_R:
				rids.append(tid)
			elif mexp[0] == MEME_B:
				bid = tid

		# Build nested dictionary structure:
		# $true_groups[$aid][implode("\t", $rids)][$bid][] = $mstate;
		if aid not in true_groups:
			true_groups[aid] = {}
		rid_key = "\t".join("" if rid is None else rid for rid in rids)
		if rid_key not in true_groups[aid]:
			true_groups[aid][rid_key] = {}
		if bid not in true_groups[aid][rid_key]:
			true_groups[aid][rid_key][bid] = []
		true_groups[aid][rid_key][bid].append(mstate)

		true_cnt += 1

	# If qry_set['all'] and no true/false/or conditions
	if qry_set.get('all') and true_cnt == 0 and false_cnt == 0 and or_cnt == 0:
		return [f"SELECT * FROM {table}", []]

	trms = []
	cte_sqls = []
	cte_outs = []
	sql_outs = []
	cte_cnt = -1

	# Process AND conditions (true_groups)
	for aid_group in true_groups.values():
		for rid_group in aid_group.values():
			for bid_group in rid_group.values():
				wheres = []
				cte_cnt += 1
				# Each bid_group is a list of mstates
				for mstate in bid_group:
					select_sql, from_sql, where_sql, qry_trms, qry_depth = state2sfwd(mstate, table)
					if not wheres:
						wheres.append(where_sql)
						trms.extend(qry_trms)
					else:
						wheres.append(where_sql[where_sql.find('qnt')-4])
						trms.extend(qry_trms[:-1])

				# If not the first CTE, link it to previous CTE
				if cte_cnt > 0:
					wheres.append(f"{select_sql[:6]} IN (SELECT aid FROM z{cte_cnt-1})")

				cte_sqls.append(f"z{cte_cnt} AS (SELECT {select_sql} {from_sql} WHERE {' AND '.join(wheres)})")
				cte_outs.append((cte_cnt, qry_depth))

	# Process OR groups
	# Each key in or_groups is an integer (the tn), or_groups[key] is a list of mstates
	for or_group in or_groups.values():
		cte_cnt += 1
		max_depth = 0
		or_selects = []
		for mstate in or_group:
			select_sql, from_sql, where_sql, qry_trms, qry_depth = state2sfwd(mstate, table)
			max_depth = max(max_depth, qry_depth)
			
			if cte_cnt > 0:
				where_sql += f" AND m0.aid IN (SELECT a0 FROM z{cte_cnt-1})"
			
			or_selects.append(f"SELECT {select_sql} {from_sql} WHERE {where_sql}")
			trms.extend(qry_trms)
		
		cte_sqls.append(f"z{cte_cnt} AS ({' UNION '.join(or_selects)})")
		cte_outs.append((cte_cnt, max_depth))

	# Process NOT conditions (false_group)
	if false_cnt:
		if true_cnt < 1:
			raise Exception('A query with a false statement must contain at least one non-OR true statement.')

		wheres = []
		for mstate in false_group:
			select_sql, from_sql, where_sql, qry_trms, qry_depth = state2sfwd(mstate, table, True)
			wheres.append(f"aid NOT IN (SELECT {select_sql} {from_sql} WHERE {where_sql})")
			trms.extend(qry_trms)

		fsql = f"SELECT aid FROM z{cte_cnt} WHERE " + ' AND '.join(wheres)
		cte_cnt += 1
		cte_sqls.append(f"z{cte_cnt} AS ({fsql})")


	# select all data related to the matching As
	if qry_set.get('all'):
		sql_outs.append(f"SELECT aid as a0, rid as r0, bid as b0, qnt as q0 FROM {table} m0 WHERE m0.aid IN (SELECT a0 FROM z{cte_cnt})")
		sql_outs.append(f"SELECT bid AS a0, rid{INVERSE} AS r0, aid AS b0, qnt AS q0 FROM {table} m0 WHERE m0.bid IN (SELECT a0 FROM z{cte_cnt})")

	else:
		for mstate in get_statements:
			select_sql, from_sql, where_sql, qry_trms, qry_depth = state2sfwd(mstate, table)
			sql_outs.append(f"SELECT {select_sql} {from_sql} WHERE {where_sql} AND m0.aid IN (SELECT a0 FROM z{cte_cnt})")
			trms.extend(qry_trms)

	for zmNum in cte_outs:
		zNum, mNum = zmNum

		cWhere=[];
		if zNum < cte_cnt:
			cWhere.append(f"a0 IN (SELECT a0 FROM z{cte_cnt})")

		m=0;
		while mNum>=m:
			#if m>0:
				#cWhere.append(f"a{m} IS NOT NULL AND r{m} NOT LIKE '?%'")

			sql_outs.append(f"SELECT DISTINCT a{m}, r{m}, b{m}, q{m} FROM z{zNum}" + ('' if len(cWhere)==0 else ' WHERE '+' AND '.join(cWhere) ))
			m+=1

	return ['WITH ' + ', '.join(cte_sqls) + ' ' + ' UNION '.join(sql_outs), trms]


# Input: One Memelang statement array
# Output: SELECT string, FROM string, WHERE string, and depth int
def state2sfwd(mstate, table='meme', aidOnly=False):
	global OPR

	trms = []
	wheres = []
	joins = [f"FROM {table} m0"]
	selects = ['m0.aid AS a0','m0.rid AS r0','m0.bid AS b0','m0.qnt AS q0']
	m = 0
	opr = None
	qnt = None

	for i, mexp in enumerate(mstate):

		# A
		if mexp[0] == MEME_A:
			wheres.append(f'm{m}.aid=%s')
			trms.append(mexp[1])

		# R
		elif mexp[0] == MEME_R:
			if mexp[1] is not None:
				wheres.append(f'm{m}.rid=%s')
				trms.append(mexp[1])

		# RI
		elif mexp[0] == MEME_RI:
			# flip the prior A to a B
			selects[0] = f'm{m}.bid AS a{m}'
			selects[1] = f"m{m}.rid{INVERSE} AS r{m}"
			selects[2] = f'm{m}.aid AS b{m}'
			if i > 0:
				# the previous is presumably m0.aid=A
				wheres[0] = f'm{m}.bid=%s'
				trms[0] = str(mstate[i-1][1])

			if mexp[1] is not None:
				wheres.append(f'm{m}.rid=%s')
				trms.append(mexp[1])

		# B
		elif mexp[0] == MEME_B:
			# inverse if previous was RI or BB
			if i > 0 and (mstate[i-1][0] == MEME_RI or mstate[i-1][0] == MEME_BB):
				wheres.append(f'm{m}.aid=%s')
				trms.append(mexp[1])
			else:
				wheres.append(f'm{m}.bid=%s')
				trms.append(mexp[1])

		# Q (operators)
		elif mexp[0] >= MEME_EQ and mexp[0] <= MEME_GRT:
			opr = OPR[mexp[0]]['shrt']
			qnt = float(mexp[1])

		# JOINS (BA, BB, RA, RB)
		else:
			lm = m
			m += 1
			if mexp[1] is not None:
				wheres.append(f'm{m}.rid=%s')
				trms.append(mexp[1])

			wheres.append(f"m{lm}.qnt{NOTFALSE}")

			if mexp[0] == MEME_BA:
				joins.append(f"JOIN {table} m{m} ON {selects[-2][:6]}=m{m}.aid")
				selects.append(f"m{m}.aid AS a{m}")
				selects.append(f"m{m}.rid AS r{m}")
				selects.append(f"m{m}.bid AS b{m}")
				selects.append(f"m{m}.qnt AS q{m}")
			elif mexp[0] == MEME_BB:
				joins.append(f"JOIN {table} m{m} ON {selects[-2][:6]}=m{m}.bid")
				selects.append(f"m{m}.bid AS a{m}")
				selects.append(f"m{m}.rid{INVERSE} AS r{m}")
				selects.append(f"m{m}.aid AS b{m}")
				selects.append(f"(CASE WHEN m{m}.qnt = 0 THEN 0 ELSE 1 / m{m}.qnt END) AS q{m}")
			elif mexp[0] == MEME_AR:
				joins.append(f"JOIN {table} m{m} ON {selects[-4][:6]}=m{m}.rid")
				selects.append(f"m{m}.aid AS a{m}")
				selects.append(f"m{m}.rid AS r{m}")
				selects.append(f"m{m}.bid AS b{m}")
				selects.append(f"m{m}.qnt AS q{m}")
			else:
				raise Exception('Error: unknown operator')

	# last qnt condition
	if qnt is None:
		wheres.append(f"m{m}.qnt{NOTFALSE}")
	else:
		wheres.append(f"m{m}.qnt{opr}{qnt}")

	if aidOnly:
		selects = ['m0.aid AS a0']

	return [
		', '.join(selects),
		' '.join(joins),
		' AND '.join(wheres),
		trms,
		m
	]
