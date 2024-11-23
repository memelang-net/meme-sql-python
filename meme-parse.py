# Define constants
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

xOPR = {
    '.': 1,
    ':': 1,
    '-': 1,
}

# Parse a Memelang query into expressions
def meme_decode(meme_string):
    # Parse a Memelang query string into commands, statements, and expressions.
    import re

    # Normalize and clean input
    meme_string = re.sub(r'\s+', ' ', meme_string.strip())
    meme_string = re.sub(r'\s*([\!<>=]+)\s*', r'\1', meme_string)
    meme_string = re.sub(r'([<>=])(\-?)\.([0-9])', r'\1\20.\3', meme_string)

    if not meme_string or meme_string == ';':
        raise ValueError("Error: Empty query provided.")

    meme_commands = []
    meme_statements = []
    meme_expressions = []
    chars = list(meme_string)
    count = len(chars)
    b_found = False
    oprstr = ''

    i = 0
    while i < count:
        varstr = ''

        if chars[i].isspace():  # Space separates statements
            b_found = False
            if meme_expressions:
                meme_statements.append(meme_expressions)
                meme_expressions = []
        elif chars[i] == ';':  # Semicolon separates commands
            b_found = False
            if meme_expressions:
                meme_statements.append(meme_expressions)
                meme_expressions = []
            if meme_statements:
                meme_commands.append(meme_statements)
                meme_statements = []
        elif chars[i] == '/' and i + 1 < count and chars[i + 1] == '/':  # Comments start with double slash
            while i < count and chars[i] != '\n':
                i += 1
        elif chars[i] in OPR:  # Operators
            oprstr = ''
            for j in range(4):
                if i + j < count and chars[i + j] in OPR and (j == 0 or chars[i + j] not in xOPR):
                    oprstr += chars[i + j]
                else:
                    break
            if oprstr not in OPR:
                raise ValueError(f"Operator '{oprstr}' not recognized at character {i} in {meme_string}")
            if b_found and oprstr == '.':
                raise ValueError(f"Invalid R after B at {i} in {meme_string}")
            i += len(oprstr) - 1
        elif chars[i].isalpha():  # Words (A-Z identifiers)
            while i < count and re.match(r'[a-zA-Z0-9_]', chars[i]):
                varstr += chars[i]
                i += 1
            i -= 1  # Adjust for last increment

            if oprstr == '=':  # Handle `=t`, `=f`, `=tn`
                if varstr == 't':
                    meme_expressions.append([MEME_EQ, MEME_TRUE])
                elif varstr == 'f':
                    meme_expressions.append([MEME_EQ, MEME_FALSE])
                elif re.match(r't(\d+)$', varstr):
                    meme_expressions.append([MEME_EQ, MEME_TRUE])
                    meme_expressions.append([MEME_ORG, int(varstr[1:])])
            else:  # Regular word or identifier
                meme_expressions.append([OPR.get(oprstr, MEME_A), varstr])
                if oprstr and OPR.get(oprstr) == MEME_B:
                    b_found = True
            oprstr = ''
        elif chars[i].isdigit() or chars[i] == '-':  # Numbers
            while i < count and re.match(r'[0-9.\-]', chars[i]):
                varstr += chars[i]
                i += 1
            i -= 1  # Adjust for last increment
            if oprstr == '=':
                oprstr = '#='
            meme_expressions.append([OPR[oprstr], float(varstr)])
            oprstr = ''
        else:
            raise ValueError(f"Unexpected character '{chars[i]}' at position {i} in {meme_string}")
        i += 1

    if meme_expressions:
        meme_statements.append(meme_expressions)
    if meme_statements:
        meme_commands.append(meme_statements)

    return meme_commands


def meme_encode(meme_commands, set_options=None):
    #Encode a list of commands, statements, and expressions back into a Memelang string.
    if set_options is None:
        set_options = {}

    command_array = []

    for meme_statements in meme_commands:
        statement_array = []

        for statement in meme_statements:
            encoded_statement = ''
            for exp in statement:
                oprstr = '' if exp[0] == MEME_A else rOPR[exp[0]]

                if oprstr == '=':
                    exp[1] = 'f' if exp[1] == MEME_FALSE else ('t' if exp[1] == MEME_TRUE else exp[1])
                elif oprstr == '#=':
                    oprstr = '='
                    if '.' not in str(exp[1]):
                        exp[1] = f"{exp[1]}.0"

                if set_options.get('html'):
                    encoded_statement += f"{oprstr}<var class='v{exp[0]}'>{exp[1]}</var>"
                else:
                    encoded_statement += f"{oprstr}{exp[1]}"

            statement_array.append(encoded_statement)

        command_array.append(' '.join(statement_array))

    if set_options.get('html'):
        return f"<code class='meme'>{'</code>; <code class=\'meme\'>'.join(command_array)};</code>"
    else:
        return '; '.join(command_array)
