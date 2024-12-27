import re
import html
from collections import defaultdict

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
MEME_RA = 22
MEME_RB = 23
MEME_GET = 30
MEME_ORG = 31
MEME_TERM = 99

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
	MEME_RA : {
		'long' : '[ra]',
		'shrt' : '?',
		'grp1' : MEME_BA
	},
	MEME_RB : {
		'long' : '[rb]',
		'shrt' : '?\'',
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
	"?": MEME_RA,
	"[ra]": MEME_RA,
	"?'": MEME_RB,
	"[rb]": MEME_RB,
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


# Input: Memelang string
# Output: meme_commands Memelang Array
def str2arr(meme_string):
	global OPR, OPRCHAR, OPRINT

	# Replace multiple spaces with a single space
	meme_string = ' '.join(meme_string.strip().split())

	# Remove spaces around opr_ids
	meme_string = re.sub(r'\s*([!<>=]+)\s*', r'\1', meme_string)

	# Prepend zero before decimals, such as =.5 to =0.5
	meme_string = re.sub(r'([<>=])(\-?)\.([0-9])', lambda m: f"{m.group(1)}{m.group(2)}0.{m.group(3)}", meme_string)

	if meme_string == '' or meme_string == ';':
		raise Exception("Error: Empty query provided.")

	meme_commands = []
	meme_statements = []
	meme_expressions = []

	meme_string_chars = list(meme_string)
	meme_string_cnt = len(meme_string_chars)

	opr_grp_cnt = {MEME_A: 0, MEME_B: 0, MEME_R: 0, MEME_EQ: 0, MEME_BA: 0}
	opr_id = MEME_A
	opr_grp = MEME_A
	opr_str = ''

	i = 0
	while i < meme_string_cnt:
		c = meme_string_chars[i]
		operand = ''

		# Semicolon separates commands
		if c == ';':
			opr_id = MEME_A
			opr_grp = MEME_A
			opr_grp_cnt = {MEME_A: 0, MEME_B: 0, MEME_R: 0, MEME_EQ: 0, MEME_BA: 0}
			if meme_expressions:
				meme_statements.append(meme_expressions)
				meme_expressions = []
			if meme_statements:
				meme_commands.append(meme_statements)
				meme_statements = []
			i += 1
			continue

		# Space separates statements
		elif c.isspace():
			opr_id = MEME_A
			opr_grp = MEME_A
			opr_grp_cnt = {MEME_A: 0, MEME_B: 0, MEME_R: 0, MEME_EQ: 0, MEME_BA: 0}
			if meme_expressions:
				meme_statements.append(meme_expressions)
				meme_expressions = []
			i += 1
			continue

		# Comment: skip until newline
		elif c == '/' and i+1 < meme_string_cnt and meme_string_chars[i+1] == '/':
			while i < meme_string_cnt and meme_string_chars[i] != '\n':
				i += 1
			i += 1
			continue

		# [xx] opr_id
		elif c == '[':
			if i+3 >= meme_string_cnt:
				raise Exception(f"Memelang parse error: Erroneous bracket at char {i} in {meme_string}")

			opr_str = meme_string[i:i+4]
			if opr_str not in OPRINT:
				raise Exception(f"Memelang parse error: Operator {opr_str} not recognized at char {i} in {meme_string}")

			opr_id = OPRINT[opr_str]
			opr_grp = opr_id
			i += 4
			continue

		# Operators
		elif c in OPRINT:
			# previous opr_id followed by empty string
			if opr_id == MEME_R:
				meme_expressions.append([MEME_BA, None])
			elif opr_id == MEME_RI:
				meme_expressions.append([(MEME_BB if opr_grp_cnt[MEME_R] > 1 else MEME_RI), None])
			elif opr_id > MEME_A:
				raise Exception(f"Memelang parse error: Errant double opr_id at char {i} in {meme_string}")

			opr_str = ''
			j = 0
			while j < 3 and (i+j) < meme_string_cnt:
				cc = meme_string_chars[i+j]
				if cc in OPRINT and (j == 0 or OPRCHAR.get(cc) == 2):
					opr_str += cc
					j += 1
				else:
					break

			if opr_str not in OPRINT:
				raise Exception(f"Memelang parse error: Operator {opr_str} not recognized at char {i} in {meme_string}")

			opr_id = OPRINT[opr_str]
			opr_grp = OPR[opr_id]['grp1']
			opr_grp_cnt[opr_grp] += 1

			# error checks
			if opr_grp == MEME_R and opr_grp_cnt[MEME_B] > 0:
				raise Exception(f"Memelang parse error: Errant R after B at char {i} in {meme_string}")

			if opr_grp == MEME_EQ and opr_grp_cnt[MEME_EQ] > 1:
				raise Exception(f"Memelang parse error: Extraneous equality opr_id at char {i} in {meme_string}")

			i += j
			continue

		# String/number following equal sign
		elif opr_id == MEME_EQ:
			while i < meme_string_cnt and re.match(r'[a-zA-Z0-9_\.\-]', meme_string_chars[i]):
				operand += meme_string_chars[i]
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
					raise Exception(f"Memelang parse error: Unrecognized =Q at char {i} in {meme_string}")

			# =number
			else:
				# Validate number
				try:
					float_val = float(operand)
					meme_expressions.append([MEME_DEQ, float_val])
				except ValueError:
					raise Exception(f"Memelang parse error: Malformed number {operand} at char {i} in {meme_string}")

			opr_id = 0
			opr_grp = 0
			continue

		# Number following inequal sign
		elif opr_grp == MEME_EQ:
			while i < meme_string_cnt and re.match(r'[0-9.\-]', meme_string_chars[i]):
				operand += meme_string_chars[i]
				i += 1

			# Validate number
			try:
				float_val = float(operand)
				meme_expressions.append([opr_id, float_val])
			except ValueError:
				raise Exception(f"Memelang parse error: Malformed number {operand} at char {i} in {meme_string}")

			opr_id = 0
			opr_grp = 0
			continue

		# String following A, R, B, or [xx]
		elif opr_grp == MEME_A or opr_grp == MEME_R or opr_grp == MEME_B or opr_grp == MEME_BA:
			while i < meme_string_cnt and re.match(r'[a-zA-Z0-9_]', meme_string_chars[i]):
				operand += meme_string_chars[i]
				i += 1

			# .R.R
			if opr_id == MEME_R and opr_grp_cnt[MEME_R] > 1:
				meme_expressions.append([MEME_BA, operand])

			# 'R'R
			elif opr_id == MEME_RI and opr_grp_cnt[MEME_R] > 1:
				meme_expressions.append([MEME_BB, operand])

			else:
				meme_expressions.append([opr_id, operand])

			opr_id = 0
			opr_grp = 0
			continue	

		# Unexpected character
		else:
			raise Exception(f"Memelang parse error: Unexpected character '{meme_string_chars[i]}' at char {i} in {meme_string}")

	# Finalize parsing
	if opr_id == MEME_RI:
		meme_expressions.append([(MEME_BB if opr_grp_cnt[MEME_R] > 1 else MEME_RI), None])
	if opr_id == MEME_R and opr_grp_cnt[MEME_R] > 1:
		meme_expressions.append([MEME_BA, None])

	if meme_expressions:
		meme_statements.append(meme_expressions)
	if meme_statements:
		meme_commands.append(meme_statements)

	return meme_commands


# Input: meme_commands Memelang Array
# Output: Memelang string
def arr2str(meme_commands, arr2str_set=None):
	if arr2str_set is None:
		arr2str_set = {}

	global OPR

	command_array = []

	for i, meme_statements in enumerate(meme_commands):
		statement_array = []

		for statement in meme_statements:
			arr2strd_statement = ''

			for exp in statement:
				# exp is expected to be something like [opr_id, operand]
				opr_id = exp[0]
				operand = exp[1]

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
					opr_str = OPR[opr_id]['shrt'] if arr2str_set.get('short') else OPR[opr_id]['long'];

				# Append the arr2strd expression
				if arr2str_set.get('html'):
					arr2strd_statement += (html.escape(opr_str) +
					  '<var class="v' + str(opr_id) + '">' +
					  html.escape(str(operand)) +
					  '</var>')
				else:
					arr2strd_statement += opr_str + str(operand)

			statement_array.append(arr2strd_statement)

		command_array.append(' '.join(statement_array))

	if arr2str_set.get('html'):
		return '<code class="meme">' + ';</code> <code class="meme">'.join(command_array) + '</code>'
	else:
		return '; '.join(command_array)


# Input: Array of [A,R,B,Q] tuples
# Output: Memelang string
def row2str(rows):
	result = []
	for row in rows:
		# Determine whether to prefix with '.' based on the first character of R
		prefix = '' if row[1].startswith("'") else '.'

		# Construct the segment for this row
		segment = f"{row[0]}{prefix}{row[1]}:{row[2]}={row[3]};"
		result.append(segment)

	return ''.join(result)


# Input: Memelang query string
# Output: SQL query string
def str2sql(meme_string, table='meme'):
	meme_commands = str2arr(meme_string)
	queries = []
	for meme_command in meme_commands:
		queries.append(cmd2sql(meme_command, table))
	return ' UNION '.join(queries)


# Input: meme_commands Memelang command array
# Output: SQL query string
def arr2sql(meme_commands, table='meme'):
	queries = []
	for meme_command in meme_commands:
		queries.append(cmd2sql(meme_command, table))
	return ' UNION '.join(queries)


# Input: One memelang command string (;)
# Output: One SQL query string
def cmd2sql(meme_command, table='meme'):
	qry_set = {'all': False}
	true_groups = {}
	false_group = []
	get_statements = []
	or_groups = defaultdict(list)
	true_cnt = 0
	or_cnt = 0
	false_cnt = 0

	# Process each statement
	for meme_statement in meme_command:
		if not meme_statement or not meme_statement[0] or not meme_statement[0][0]:
			raise Exception('Error: invalid meme_statement')

		if meme_statement[0][0] == MEME_A and meme_statement[0][1] == 'qry':
			qry_set[meme_statement[1][1]] = True
			continue

		lastexp = meme_statement[-1] if meme_statement else None
		if not lastexp:
			continue

		# Handle =f (false)
		if lastexp[0] == MEME_EQ and lastexp[1] == MEME_FALSE:
			false_cnt += 1
			# all but last expression
			false_group.append(meme_statement[:-1])
			continue

		# Handle =g (get)
		if lastexp[0] == MEME_EQ and lastexp[1] == MEME_GET:
			get_statements.append(meme_statement[:-1])
			continue

		# Handle =tn (OR groups)
		if lastexp[0] == MEME_ORG:
			or_cnt += 1
			or_groups[lastexp[1]].append(meme_statement[:-1])
			continue

		# Default: Add to true conditions
		aid = None
		rids = []
		bid = None
		for exp in meme_statement:
			if exp[0] == MEME_A:
				aid = exp[1]
			elif exp[0] == MEME_R:
				rids.append(exp[1])
			elif exp[0] == MEME_B:
				bid = exp[1]

		# Build nested dictionary structure:
		# $true_groups[$aid][implode("\t", $rids)][$bid][] = $meme_statement;
		if aid not in true_groups:
			true_groups[aid] = {}
		rid_key = "\t".join("" if rid is None else rid for rid in rids)
		if rid_key not in true_groups[aid]:
			true_groups[aid][rid_key] = {}
		if bid not in true_groups[aid][rid_key]:
			true_groups[aid][rid_key][bid] = []
		true_groups[aid][rid_key][bid].append(meme_statement)

		true_cnt += 1

	# If qry_set['all'] and no true/false/or conditions
	if qry_set.get('all') and true_cnt == 0 and false_cnt == 0 and or_cnt == 0:
		return f"SELECT * FROM {table}"

	cte_gets = []
	cte_outs = []
	sql_outs = []
	cte_cnt = -1

	# Process AND conditions (true_groups)
	for aid_group in true_groups.values():
		for rid_group in aid_group.values():
			for bid_group in rid_group.values():
				wheres = []
				cte_cnt += 1
				# Each bid_group is a list of meme_statements
				for meme_statement in bid_group:
					sql_select, sql_from, sql_where, sql_depth = state2sfwd(meme_statement, table)
					if not wheres:
						wheres.append(sql_where)
					else:
						wheres.append(sql_where[sql_where.find('qnt')-4])

				# If not the first CTE, link it to previous CTE
				if cte_cnt > 0:
					wheres.append(f"{sql_select[:6]} IN (SELECT aid FROM z{cte_cnt-1})")

				cte_gets.append(f"z{cte_cnt} AS (SELECT {sql_select} {sql_from} WHERE {' AND '.join(wheres)})")
				cte_outs.append((cte_cnt, sql_depth))

	# Process OR groups
	# Each key in or_groups is an integer (the tn), or_groups[key] is a list of meme_statements
	for or_group in or_groups.values():
		cte_cnt += 1
		max_depth = 0
		or_selects = []
		for meme_statement in or_group:
			sql_select, sql_from, sql_where, sql_depth = state2sfwd(meme_statement, table)
			max_depth = max(max_depth, sql_depth)
			
			if cte_cnt > 0:
				sql_where += f" AND m0.aid IN (SELECT a0 FROM z{cte_cnt-1})"
			
			or_selects.append(f"SELECT {sql_select} {sql_from} WHERE {sql_where}")
		
		cte_gets.append(f"z{cte_cnt} AS ({' UNION '.join(or_selects)})")
		cte_outs.append((cte_cnt, max_depth))

	# Process NOT conditions (false_group)
	if false_cnt:
		if true_cnt < 1:
			raise Exception('A query with a false statements must contain at least one non-OR true statement.')

		wheres = []
		for meme_statement in false_group:
			sql_select, sql_from, sql_where, sql_depth = state2sfwd(meme_statement, table, True)
			wheres.append(f"aid NOT IN (SELECT {sql_select} {sql_from} WHERE {sql_where})")

		fsql = f"SELECT aid FROM z{cte_cnt} WHERE " + ' AND '.join(wheres)
		cte_cnt += 1
		cte_gets.append(f"z{cte_cnt} AS ({fsql})")


	# select all data related to the matching As
	if qry_set.get('all'):
		sql_outs.append(f"SELECT aid as a0, rid as r0, bid as b0, qnt as q0 FROM {table} m0 WHERE m0.aid IN (SELECT a0 FROM z{cte_cnt})")
		sql_outs.append(f"SELECT bid AS a0, CONCAT(\"'\", rid) AS r0, aid AS b0, qnt AS q0 FROM {table} m0 WHERE m0.bid IN (SELECT a0 FROM z{cte_cnt})")

	else:
		for meme_statement in get_statements:
			sql_select, sql_from, sql_where, sql_depth = state2sfwd(meme_statement, table)
			sql_outs.append(f"SELECT {sql_select} {sql_from} WHERE {sql_where} AND m0.aid IN (SELECT a0 FROM z{cte_cnt})")

	for zmNum in cte_outs:
		zNum, mNum = zmNum

		cWhere=[];
		if zNum < cte_cnt:
			cWhere.append(f"a0 IN (SELECT a0 FROM z{cte_cnt})")

		m=0;
		while mNum>=m:
			if m>0:
				cWhere.append(f"a{m} IS NOT NULL AND r{m} NOT LIKE '?%'")

			sql_outs.append(f"SELECT DISTINCT a{m}, r{m}, b{m}, q{m} FROM z{zNum}" + ('' if len(cWhere)==0 else ' WHERE '+' AND '.join(cWhere) ))
			m+=1

	return 'WITH ' + ', '.join(cte_gets) + ' ' + ' UNION '.join(sql_outs)


# Input: One Memelang statement array
# Output: SELECT string, FROM string, WHERE string, and depth int
def state2sfwd(meme_statement, table='meme', aidOnly=False):
	global OPR

	wheres = []
	joins = [f"FROM {table} m0"]
	selects = ['m0.aid AS a0','m0.rid AS r0','m0.bid AS b0','m0.qnt AS q0']
	m = 0
	opr = '!='
	qnt = 0

	for i, exp in enumerate(meme_statement):
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
				prevVal = meme_statement[i-1][1]
				wheres[0] = f'm0.bid="{prevVal}"'

			if exp[1] is not None:
				wheres.append(f'm0.rid="{exp[1]}"')

		# B
		elif exp[0] == MEME_B:
			# inverse if previous was RI or BB
			if i > 0 and (meme_statement[i-1][0] == MEME_RI or meme_statement[i-1][0] == MEME_BB):
				wheres.append(f"m{m}.aid='{exp[1]}'")
			else:
				wheres.append(f"m{m}.bid='{exp[1]}'")

		# Q (operators)
		elif exp[0] >= MEME_EQ and exp[0] <= MEME_LSE:
			opr = OPR[exp[0]]['shrt']
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
