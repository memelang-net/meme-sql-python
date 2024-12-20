import sys
import os
import memelang
import db

DB_TEST_DIR = os.path.dirname(os.path.abspath(__file__))

def query():
	if len(sys.argv)<2:
		sys.exit("\nNo query provided\n")

	try:
		meme_string = sys.argv[2]
		sql_string = memelang.str2sql(meme_string)
	except Exception as e:
		sys.exit(f"\n{e}\n")

	# Execute query
	rows = db.query(sql_string)

	# Formatting the output
	br = f"+{'-' * 21}+{'-' * 21}+{'-' * 21}+{'-' * 12}+"

	# Output data
	print(f"\nSQL: {sql_string}\n")
	print(br)
	print(f"| {'A':<19} | {'R':<19} | {'B':<19} | {'Q':>10} |")
	print(br)

	if not rows:
		print(f"| {'No matching memes':<76} |")
	else:
		for row in rows:
			print(f"| {row[0][:19]:<19} | {row[1][:19]:<19} | {row[2][:19]:<19} | {row[3]:>10} |")

	print(br+"\n")


def test_make():
	questions = question_gen()
	tsv_path = os.path.join(DB_TEST_DIR, 'test_data.tsv')
	if os.path.exists(tsv_path):
		os.remove(tsv_path)

	with open(tsv_path, 'w', encoding='utf-8') as tsv:
		for group in questions.values():
			for id_, names in group['subject'].items():
				for name in names:
					for eng_str, memelang in group['question'].items():
						eng_str = eng_str.replace('%NAME', name)
						mem_str = memelang.replace('%ID', str(id_))

						sql_str = memelang.str2sql(mem_str)
						rows = db.query(sql_str)
						result_str = memelang.row2str(rows)

						tsv.write(
							eng_str + "\t" +
							mem_str + "\t" +
							sql_str.replace("\t", " ") + "\t" +
							result_str + "\n"
						)

						print(eng_str)



def test_check():
	questions = question_gen()
	tsv_path = os.path.join(DB_TEST_DIR, 'test_data.tsv')

	with open(tsv_path, 'r', encoding='utf-8') as f:
		for line_number, line in enumerate(f, start=1):
			line = line.strip()
			if not line:
				continue

			# The TSV is expected to have at least 4 columns:
			# eng_str, mem_str, sql, row2str_result
			parts = line.split('\t')
			if len(parts) == 3:
				eng_str, mem_str, sql_str, expected_result = parts[0], parts[1], parts[2], ''

			elif len(parts) < 4:
				print(f"Line {line_number}: Not enough columns.")
				continue

			else:
				eng_str, mem_str, sql_str, expected_result = parts[0], parts[1], parts[2], parts[3]

			# Execute the memelang query again
			sql_str = memelang.str2sql(mem_str)
			rows = db.query(sql_str)
			actual_result = memelang.row2str(rows)

			# Split by ';' (remove empty if trailing semicolon)
			actual_list = [x for x in actual_result.split(';') if x]
			expected_list = [x for x in expected_result.split(';') if x]

			# Sort them
			actual_list.sort()
			expected_list.sort()

			# Compare actual_result with expected_result
			if actual_list == expected_list:
				print(f"OK {eng_str}")
			else:
				print(f"\nMISMATCH {eng_str}\n")
				print(f"Memelang: {memelang}\n")
				print(f"SQL Stored: {sql_str}\n")
				print(f"SQL Created: "+memelang.str2sql(memelang)+"\n")
				print(f"Expected:\n{expected_result}\n")
				print(f"Got:\n{actual_result}\n")
				sys.exit();


def question_gen():
	questions = {
		'president': {
			'subject': {
				'george_washington': ['George Washington', 'Washington'],
				'john_adams': ['John Adams'],
				'thomas_jefferson': ['Thomas Jefferson', 'Jefferson'],
				'james_madison': ['James Madison', 'Madison'],
				'james_monroe': ['James Monroe', 'Monroe'],
				'john_quincy_adams': ['John Quincy Adams'],
				'andrew_jackson': ['Andrew Jackson', 'Jackson'],
				'martin_van_buren': ['Martin van Buren', 'van Buren'],
				'william_harrison': ['William Harrison', 'Harrison'],
				'john_tyler': ['John Tyler', 'Tyler'],
				'james_polk': ['James Polk', 'Polk'],
				'zachary_taylor': ['Zachary Taylor', 'Taylor'],
				'millard_fillmore': ['Millard Fillmore', 'Fillmore'],
				'franklin_pierce': ['Franklin Pierce', 'Pierce'],
				'james_buchanan': ['James Buchanan', 'Buchanan'],
				'abraham_lincoln': ['Abraham Lincoln', 'Lincoln'],
				'andrew_johnson': ['Andrew Johnson', 'Johnson'],
				'ulysses_grant': ['Ulysses Grant', 'Ulysses S Grant', 'Grant'],
				'rutherford_hayes': ['Rutherford Hayes', 'Rutherford B Hayes', 'Hayes'],
				'james_garfield': ['James Garfield', 'Garfield'],
				'chester_arthur': ['Chester Arthur', 'Arthur'],
				'grover_cleveland': ['Grover Cleveland', 'Cleveland'],
				'benjamin_harrison': ['Benjamin Harrison', 'Harrison'],
				'grover_cleveland': ['Grover Cleveland', 'Cleveland'],
				'william_mckinley': ['William Mckinley', 'Mckinley'],
				'theodore_roosevelt': ['Theodore Roosevelt', 'TR'],
				'william_taft': ['William Taft', 'Taft'],
				'woodrow_wilson': ['Woodrow Wilson', 'Wilson'],
				'warren_harding': ['Warren Harding', 'Harding'],
				'calvin_coolidge': ['Calvin Coolidge', 'Coolidge'],
				'herbert_hoover': ['Herbert Hoover', 'Hoover'],
				'franklin_roosevelt': ['Franklin Roosevelt', 'Roosevelt', 'FDR'],
				'harry_truman': ['Harry Truman', 'Truman'],
				'dwight_eisenhower': ['Dwight Eisenhower', 'Eisenhower', 'Ike'],
				'john_kennedy': ['John Kennedy', 'Kennedy', 'JFK'],
				'lyndon_johnson': ['Lyndon Johnson', 'Lyndon B Johnson', 'Johnson', 'LBJ'],
				'richard_nixon': ['Richard Nixon', 'Nixon'],
				'gerald_ford': ['Gerald Ford', 'Ford'],
				'james_carter': ['James Carter', 'Jimmy Carter', 'Carter'],
				'ronald_reagan': ['Ronald Reagan', 'Reagan'],
				'george_hw_bush': ['George HW Bush', 'George H.W. Bush', 'George Bush Sr'],
				'william_clinton': ['William Clinton', 'Bill Clinton', 'Clinton'],
				'george_w_bush': ['George W Bush', 'George W. Bush', 'George Bush Jr'],
				'barack_obama': ['Barack Obama', 'Obama'],
				'donald_trump': ['Donald Trump', 'Trump'],
				'joseph_biden': ['Joseph Biden', 'Biden']
			},
			'question': {
				"%NAME": "%ID qry.all",
				"Tell me about %NAME": "%ID qry.all",
				"Who were %NAME's kids?": "%ID.child",
				"Who were %NAME's children?": "%ID.child",
				"Who was %NAME's spouse?": "%ID.spouse",
				"Who was %NAME's wife?": "%ID.spouse",
				"Which number president was %NAME?": "%ID.pres_order",
				"What were %NAME's jobs?": "%ID?profession",
				"What was %NAME's profession before becoming President?": "%ID?profession",
				"%NAME's birth": "%ID.birth.",
				"%NAME's death": "%ID.death.",
				"When did %NAME die?": "%ID.death.year:ad",
				"In what did was %NAME die?": "%ID.death.year:ad",
				"When was %NAME born?": "%ID.birth.year:ad",
				"In what year was %NAME born?": "%ID.birth.year:ad",
				"Where was %NAME born?": "%ID.birth.state",
				"In which state was %NAME born?": "%ID.birth.state",
				"When was %NAME elected?": "%ID.election.year",
				"In what year was %NAME elected?": "%ID.election.year:ad",
				"Where did %NAME attended college?": "%ID.college",
				"From where did %NAME graduate?": "%ID.college",
				"To which political party where did %NAME belong?": "%ID.party",
				"What was %NAME's party?": "%ID.party",
			}
		},

		'year': {
			'subject': {},
			'question': {
				'What happened in %NAME?': '.year:ad=%ID',
				# Duplicate key in PHP is possible, Python dict last definition wins:
				'Who was born in %NAME?': '.birth.year:ad=%ID',
				'Who was born before %NAME?': '.birth.year:ad<%ID',
				'Who was born after %NAME?': '.birth.year:ad>%ID',
				'Who was elected on %NAME?': '.elected.year:ad=%ID',
				'Who was elected before %NAME?': '.elected.year:ad<%ID',
				'Who was elected after %NAME?': '.elected.year:ad>%ID',
			}
		},

		'state': {
			'subject': {
				'new_york': ['New York', 'NY'],
				'virginia': ['Virginia', 'VA'],
				'massachusetts': ['Massachusetts', 'MA'],
				'south_carolina': ['South Carolina', 'SC'],
				'north_carolina': ['Sorth Carolina', 'NC'],  # Typo "Sorth" in original
				'new_hampshire': ['New Hampshire', 'NH'],
				'pennsylvania': ['Pennsylvania', 'PA'],
				'kentucky': ['Kentucky', 'KY'],
				'ohio': ['Ohio', 'OH'],
				'vermont': ['Vermont', 'VT'],
				'new_jersey': ['New Jersey', 'NJ'],
				'iowa': ['Iowa', 'IA'],
			},
			'question': {
				"%NAME": "%ID qry.all",
				"Tell me about %NAME": "%ID qry.all",
				"Who worked for %NAME?": ":%ID?profession",
				"Who was employed by %NAME?": ":%ID?profession",
				"Who was born in %NAME?": ".birth.state:%ID",
			}
		},
	}

	# Add years to 'year' subject
	for i in range(1800, 2001, 4):
		questions['year']['subject'][i] = [str(i), f"the year {i}", f"{i} AD"]

	return questions

if __name__ == "__main__":
	if sys.argv[1] == 'testmake' or sys.argv[1] == 'maketest':
		test_make()
	elif sys.argv[1] == 'testcheck' or sys.argv[1] == 'checktest':
		test_check()
	elif sys.argv[1] == 'query':
		query()
	else:
		sys.exit("Invalid arguments.");