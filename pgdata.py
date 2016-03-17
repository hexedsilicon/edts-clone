import re

# This does not validate sector names, just ensures that it matches the 'Something AB-C d1' or 'Something AB-C d1-23' format
pg_system_regex = re.compile('^(?P<sector>[\\w\\s]+) (?P<prefix>\\w)(?P<centre>\\w)-(?P<suffix>\\w) (?P<lcode>\\w)(?P<number1>\\d+)(?:-(?P<number2>\\d+))?$')


# Actual data, should be accurate

# Hopefully-complete list of valid name fragments / phonemes
cx_raw_fragments = [
  "Th", "Eo", "Oo", "Eu", "Tr", "Sly", "Dry", "Ou",
  "Tz", "Phl", "Ae", "Sch", "Hyp", "Syst", "Ai", "Kyl",
  "Phr", "Eae", "Ph", "Fl", "Ao", "Scr", "Shr", "Fly",
  "Pl", "Fr", "Au", "Pry", "Pr", "Hyph", "Py", "Chr",
  "Phyl", "Tyr", "Bl", "Cry", "Gl", "Br", "Gr", "By",
  "Aae", "Myc", "Gyr", "Ly", "Myl", "Lych", "Myn", "Ch",
  "Myr", "Cl", "Rh", "Wh", "Pyr", "Cr", "Syn", "Str",
  "Syr", "Cy", "Wr", "Hy", "My", "Sty", "Sc", "Sph",
  "Spl", "A", "Sh", "B", "C", "D", "Sk", "Io",
  "Dr", "E", "Sl", "F", "Sm", "G", "H", "I",
  "Sp", "J", "Sq", "K", "L", "Pyth", "M", "St",
  "N", "O", "Ny", "Lyr", "P", "Sw", "Thr", "Lys",
  "Q", "R", "S", "T", "Ea", "U", "V", "W",
  "Schr", "X", "Ee", "Y", "Z", "Ei", "Oe",

  "ll", "ss", "b", "c", "d", "f", "dg", "g", "ng", "h", "j", "k", "l", "m", "n",
  "mb", "p", "q", "gn", "th", "r", "s", "t", "ch", "tch", "v", "w", "wh",
  "ck", "x", "y", "z", "ph", "sh", "ct", "wr", "o", "ai", "a", "oi", "ea",
  "ie", "u", "e", "ee", "oo", "ue", "i", "oa", "au", "ae", "oe", "scs",
  "wsy", "vsky", "sms", "dst", "rb", "nts", "rd", "rld", "lls", "rgh",
  "rg", "hm", "hn", "rk", "rl", "rm", "cs", "wyg", "rn", "hs", "rbs", "rp",
  "tts", "wn", "ms", "rr", "mt", "rs", "cy", "rt", "ws", "lch", "my", "ry",
  "nks", "nd", "sc", "nk", "sk", "nn", "ds", "sm", "sp", "ns", "nt", "dy",
  "st", "rrs", "xt", "nz", "sy", "xy", "rsch", "rphs", "sts", "sys", "sty",
  "tl", "tls", "rds", "nch", "rns", "ts", "wls", "rnt", "tt", "rdy", "rst",
  "pps", "tz", "sks", "ppy", "ff", "sps", "kh", "sky", "lts", "wnst", "rth",
  "ths", "fs", "pp", "ft", "ks", "pr", "ps", "pt", "fy", "rts", "ky",
  "rshch", "mly", "py", "bb", "nds", "wry", "zz", "nns", "ld", "lf",
  "gh", "lks", "sly", "lk", "rph", "ln", "bs", "rsts", "gs", "ls", "vvy",
  "lt", "rks", "qs", "rps", "gy", "wns", "lz", "nth", "phs", "io", "oea",
  "aa", "ua", "eia", "ooe", "iae", "oae", "ou", "uae", "ao", "eae", "aea",
  "ia", "eou", "aei", "uia", "aae", "eau" ]

# Sort fragments by length to ensure we check the longest ones first
cx_fragments = sorted(cx_raw_fragments, key=len, reverse=True)

# Not sure if order here is relevant
cx_prefixes = cx_raw_fragments[0:111]

#
# Sequences used in runs
#

# Vowel-ish infixes (SPECULATIVE)
c1_infixes_s1 = [
  "o", "ai", "a", "oi", "ea", "ie", "u", "e",
  "ee", "oo", "ue", "i", "oa", "au", "ae", "oe"
]

# Consonant-ish infixes (SPECULATIVE)
c1_infixes_s2 = [
  "ll", "ss", "b", "c", "d", "f", "dg", "g",
  "ng", "h", "j", "k", "l", "m", "n", "mb",
  "p", "q", "gn", "th", "r", "s", "t", "ch",
  "tch", "v", "w", "wh", "ck", "x", "y", "z",
  "ph", "sh", "ct", "wr"
]

c1_infixes = [
  None,
  c1_infixes_s1,
  c1_infixes_s2
]


# Sequence 1
cx_suffixes_s1 = [
  "oe",  "io",  "oea", "oi",  "aa",  "ua", "eia", "ae",
  "ooe", "oo",  "a",   "ue",  "ai",  "e",  "iae", "oae",
  "ou",  "uae", "i",   "ao",  "au",  "o",  "eae", "u",
  "aea", "ia",  "ie",  "eou", "aei", "ea", "uia", "oa",
  "aae", "eau", "ee"
]

# Sequence 2
cx_suffixes_s2 = [
  "b", "scs", "wsy", "c", "d", "vsky", "f", "sms",
  "dst", "g", "rb", "h", "nts", "ch", "rd", "rld",
  "k", "lls", "ck", "rgh", "l", "rg", "m", "n", 
  # Formerly sequence 4/5...
  "hm", "p", "hn", "rk", "q", "rl", "r", "rm",
  "s", "cs", "wyg", "rn", "ct", "t", "hs", "rbs",
  "rp", "tts", "v", "wn", "ms", "w", "rr", "mt",
  "x", "rs", "cy", "y", "rt", "z", "ws", "lch", # "y" is speculation
  "my", "ry", "nks"
]

# Sequence 3
cx_suffixes_s3 = [
  "nd", "sc", "ng", "sh", "nk",
  "sk", "nn", "ds", "sm", "sp", "ns",
  # Formerly sequence 4a/5
  "nt",
  "dy", "ss", "st", "rrs", "xt", "nz", "sy", "xy",
  "rsch", "rphs", "sts", "sys", "sty", "th", "tl", "tls",
  "rds", "nch", "rns", "ts", "wls", "rnt", "tt", "rdy",
  "rst", "pps", "tz", "tch", "sks", "ppy", "ff", "sps",
  "kh", "sky", "ph", "lts", 
  # Formerly sequence 4b/5
  "wnst",
  "rth", "ths", "fs", "pp", "ft", "ks", "pr", "ps",
  "pt", "fy", "rts", "ky", "rshch", "mly", "py", "bb",
  "nds", "wry", "zz", "nns", "ld", "lf", "gh", "lks",
  "sly", "lk", "ll", "rph", "ln", "bs", "rsts", "gs",
  "ls", "vvy", "lt", "rks", "qs", "rps", "gy", "wns",
  "lz", "nth", "phs"
]


cx_suffixes = [
  None,
  cx_suffixes_s1,
  cx_suffixes_s2,
  cx_suffixes_s3
]

c2_prefix_suffix_override_map = {
  "Eo":  2, "Oo": 2, "Eu": 2,
  "Ou":  2, "Ae": 2, "Ai": 2,
  "Eae": 2, "Ao": 2, "Au": 2
}

c1_prefix_infix_override_map = {
  "Eo": 2, "Oo":  2, "Eu":  2, "Ou": 2,
  "Ae": 2, "Ai":  2, "Eae": 2, "Ao": 2,
  "Au": 2, "Aae": 2, "A":   2, "Io": 2,
  "E":  2, "I":   2, "O":   2, "Ea": 2,
  "U":  2, "Ee":  2, "Ei":  2, "Oe": 2
}

c1_infix_rollover_overrides = [
  "q" # q --> gn
]


# Phoneme 1, from the "near" side of the galaxy to the far side
# Commented values are the Phoneme 3 values at Y=0
c2_positions_y0z_offset = 19
c2_positions_y0z = [
  (("Eo",  "Dry"), ("Th", "Eu")), # SPECULATION
  (("Hyp", "Ph" ), ("Th", "Eu")),
  (("Eo",  "Dry"), ("Ae", "Ai")),
  (("Hyp", "Ph" ), ("Ae", "Ai")),
  (("Pl",  "Pr" ), ("Th", "Eu")),
  (("Bl",  "By" ), ("Th", "Eu")),
  (("Pl",  "Pr" ), ("Ae", "Ai")),
  (("Bl",  "By" ), ("Ae", "Ai")),
  (("Eo",  "Dry"), ("Ao", "Au")),
  (("Hyp", "Ph" ), ("Ao", "Au")),
  (("Eo",  "Dry"), ("Ch", "Br")),
  (("Hyp", "Ph" ), ("Ch", "Br")),
  (("Pl",  "Pr" ), ("Ao", "Au")),
  (("Bl",  "By" ), ("Ao", "Au")),
  (("Pl",  "Pr" ), ("Ch", "Br")),
  (("Bl",  "By" ), ("Ch", "Br")),
  (("Ch",  "Py" ), ("Th", "Eu")),
  (("Syr", "My" ), ("Th", "Eu"))
]


c2_y_mapping_offset = 3
c2_word1_y_mapping = {
   "Eo": [("Th",1), ("Eo",0), ("Eo",0), ("Eo",1), ("Eo",1), ("Oo",0)],
  "Dry": [("Tr",1), ("Dry",0), ("Dry",0), ("Dry",1), ("Dry",1), ("Ou",0)],
  "Hyp": [("Sch",0), ("Sch",1), ("Sch", 1), ("Hyp",0), ("Hyp",0), ("Syst",0)], # Sch --> Hyp
   "Ph": [],
   "Pl": [(None,1), ("Fly",0), ("Fly",0), ("Pl",0), ("Pl",0), (None,0)],
   "Pr": [("Au",1), ("Pr",0), ("Pr",0), ("Pr",1), ("Pr",1), ("Hyph",0)],
   "Bl": [("Tyr",1), ("Bl",0), ("Bl",0), ("Bl",1), ("Bl",1), ("Cry",0)],
   "By": [("Gr",0), ("Gr",1), ("Gr",1), ("By",0), ("By",0), ("By",1)],
   "Ch": [],
   "Py": [],
  "Syr": [],
   "My": []
}

c2_word2_y_mapping = {
  "Th": [],
  "Eu": [],
  "Ae": [],
  "Ai": [("Phr",1), ("Phr",0), ("Phr",1), ("Ai",0), ("Ai",1), ("Ai",0)], # Eae --> Phr
  "Ao": [("Fly",1), ("Fly",0), ("Fly",1), ("Fl",0), ("Scr",0), ("Fl",0)], # Fl --> Ao
  "Au": [("Pr",1), ("Pr",0), ("Pr",1), ("Fr",0), ("Au",1), ("Fr",0)],
  "Ch": [],
  "Br": []
}


c2_word1_suffix_starts = {
   "Th": [None, "aae"], "Eo": ["ch", "rl"],  "Oo": ["rb", None],
   "Tr": [], "Dry": [], "Ou": [],
  "Sch": ["uae", "eau"], "Hyp": ["iae", None], "Syst": ["ua", None],
   "Ph": [],
  "Fly": ["ua", None], "Pl": ["io", None],
   "Au": [], "Pr": ["ua", "o"],
  "Tyr": [None,  "e"],    "Bl": ["aa", "au"], "Cry": ["io", None],
   "Gr": ["eia", "eae"],  "By": ["oi", "ao"],  # None
   "Ch": [],
   "Py": [],
  "Syr": [],
   "My": []
}

c2_word2_suffix_starts = {
   "Th": ["oe", "ooe"], "Eo": ["ch", "rl"], "Oo": ["rb", None],
   "Ai": ["ck", "hn"], 
   "Pr": ["ua", "e"], "Au": [],
   "Phr": ["io", "ee"],
  "Fly": ["ua", "e"], "Scr": ["oe", None],
  "Fl": ["aae", ]
}

c2_overrides = {
  "Eo": {"rn": ["Oo", "b"], "ct": ["Oo", "scs"]}
}


# C1: four prefixes per stack?
# C1: how to decide whether to increment phoneme 1 or 3?

# More checkerboards on long runs?
# Plaa Aowsy --> Plaa Scrua --> Plua Aowsy


# Index modifiers for all states
# In pairs of (phoneme 1, phoneme 3)
c2_run_states = [
  (0, 0), (1, 0), (0, 1), (1, 1),
  (2, 0), (3, 0), (2, 1), (3, 1),
  (0, 2), (1, 2), (0, 3), (1, 3),
  (2, 2), (3, 2), (2, 3), (3, 3),
  (4, 0), (5, 0), (4, 1), (5, 1),
  (6, 0), (7, 0), (6, 1), (7, 1),
  (4, 2), (5, 2), (4, 3), (5, 3),
  (6, 2), (7, 2), (6, 3), (7, 3),
  (0, 4), (1, 4), (0, 5), (1, 5),
  (2, 4), (3, 4), (2, 5), (3, 5),
  (0, 6), (1, 6), (0, 7), (1, 7),
  (2, 6), (3, 6), (2, 7), (3, 7),
  (4, 4), (5, 4), (4, 5), (5, 5),
  (6, 4), (7, 4), (6, 5), (7, 5),
  (4, 6), (5, 6), (4, 7), (5, 7),
  (6, 6), (7, 6), (6, 7), (7, 7)
]


