import re
from meme_parse import meme_decode

# Constants
MEME_FALSE = 0
MEME_TRUE = 1
MEME_A = 2
MEME_RI = 3
MEME_R = 4
MEME_B = 5
MEME_EQ = 6
MEME_DEQ = 16
MEME_GET = 40
MEME_ORG = 41

# Operators mappings
OPR = {
    '@': MEME_A,
    '.': MEME_R,
    '\'': MEME_RI,
    ':': MEME_B,
    '=': MEME_EQ,
    # '==' : 8,
    '=>': 9,
    '!=': 10,
    # '!==' : 11,
    '>': 12,
    '>=': 13,
    '<': 14,
    '<=': 15,
    '#=': MEME_DEQ,
}
rOPR = {v: k for k, v in OPR.items()}

# Database table
DB_TABLE_MEME = "meme"

# Main function to process Memelang query and return results
def meme_query(meme_string):
    try:
        sql_query = meme_sql(meme_string)
        return execute_db_query(sql_query)
    except Exception as e:
        return f"Error: {str(e)}"

# Translate a Memelang query (which may contain multiple commands) into SQL
def meme_sql(meme_string):
    queries = []
    meme_commands = meme_decode(meme_string)
    for meme_command in meme_commands:
        queries.append(meme_cmd_sql(meme_command))
    sql = " UNION ".join(queries)

    # Consolidate subqueries into CTE
    if "m.*" not in sql or not re.findall(r'bid IN \((.*?)\)', sql):
        return sql

    matches = list(set(re.findall(r'bid IN \((.*?)\)', sql)))
    with_cte = "WITH " + ", ".join([f"sq{i} AS ({subquery})" for i, subquery in enumerate(matches)])
    for i, subquery in enumerate(matches):
        sql = sql.replace(subquery, f"SELECT aid FROM sq{i}")

    return f"{with_cte} {sql}"

# Translate one Memelang command into SQL
def meme_cmd_sql(meme_command):
    true_group = []
    false_group = []
    filter_group = []
    or_groups = {}
    query_settings = {"all": False}

    for meme_statement in meme_command:
        if meme_statement[0][0] == MEME_A and meme_statement[0][1] == "qry":
            query_settings[meme_statement[1][1]] = True
            continue

        last_exp = meme_statement[-1] if meme_statement else None
        if not last_exp:
            continue

        if last_exp[0] == MEME_EQ:
            if last_exp[1] == MEME_FALSE:
                false_group.append(meme_statement[:-1])
                continue
            if last_exp[1] == MEME_GET:
                filter_group.append(meme_statement[:-1])
                continue

        # Group =tn into OR groups
        if last_exp[0] == MEME_ORG:
            or_groups.setdefault(last_exp[1], []).append(meme_statement[:-1])
            filter_group.append(meme_statement[:-1])
            continue

        # Default: Add to true conditions
        true_group.append(meme_statement)
        filter_group.append(meme_statement)

    # Get all
    if query_settings["all"] and not true_group and not false_group and not or_groups:
        return f"SELECT * FROM {DB_TABLE_MEME}"

    # Simple query
    if (
        len(true_group) == 1
        and not false_group
        and not or_groups
        and len(filter_group) == 1
        and not query_settings["all"]
    ):
        return f"SELECT * FROM {DB_TABLE_MEME} WHERE {meme_where(true_group[0])}"

    # Clear filters if qry.all is present
    if query_settings["all"]:
        filter_group = []

    # Generate SQL query for complex cases
    having_sql = []

    # Process AND conditions
    for meme_statement in true_group:
        having_sql.append(f"SUM(CASE WHEN ({meme_where(meme_statement)}) THEN 1 ELSE 0 END) > 0")

    # Process grouped OR conditions
    for or_group in or_groups.values():
        or_sql = [f"({meme_where(or_state)})" for or_state in or_group]
        having_sql.append(f"SUM(CASE WHEN ({' OR '.join(or_sql)}) THEN 1 ELSE 0 END) > 0")

    # Process NOT conditions
    for meme_statement in false_group:
        having_sql.append(f"SUM(CASE WHEN ({meme_where(meme_statement)}) THEN 1 ELSE 0 END) = 0")

    # Process GET filters
    filter_sql = []
    where_sql = ""
    if filter_group:
        filter_sql = [f"({meme_where(statement, False)})" for statement in filter_group]
        where_sql = f" WHERE {' OR '.join(meme_filter_group(filter_sql))}"

    return f"SELECT m.* FROM {DB_TABLE_MEME} m JOIN (SELECT aid FROM {DB_TABLE_MEME} GROUP BY aid HAVING {' AND '.join(having_sql)}) AS aids ON m.aid = aids.aid{where_sql}"

# Translate an $memeStatement array of ARBQ into an SQL WHERE clause
def meme_where(meme_statement, use_qnt=True):
    conditions = []
    rids = []
    aid = None
    bid = None
    opr = "!="
    qnt = 0
    rid_nest = ""

    for exp in meme_statement:
        if exp[0] == MEME_A:
            aid = exp[1]
        elif exp[0] == MEME_R:
            rids.append(exp[1])
        elif exp[0] == MEME_B:
            bid = exp[1]
        elif use_qnt and exp[0] in rOPR:
            opr = "=" if exp[0] == MEME_DEQ else rOPR[exp[0]]
            qnt = exp[1]

    if len(rids) > 1:
        for i in range(1, len(rids)):
            if i > 1:
                rid_nest += " AND "
            rid_nest += f"bid IN (SELECT aid FROM {DB_TABLE_MEME} WHERE rid='{rids[i]}'"
            if i == len(rids) - 1:
                if bid:
                    rid_nest += f" AND bid='{bid}'"
                rid_nest += f" AND qnt{opr}{qnt})"

        bid = None
        use_qnt = None

    if aid:
        conditions.append(f"aid='{aid}'")
    if rids:
        conditions.append(f"rid='{rids[0]}'")
    if bid:
        conditions.append(f"bid='{bid}'")
    if use_qnt:
        conditions.append(f"qnt{opr}{qnt}")
    if rid_nest:
        conditions.append(rid_nest)

    return " AND ".join(conditions)

# Group filters to reduce SQL complexity
def meme_filter_group(filters):
    rid_values = []
    bid_values = []
    mixed_values = []

    for filter_ in filters:
        if re.match(r"^\(rid='[A-Za-z0-9_]+'\)$", filter_):
            rid_values.append(re.findall(r"rid='([A-Za-z0-9_]+)'", filter_)[0])
        elif re.match(r"^\(bid='[A-Za-z0-9_]+'\)$", filter_):
            bid_values.append(re.findall(r"bid='([A-Za-z0-9_]+)'", filter_)[0])
        else:
            mixed_values.append(filter_)

    grouped = []
    if rid_values:
        grouped.append(f"m.rid IN ('{'', ''.join(set(rid_values))}')")
    if bid_values:
        grouped.append(f"m.bid IN ('{'', ''.join(set(bid_values))}')")

    return grouped + mixed_values

# Tokenize DB output
def meme_db_decode(meme_triples):
    meme_commands = []
    for row in meme_triples:
        if row["qnt"] == 1:
            opr = MEME_EQ
            qnt = MEME_TRUE
        elif row["qnt"] == 0:
            opr = MEME_EQ
            qnt = MEME_FALSE
        else:
            opr = MEME_DEQ
            qnt = float(row["qnt"])

        meme_commands.append([[
            [MEME_A, row["aid"]],
            [MEME_R, row["rid"]],
            [MEME_B, row["bid"]],
            [opr, qnt]
        ]])
    return meme_commands

# Output DB data
def meme_db_out(meme_triples, set_options=None):
    print(meme_encode(meme_db_decode(meme_triples), set_options))
