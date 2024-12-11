import re
from const import *

# Parse a Memelang query into expressions
def decode(meme_string):

	meme_string = re.sub(r'\s+', ' ', meme_string.strip())
	meme_string = re.sub(r'\s*([!<>=]+)\s*', r'\1', meme_string)
	meme_string = re.sub(r'([<>=])(\-?)\.(\d)', r'\1\2' + '\0.' + r'\3', meme_string)


	if meme_string == '' or meme_string == ';':
		raise ValueError("Error: Empty query provided.")

	meme_commands = []
	meme_statements = []
	meme_expressions = []
	chars = list(meme_string)
	count = len(chars)
	opr_found = {MEME_A: 0, MEME_B: 0, MEME_R: 0, MEME_EQ: 0, MEME_RA: 0}
	oprid = MEME_A
	oprgrp = MEME_A

	i = 0
	while i < count:
		varstr = ''
		if chars[i] == ';':
			oprid = MEME_A
			oprgrp = MEME_A
			opr_found = {MEME_A: 0, MEME_B: 0, MEME_R: 0, MEME_EQ: 0, MEME_RA: 0}
			if meme_expressions:
				meme_statements.append(meme_expressions)
				meme_expressions = []
			if meme_statements:
				meme_commands.append(meme_statements)
				meme_statements = []
		elif chars[i].isspace():
			oprid = MEME_A
			oprgrp = MEME_A
			opr_found = {MEME_A: 0, MEME_B: 0, MEME_R: 0, MEME_EQ: 0, MEME_RA: 0}
			if meme_expressions:
				meme_statements.append(meme_expressions)
				meme_expressions = []
		elif chars[i] == '/' and i + 1 < count and chars[i + 1] == '/':
			while i < count and chars[i] != "\n":
				i += 1
		elif chars[i] == '[':
			oprstr = ''.join(chars[i:i+4])
			oprid = OPRINT.get(oprstr)
			if oprid is None:
				raise ValueError(f"Operator {oprstr} not recognized at char {i} in {meme_string}")

			oprgrp = oprid
			i += 3 if chars[i] == '.' else 4
		elif chars[i] in OPRINT:
			oprstr = ''
			for j in range(3):
				if i + j < count and chars[i + j] in OPRINT and (j == 0 or OPRCHAR[chars[i + j]] == 2):
					oprstr += chars[i + j]
				else:
					break

			oprid = OPRINT.get(oprstr)
			if oprid is None:
				raise ValueError(f"Operator {oprstr} not recognized at char {i} in {meme_string}")

			oprgrp = (MEME_A if oprid <= MEME_B else
					  MEME_R if oprid <= MEME_R else
					  MEME_EQ if oprid <= MEME_LSE else
					  MEME_RA)

			opr_found[oprgrp] += 1
			i += len(oprstr) - 1
		elif chars[i].isalpha():
			while i < count and re.match(r'[a-zA-Z0-9_]', chars[i]):
				varstr += chars[i]
				i += 1

			if oprid == MEME_EQ:
				if varstr == 't':
					meme_expressions.append((MEME_EQ, MEME_TRUE))
				elif varstr == 'f':
					meme_expressions.append((MEME_EQ, MEME_FALSE))
				elif varstr == 'g':
					meme_expressions.append((MEME_EQ, MEME_GET))
				else:
					raise ValueError(f"Unrecognized =Q at char {i} in {meme_string}")
			else:
				meme_expressions.append((oprid, varstr))
			oprid = 0
		elif chars[i].isdigit() or chars[i] == '-':
			while i < count and re.match(r'[0-9.\-]', chars[i]):
				varstr += chars[i]
				i += 1
			if not re.match(r'^-?\d*(\.\d+)?$', varstr):
				raise ValueError(f"Malformed number {varstr} at char {i} in {meme_string}")
			meme_expressions.append((oprid, float(varstr)))
			oprid = 0
		else:
			raise ValueError(f"Unexpected character '{chars[i]}' at char {i} in {meme_string}")
		i += 1

	if meme_expressions:
		meme_statements.append(meme_expressions)
	if meme_statements:
		meme_commands.append(meme_statements)

	return meme_commands




def encode(meme_commands, settings=None):
	settings = settings or {}
	command_array = []

	for meme_statements in meme_commands:
		statement_array = []

		for statement in meme_statements:
			encoded_statement = ''
			for exp in statement:
				oprstr = OPRSTR.get(exp[0], '')

				if exp[0] == MEME_EQ:
					if exp[1] == MEME_TRUE:
						exp = (MEME_EQ, 't')
					elif exp[1] == MEME_FALSE:
						exp = (MEME_EQ, 'f')
					elif exp[1] == MEME_GET:
						exp = (MEME_EQ, 'g')

				elif exp[0] == MEME_DEQ and '.' not in str(exp[1]):
					exp = (MEME_DEQ, f"{exp[1]}.0")

				encoded_statement += f"{oprstr}{exp[1]}"

			statement_array.append(encoded_statement)

		command_array.append(' '.join(statement_array))

	return ' '.join(command_array)
