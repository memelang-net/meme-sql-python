import re
import html
from const import *

# Parse a Memelang query into expressions
def decode(meme_string):
	global OPRCHAR, OPRINT

	# Normalize and clean input
	meme_string = meme_string.strip()
	# Replace multiple spaces with a single space
	meme_string = ' '.join(meme_string.split())
	# Remove spaces around operators
	meme_string = re.sub(r'\s*([!<>=]+)\s*', r'\1', meme_string)
	# Convert patterns like =.5 into =0.5
	meme_string = re.sub(r'([<>=])(\-?)\.([0-9])', lambda m: f"{m.group(1)}{m.group(2)}0.{m.group(3)}", meme_string)

	if meme_string == '' or meme_string == ';':
		raise Exception("Error: Empty query provided.")

	meme_commands = []
	meme_statements = []
	meme_expressions = []

	chars = list(meme_string)
	count = len(chars)

	oprFound = {MEME_A: 0, MEME_B: 0, MEME_R: 0, MEME_EQ: 0, MEME_RA: 0}
	oprid = MEME_A
	oprgrp = MEME_A
	oprstr = ''

	i = 0
	while i < count:
		c = chars[i]
		varstr = ''

		# Semicolon separates commands
		if c == ';':
			oprid = MEME_A
			oprgrp = MEME_A
			oprFound = {MEME_A: 0, MEME_B: 0, MEME_R: 0, MEME_EQ: 0, MEME_RA: 0}
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
			oprid = MEME_A
			oprgrp = MEME_A
			oprFound = {MEME_A: 0, MEME_B: 0, MEME_R: 0, MEME_EQ: 0, MEME_RA: 0}
			if meme_expressions:
				meme_statements.append(meme_expressions)
				meme_expressions = []
			i += 1
			continue

		# Comment: skip until newline
		elif c == '/' and i+1 < count and chars[i+1] == '/':
			i += 2
			while i < count and chars[i] != '\n':
				i += 1
			i += 1
			continue

		# [xx] operator
		elif c == '[':
			if i+3 >= count:
				raise Exception(f"Erroneous bracket at char {i} in {meme_string}")

			oprstr = meme_string[i:i+4]
			if oprstr not in OPRINT:
				raise Exception(f"Operator {oprstr} not recognized at char {i} in {meme_string}")

			oprid = OPRINT[oprstr]
			oprgrp = oprid
			i += 4

		# Operators
		elif c in OPRINT:
			# previous operator checks
			if oprid == MEME_R:
				meme_expressions.append([MEME_BA, None])
			elif oprid == MEME_RI:
				meme_expressions.append([(MEME_BB if oprFound[MEME_R] > 1 else MEME_RI), None])

			oprstr = ''
			j = 0
			while j < 3 and (i+j) < count:
				cc = chars[i+j]
				if cc in OPRINT and (j == 0 or OPRCHAR.get(cc) == 2):
					oprstr += cc
					j += 1
				else:
					break

			if oprstr not in OPRINT:
				raise Exception(f"Operator {oprstr} not recognized at char {i} in {meme_string}")

			oprid = OPRINT[oprstr]

			# Determine operator group
			if oprid <= MEME_B:
				oprgrp = oprid
			elif oprid <= MEME_R:
				oprgrp = MEME_R
			elif oprid <= MEME_LSE:
				oprgrp = MEME_EQ
			else:
				oprgrp = MEME_RA

			oprFound[oprgrp] += 1

			# error checks
			if oprgrp == MEME_R and oprFound[MEME_B] > 0:
				raise Exception(f"Errant R after B at char {i} in {meme_string}")

			if oprgrp == MEME_EQ and oprFound[MEME_EQ] > 1:
				raise Exception(f"Extraneous equality operator at char {i} in {meme_string}")

			i += j+1
			continue

		# Words (A-Z identifiers)
		elif c.isalpha():
			while i < count and re.match(r'[a-zA-Z0-9_]', chars[i]):
				varstr += chars[i]
				i += 1

			if oprid == MEME_EQ:
				# handle =t, =f, =g, =tn
				if varstr == 't':
					meme_expressions.append([MEME_EQ, MEME_TRUE])
				elif varstr == 'f':
					meme_expressions.append([MEME_EQ, MEME_FALSE])
				elif varstr == 'g':
					meme_expressions.append([MEME_EQ, MEME_GET])
				else:
					tm = re.match(r't(\d+)$', varstr)
					if tm:
						meme_expressions.append([MEME_EQ, MEME_TRUE])
						meme_expressions.append([MEME_ORG, int(tm.group(1))])
					else:
						raise Exception(f"Unrecognized =Q at char {i} in {meme_string}")

			elif oprid == MEME_R and oprFound[MEME_R] > 1:
				meme_expressions.append([MEME_BA, varstr])

			elif oprid == MEME_RI and oprFound[MEME_R] > 1:
				meme_expressions.append([MEME_BB, varstr])

			else:
				meme_expressions.append([oprid, varstr])

			oprid = 0
			oprgrp = 0
			continue

		# Numbers (integers or decimals)
		elif c.isdigit() or c == '-':
			while i < count and re.match(r'[0-9.\-]', chars[i]):
				varstr += chars[i]
				i += 1

			# Validate number
			try:
				float_val = float(varstr)
			except ValueError:
				raise Exception(f"Malformed number {varstr} at char {i} in {meme_string}")

			if oprid == MEME_EQ:
				oprid = MEME_DEQ
			meme_expressions.append([oprid, float_val])
			oprid = 0
			continue

		# Unexpected character
		else:
			raise Exception(f"Unexpected character '{chars[i]}' at char {i} in {meme_string}")

	# Finalize parsing
	if oprid == MEME_RI:
		meme_expressions.append([(MEME_BB if oprFound[MEME_R] > 1 else MEME_RI), None])
	if oprid == MEME_R and oprFound[MEME_R] > 1:
		meme_expressions.append([MEME_BA, None])

	if meme_expressions:
		meme_statements.append(meme_expressions)
	if meme_statements:
		meme_commands.append(meme_statements)

	return meme_commands


def encode(meme_commands, set_=None):
	if set_ is None:
		set_ = {}

	global OPRSTR, OPRSHORT
	# OPRSTR and OPRSHORT should be defined globally

	command_array = []

	for i, meme_statements in enumerate(meme_commands):
		statement_array = []

		for statement in meme_statements:
			encoded_statement = ''

			for exp in statement:
				# exp is expected to be something like [operator, operand]
				operator = exp[0]
				operand = exp[1]

				# Determine the operator string
				if operator == MEME_A:
					oprstr = ''
				elif operator == MEME_EQ:
					oprstr = '='
					if operand == MEME_FALSE:
						operand = 'f'
					elif operand == MEME_TRUE:
						operand = 't'
					elif operand == MEME_GET:
						operand = 'g'
				elif operator == MEME_DEQ:
					oprstr = '='
					# Ensure operand is decimal
					if '.' not in str(operand):
						operand = str(operand) + '.0'
				elif set_.get('short') and operator in OPRSHORT:
					oprstr = OPRSHORT[operator]
				else:
					oprstr = OPRSTR[operator]

				# Append the encoded expression
				if set_.get('html'):
					encoded_statement += (html.escape(oprstr) +
										  '<var class="v' + str(operator) + '">' +
										  html.escape(str(operand)) +
										  '</var>')
				else:
					encoded_statement += oprstr + str(operand)

			statement_array.append(encoded_statement)

		command_array.append(' '.join(statement_array))

	if set_.get('html'):
		return '<code class="meme">' + ';</code> <code class="meme">'.join(command_array) + '</code>'
	else:
		return '; '.join(command_array)
