
COL_AID = 0
COL_RID = 1
COL_BID = 2
COL_QNT = 3

MEME_FALSE = 0
MEME_TRUE = 1
MEME_UNK = 2
MEME_A = 3
MEME_B = 4
MEME_RI = 5
MEME_R = 6
MEME_EQ = 8
MEME_DEQ = 9
MEME_NEQ = 10
MEME_GRT = 11
MEME_GRE = 12
MEME_LST = 13
MEME_LSE = 14
MEME_BA = 33
MEME_BB = 34
MEME_RA = 35
MEME_RB = 36
MEME_GET = 40
MEME_ORG = 41
MEME_TERM = 99

# Global variables
OPRINT = {
	"@": MEME_A,
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

OPRSTR = {v: k for k, v in OPRINT.items()}

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

OPRSHORT = {
	MEME_BA: ".",
	MEME_BB: "'",
	MEME_RA: "?",
	MEME_RB: "?'",
}