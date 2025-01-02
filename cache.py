global TKEY2TID, TID2TKEY

# Global dictionary to cache trm->tid mappings

TKEY2TID = {
	'f' : 0,
	't' : 1,
	'UNK' : 2,
	'dcl' : 96,
	'qst' : 97,
	'nam' : 98,
	'key' : 99,
	'cor' : 999999
}

TID2TKEY = {
	0 : 'f',
	1 : 't',
	2 : 'UNK',
	96 : 'dcl',
	97 : 'qst',
	98 : 'nam',
	99 : 'key',
	999999 : 'cor'
}