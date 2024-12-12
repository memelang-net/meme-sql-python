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
    return ' UNION ALL '.join(queries)


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
                    select_, where_ = sql_select_where(memeStatement, table)
                    if not wheres:
                        wheres.append(where_)
                    else:
                        # In PHP: substr($where, strpos($where, 'qnt')-4, 99)
                        # Extracting from $where: we find 'qnt' and take substr
                        # We'll replicate logic:
                        qnt_pos = where_.find('qnt')
                        if qnt_pos != -1:
                            where_sub = where_[qnt_pos-4 : qnt_pos-4+99]
                        else:
                            # fallback: if 'qnt' not found, append whole where?
                            where_sub = where_
                        wheres.append(where_sub)

                # If not the first CTE, link it to previous CTE
                if cteCount > 0:
                    # Check if MEME_BID_AS_AID in select_ to determine join column
                    join_col = 'm0.bid' if MEME_BID_AS_AID in select_ else 'm0.aid'
                    wheres.append(f"{join_col} IN (SELECT aid FROM z{cteCount-1})")

                cteSQL.append(f"z{cteCount} AS ({select_} WHERE {' AND '.join(wheres)})")
                cteOut.append(cteCount)

    # Process OR groups
    # Each key in orGroups is an integer (the tn), orGroups[key] is a list of memeStatements
    for orGroup in orGroups.values():
        cteCount += 1
        orSQL = []
        for memeStatement in orGroup:
            select_, where_ = sql_select_where(memeStatement, table)
            cond = where_
            if cteCount > 0:
                cond += f" AND m0.aid IN (SELECT aid FROM z{cteCount-1})"
            orSQL.append(select_ + " WHERE " + cond)
        cteSQL.append(f"z{cteCount} AS ({' UNION ALL '.join(orSQL)})")
        cteOut.append(cteCount)

    # Process NOT conditions (falseGroup)
    if falseCount:
        if trueCount < 1:
            raise Exception('A query with a false statements must contain at least one non-OR true statement.')

        falseSQL = []
        for memeStatement in falseGroup:
            select_, where_ = sql_select_where(memeStatement, table, True)
            # "aid NOT IN ( SELECT ... WHERE ... )"
            # The original code: "aid NOT IN (" . implode(' WHERE ', sql_select_where($memeStatement,$table,true)) . ')'
            # sql_select_where returns [select, where], so 'WHERE' joining them doesn't make sense.
            # The original code does `implode(' WHERE ', sql_select_where($memeStatement, $table, true))`.
            # This implies sql_select_where returns [select, where]. So "SELECT ... FROM ...", "condition".
            # "WHERE" to join might be a quirk. We'll replicate logic:
            # "aid NOT IN (" + select + " WHERE " + where + ")"
            falseSQL.append("aid NOT IN (" + select_ + " WHERE " + where_ + ")")

        fsql = f"SELECT aid FROM z{cteCount} WHERE " + ' AND '.join(falseSQL)
        cteCount += 1
        cteSQL.append(f"z{cteCount} AS ({fsql})")

    selectSQL = []

    # select all data related to the matching As
    if querySettings.get('all'):
        selectSQL.append(f"SELECT * FROM {table} WHERE aid IN (SELECT aid FROM z{cteCount})")
        selectSQL.append(f"SELECT bid AS aid, CONCAT(\"'\", rid), aid as bid, qnt FROM {table} WHERE bid IN (SELECT aid FROM z{cteCount})")
    elif cteCount == 0:
        # return substr($cteSQL[0], strpos($cteSQL[0],'(')+1, -1);
        # extract the part inside the parentheses of cteSQL[0]
        first_cte = cteSQL[0]
        pos = first_cte.find('(')
        if pos == -1:
            return first_cte
        # substring from pos+1 to the end minus 1 char
        return first_cte[pos+1:-1]
    else:
        # otherwise select the matching and the GET fields
        for memeStatement in getGroup:
            select_, where_ = sql_select_where(memeStatement, table)
            selectSQL.append(select_ + " WHERE " + where_ + f" AND m0.aid IN (SELECT aid FROM z{cteCount})")

    for cteNum in cteOut:
        selectSQL.append(f"SELECT * FROM z{cteNum}" + ("" if cteNum == cteCount else f" WHERE aid IN (SELECT aid FROM z{cteCount})"))

    return 'WITH ' + ', '.join(cteSQL) + ' ' + ' UNION ALL '.join(selectSQL)


def sql_select_where(memeStatement, table=DB_TABLE_MEME, aidOnly=False):
    global OPRSTR

    wheres = []
    joins = [f"FROM {table} m0"]
    selects = ['m0.aid as aid']
    rids = ['m0.rid']
    bids = ['m0.bid']
    qnts = ['m0.qnt']
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
            selects[0] = MEME_BID_AS_AID
            if i > 0:
                # the previous is presumably A or something
                # set where[0] = 'm0.bid="previous A"'
                # We assume memeStatement[i-1] was A or something with an ID
                prevVal = memeStatement[i-1][1]
                wheres[0] = f'm0.bid="{prevVal}"'

            if exp[1] is not None:
                wheres.append(f'm0.rid="{exp[1]}"')
            rids[0] = 'CONCAT("\'", m0.rid)'
            bids[0] = 'm0.aid'

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
                joins.append(f"JOIN {table} m{m} ON {bids[-1]}=m{m}.aid")
                rids.append(f"m{m}.rid")
                bids.append(f"m{m}.bid")
                qnts.append(f"m{m}.qnt")
            elif exp[0] == MEME_BB:
                joins.append(f"JOIN {table} m{m} ON {bids[-1]}=m{m}.bid")
                rids.append(f'CONCAT("\'", m{m}.rid)')
                bids.append(f"m{m}.aid")
                qnts.append(f"(CASE WHEN m{m}.qnt = 0 THEN 0 ELSE 1 / m{m}.qnt END)")
            elif exp[0] == MEME_RA:
                joins.append(f"JOIN {table} m{m} ON m{lm}.rid=m{m}.aid")
                rids.append(f'CONCAT("?", m{m}.rid)')
                bids.append(f"m{m}.bid")
                qnts.append(f"m{m}.qnt")
            elif exp[0] == MEME_RB:
                joins.append(f"JOIN {table} m{m} ON m{lm}.rid=m{m}.bid")
                rids.append(f'CONCAT("\'", m{m}.rid)')
                bids.append(f"m{m}.aid")
                qnts.append(f"(CASE WHEN m{m}.qnt = 0 THEN 0 ELSE 1 / m{m}.qnt END)")
            else:
                raise Exception('Error: unknown operator')

    # last qnt condition
    wheres.append(f"m{m}.qnt{opr}{qnt}")

    if aidOnly:
        # No changes to selects if aidOnly?
        pass
    else:
        if m == 0 and '.aid' not in bids[0]:
            selects = ['*']
        elif m == 0:
            selects.append(rids[0]+' AS rid')
            selects.append(bids[0]+' AS bid')
            selects.append(qnts[0]+' AS qnt')
        else:
            selects.append('CONCAT(' + ", '	', ".join(rids) + ') AS rid')
            selects.append('CONCAT(' + ", '	', ".join(bids) + ') AS bid')
            selects.append('CONCAT(' + ", '	', ".join(qnts) + ') AS qnt')

    return [
        'SELECT ' + ', '.join(selects) + ' ' + ' '.join(joins),
        ' AND '.join(wheres)
    ]
