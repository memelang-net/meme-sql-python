import re
from conf import *
from const import *
from parse import decode, encode

# Define constants
MEME_BID_AS_AID = 'm0.bid AS aid'

# Translate a Memelang query (which may contain multiple commands) into SQL
def sql(meme_string, table=DB_TABLE_MEME):
	queries = []
	meme_commands = decode(meme_string)
	for meme_command in meme_commands:
		queries.append(sql_cmd(meme_command, table))
	return ' UNION ALL '.join(queries)

# Translate one Memelang command into SQL
def sql_cmd(meme_command, table=DB_TABLE_MEME):
	query_settings = {'all': False}
	true_group = {}
	false_group = []
	get_group = []
	or_groups = {}
	true_count = 0
	or_count = 0
	false_count = 0
	get_count = 0

	for meme_statement in meme_command:
		if meme_statement[0][0] == MEME_A and meme_statement[0][1] == 'qry':
			query_settings[meme_statement[1][1]] = True
			continue

		lastexp = meme_statement[-1] if meme_statement else None

		if not lastexp:
			continue

		if lastexp[0] == MEME_EQ:
			if lastexp[1] == MEME_FALSE:
				false_count += 1
				false_group.append(meme_statement[:-1])
				continue
			if lastexp[1] == MEME_GET:
				get_count += 1
				get_group.append(meme_statement[:-1])
				continue

		if lastexp[0] == MEME_ORG:
			or_count += 1
			or_groups.setdefault(lastexp[1], []).append(meme_statement[:-1])
			continue

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

		true_count += 1
		true_group.setdefault(aid, {}).setdefault('\t'.join(rids), {}).setdefault(bid, []).append(meme_statement)

	if query_settings['all'] and true_count == 0 and false_count == 0 and or_count == 0:
		return f"SELECT * FROM {table}"

	cte_sql = []
	cte_count = -1

	for aid_group in true_group.values():
		for rid_group in aid_group.values():
			for bid_group in rid_group.values():
				wheres = []
				cte_count += 1

				for meme_statement in bid_group:
					select, where = sql_select_where(meme_statement, table)
					if not wheres:
						wheres.append(where)
					else:
						wheres.append(where[where.find('qnt') - 4:])

				if cte_count > 0:
					wheres.append(("m0.bid" if MEME_BID_AS_AID in select else "m0.aid") +
					             f" IN (SELECT aid FROM z{cte_count - 1})")

				cte_sql.append(f"z{cte_count} AS ({select} WHERE {' AND '.join(wheres)})")

	for or_group in or_groups.values():
		cte_count += 1
		or_sql = []
		for meme_statement in or_group:
			select, where = sql_select_where(meme_statement, table)
			or_sql.append(f"{select} WHERE {where}" +
			              (f" AND m0.aid IN (SELECT aid FROM z{cte_count - 1})" if cte_count > 0 else ""))
		cte_sql.append(f"z{cte_count} AS ({' UNION ALL '.join(or_sql)})")

	if false_count:
		if true_count < 1:
			raise ValueError("A query with false statements must contain at least one non-OR true statement.")

		false_sql = [f"aid NOT IN ({select} WHERE {where})"
		             for select, where in (sql_select_where(statement, table, True) for statement in false_group)]
		cte_sql.append(f"z{cte_count + 1} AS (SELECT aid FROM z{cte_count} WHERE {' AND '.join(false_sql)})")
		cte_count += 1

	select_sql = []

	if query_settings['all']:
		select_sql.append(f"SELECT * FROM {table} WHERE aid IN (SELECT aid FROM z{cte_count})")
		select_sql.append(f"SELECT bid AS aid, CONCAT('\'', rid), aid as bid, qnt FROM {table} WHERE bid IN (SELECT aid FROM z{cte_count})")
	elif cte_count == 0:
		return cte_sql[0][cte_sql[0].find('(') + 1:-1]
	else:
		for meme_statement in get_group:
			select, where = sql_select_where(meme_statement, table)
			select_sql.append(f"{select} WHERE {where} AND m0.aid IN (SELECT aid FROM z{cte_count})")

	return f"WITH {', '.join(cte_sql)} {' UNION ALL '.join(select_sql)}"

# Translate a meme_statement array into SQL
def sql_select_where(meme_statement, table=DB_TABLE_MEME, aid_only=False):
	wheres = []
	joins = [f"FROM {table} m0"]
	selects = ["m0.aid AS aid"]
	rids = ["m0.rid"]
	bids = ["m0.bid"]
	qnts = ["m0.qnt"]
	m = 0
	opr = "!="
	qnt = 0

	for i, exp in enumerate(meme_statement):
		if exp[0] == MEME_A:
			wheres.append(f"m0.aid='{exp[1]}'")
		elif exp[0] == MEME_R:
			if exp[1] is not None:
				wheres.append(f"m0.rid='{exp[1]}'")
		elif exp[0] == MEME_RI:
			selects[0] = MEME_BID_AS_AID
			if i > 0:
				wheres[0] = f"m0.bid='{meme_statement[i - 1][1]}'"
			if exp[1] is not None:
				wheres.append(f"m0.rid='{exp[1]}'")
			rids[0] = "CONCAT('\'', m0.rid)"
			bids[0] = "m0.aid"
		elif exp[0] == MEME_B:
			if meme_statement[i - 1][0] in {MEME_RI, MEME_BB}:
				wheres.append(f"m{m}.aid='{exp[1]}'")
			else:
				wheres.append(f"m{m}.bid='{exp[1]}'")
		elif MEME_EQ <= exp[0] <= MEME_LSE:
			opr = "=" if exp[0] == MEME_DEQ else OPRSTR[exp[0]]
			qnt = exp[1]
		else:
			lm = m
			m += 1
			wheres.append(f"m{m}.rid='{exp[1]}'")
			wheres.append(f"m{lm}.qnt!=0")
			if exp[0] == MEME_BA:
				joins.append(f"JOIN {table} m{m} ON {bids[-1]}=m{m}.aid")
				rids.append(f"m{m}.rid")
				bids.append(f"m{m}.bid")
				qnts.append(f"m{m}.qnt")
			elif exp[0] == MEME_BB:
				joins.append(f"JOIN {table} m{m} ON {bids[-1]}=m{m}.bid")
				rids.append(f"CONCAT('\'', m{m}.rid)")
				bids.append(f"m{m}.aid")
				qnts.append(f"(CASE WHEN m{m}.qnt = 0 THEN 0 ELSE 1 / m{m}.qnt END)")
			elif exp[0] == MEME_RA:
				joins.append(f"JOIN {table} m{m} ON m{lm}.rid=m{m}.aid")
				rids.append(f"CONCAT('?', m{m}.rid)")
				bids.append(f"m{m}.bid")
				qnts.append(f"m{m}.qnt")
			elif exp[0] == MEME_RB:
				joins.append(f"JOIN {table} m{m} ON m{lm}.rid=m{m}.bid")
				rids.append(f"CONCAT('\'', m{m}.rid)")
				bids.append(f"m{m}.aid")
				qnts.append(f"(CASE WHEN m{m}.qnt = 0 THEN 0 ELSE 1 / m{m}.qnt END)")
			else:
				raise ValueError("Error: unknown operator")

	wheres.append(f"m{m}.qnt{opr}{qnt}")

	if aid_only:
		return ["SELECT aid", " FROM z0"]
	elif m == 0 and ".aid" not in bids[0]:
		selects = ["*"]
	elif m == 0:
		selects += [f"{rids[0]} AS rid", f"{bids[0]} AS bid", f"{qnts[0]} AS qnt"]
	else:
		selects += [
			f"CONCAT({', '.join(rids)}) AS rid",
			f"CONCAT({', '.join(bids)}) AS bid",
			f"CONCAT({', '.join(qnts)}) AS qnt",
		]

	return [f"SELECT {', '.join(selects)} {' '.join(joins)}", ' AND '.join(wheres)]
