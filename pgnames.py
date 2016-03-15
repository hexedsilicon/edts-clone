#!/usr/bin/env python

from __future__ import print_function
import argparse
import logging
import math
import re
import sys
from vector3 import Vector3

app_name = "pgnames"

log = logging.getLogger(app_name)

base_coords = Vector3(-65, -25, 215)
cube_size = 1280.0

def get_sector_coords(pos):
  x = math.floor((pos.x - base_coords.x) / cube_size)
  y = math.floor((pos.y - base_coords.y) / cube_size)
  z = math.floor((pos.z - base_coords.z) / cube_size)
  return [int(x), int(y), int(z)]

def get_sector_origin(sc):
  if isinstance(sc, Vector3):
    return get_sector_origin(get_sector_coords(sc))
  x = base_coords.x + (cube_size * sc[0])
  y = base_coords.y + (cube_size * sc[1])
  z = base_coords.z + (cube_size * sc[2])
  return Vector3(x, y, z)

# This does not validate sector names, just ensures that it matches the 'Something AB-C d1' or 'Something AB-C d1-23' format
pg_system_regex = re.compile('^(?P<sector>[\\w\\s]+) (?P<prefix>\\w)(?P<centre>\\w)-(?P<suffix>\\w) (?P<lcode>\\w)(?P<number1>\\d+)(?:-(?P<number2>\\d+))?$')
# m = pg_system_regex.match('Eodgols ZP-R b13-45')
# m.group('sector', 'number1', 'number2')


# Actual data, should be accurate

# Hopefully-complete list of valid name fragments / phonemes
cx_raw_fragments = [
"Th", "Eo", "Oo", "Eu", "Tr", "Sly", "Dry", "Ou", "Tz", "Phl",
"Ae", "Sch", "Hyp", "Syst", "Ai", "Kyl", "Phr", "Eae", "Ph",
"Fl", "Ao", "Scr", "Shr", "Fly", "Pl", "Fr", "Au", "Pry", "Pr",
"Hyph", "Py", "Chr", "Phyl", "Tyr", "Bl", "Cry", "Gl", "Br", "Gr", "By",
"Aae", "Myc", "Gyr", "Ly", "Myl", "Lych", "Myn", "Ch", "Myr", "Cl",
"Rh", "Wh", "Pyr", "Cr", "Syn", "Str", "Syr", "Cy", "Wr", "Hy", "My",
"Sty", "Sc", "Sph", "Spl", "A", "Sh", "B", "C", "D", "Sk", "Io", "Dr",
"E", "Sl", "F", "Sm", "G", "H", "I", "Sp", "J", "Sq", "K", "L", "Pyth",
"M", "St", "N", "O", "Ny", "Lyr", "P", "Sw", "Thr", "Lys", "Q", "R", "S",
"T", "Ea", "U", "V", "W", "Schr", "X", "Ee", "Y", "Z", "Ei", "Oe",

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
cx_prefixes = cx_raw_fragments[0:110]

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
  "oe",
  "io",  "oea", "oi",  "aa",  "ua", "eia", "ae",  "ooe",
  "oo",  "a",   "ue",  "ai",  "e",  "iae", "oae", "ou",
  "uae", "i",   "ao",  "au",  "o",  "eae", "u",   "aea", 
  "ia",  "ie",  "eou", "aei", "ea", "uia", "oa",  "aae", "eau", "ee"
]

# Sequence 2
cx_suffixes_s2 = [
  "b",
  "scs", "wsy", "c", "d", "vsky", "f", "sms", "dst",
  "g", "rb", "h", "nts", "ch", "rd", "rld", "k",
  "lls", "ck", "rgh", "l", "rg", "m", "n", 
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
  "sk", "nn", "ds", "sm", "sp", "ns"
]

# Sequence 4
cx_suffixes_s4 = [
  # Sequence 4a
  "nt",
  "dy", "ss", "st", "rrs", "xt", "nz", "sy", "xy",
  "rsch", "rphs", "sts", "sys", "sty", "th", "tl", "tls",
  "rds", "nch", "rns", "ts", "wls", "rnt", "tt", "rdy",
  "rst", "pps", "tz", "tch", "sks", "ppy", "ff", "sps",
  "kh", "sky", "ph", "lts", 
  # Sequence 4b
  "wnst",
  "rth", "ths", "fs", "pp", "ft", "ks", "pr", "ps",
  "pt", "fy", "rts", "ky", "rshch", "mly", "py", "bb",
  "nds", "wry", "zz", "nns", "ld", "lf", "gh", "lks",
  "sly", "lk", "ll", "rph", "ln", "bs", "rsts", "gs",
  "ls", "vvy", "lt", "rks", "qs", "rps", "gy", "wns",
  "lz", "nth", "phs"
]


c2_suffixes = [
  None,
  cx_suffixes_s1,
  cx_suffixes_s2,
  cx_suffixes_s3,
  cx_suffixes_s4
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

# TODO: Work out how C1 suffixes actually work (because it's not this)
# c1_infix_suffix_s1_override_map = {
#   "o": 3, "ai": 2, "a": 2, "oi", "ea", "ie", "u", "e",
#   "ee", "oo", "ue", "i", "oa", "au", "ae", "oe"
# }


def get_fragments(sector_name):
  input = sector_name.replace(' ', '')
  segments = []
  current_str = input
  while len(current_str) > 0:
    found = False
    for frag in cx_fragments:
      if current_str[0:len(frag)] == frag:
        segments.append(frag)
        current_str = current_str[len(frag):]
        found = True
        break
    if not found:
      break
  if len(current_str) == 0:
    return segments
  else:
    return None


def get_sector_class(sector_name):
  frags = get_fragments(sector_name)
  if frags is None:
    return None
  if frags[2] in cx_prefixes:
    return "2"
  elif len(frags) == 4:
    return "1a"
  else:
    return "1b"


def get_suffixes(prefix):
  frags = get_fragments(prefix)
  if frags is None:
    return None
  if frags[-1] in cx_prefixes:
    # Append suffix straight onto a prefix (probably C2)
    suffix_map_idx = 1
    if frags[-1] in c2_prefix_suffix_override_map:
      suffix_map_idx = c2_prefix_suffix_override_map[frags[0]]
    return c2_suffixes[suffix_map_idx]
  else:
    # TODO: Oh god C1 suffixes
    pass


#
# Other data
#

# Phoneme 1, from the "near" side of the galaxy to the far side
# Commented values are the Phoneme 3 values at Y=0
c2_positions_z_z0_index = 4
c2_positions_z_z0_subindex = 4
c2_positions_z = [
  ("Eo",  "Dry"), #("Th", "Eu")), # SPECULATION
  ("Hyp", "Ph" ), #("Th", "Eu")),
  ("Eo",  "Dry"), #("Ae", "Ai")),
  ("Hyp", "Ph" ), #("Ae", "Ai")),
  ("Pl",  "Pr" ), #("Th", "Eu")),
  ("Bl",  "By" ), #("Th", "Eu")),
  ("Pl",  "Pr" ), #("Ae", "Ai")),
  ("Bl",  "By" ), #("Ae", "Ai")),
  ("Eo",  "Dry"), #("Ao", "Au")),
  ("Hyp", "Ph" ), #("Ao", "Au")),
  ("Eo",  "Dry"), #("Ch", "Br")),
  ("Hyp", "Ph" ), #("Ch", "Br")),
  ("Pl",  "Pr" ), #("Ao", "Au")),
  ("Bl",  "By" ), #("Ao", "Au")),
  ("Pl",  "Pr" ), #("Ch", "Br")),
  ("Bl",  "By" ), #("Ch", "Br")),
  ("Ch",  "Py" ), #("Th", "Eu")),
  ("Syr", "My" )  #("Th", "Eu"))
]

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


def get_suffix_index(s):
  if s in cx_suffixes_s1:
    return 1
  if s in cx_suffixes_s2:
    return 2
  if s in cx_suffixes_s3:
    return 3
  if s in cx_suffixes_s4:
    return 4
  return None


if __name__ == '__main__':
  if len(sys.argv) >= 2:
    if sys.argv[1] == "debug":
      with open("edsm_data.txt") as f:
        names = [n.strip() for n in f.readlines()]
      
      print(len(names))
      
      prefixes = {}
      
      for n in names:
        frags = get_fragments(n)
        sc = get_sector_class(n)
        if sc != "2":
          if frags[0] not in prefixes:
            prefixes[frags[0]] = set()
          if get_suffix_index(frags[-1]) is not None:
            prefixes[frags[0]].add(frags[-1])
          else:
            print("Bad sector: {0}".format(n))
          
      print(len(prefixes))
      for p in prefixes:
        if len([l for l in prefixes[p] if get_suffix_index(l) != 1]) > 0:
          print("{0}: {1}".format(p, ", ".join([str(get_suffix_index(x)) for x in prefixes[p] if get_suffix_index(x) != 1])))
    elif sys.argv[1] == "baseline":
      baselines = {
        "Vegnao": Vector3(4300, 1000, 36650),
        "Vegnau": Vector3(5200, 1000, 36650),
        "Weqo": Vector3(6500, 1000, 36650),
        "Veqo": Vector3(-38450, 1000, 36650),
        "Vequia": Vector3(-26560, 1000, 36650),
        "Veqeau": Vector3(-22750, 1000, 36650),
        "Veqee": Vector3(-21700, 1000, 36650)
      }
      
      start = "Veqo"
      start_coords = baselines[start]
      # print("start: {0}, cube: {1} @ {2}".format(start_coords, get_sector_coords(start_coords), get_sector_origin(start_coords)))
      
      current = start
      current_coords = start_coords
      for i in range(0, int(sys.argv[1])):
        extra = ""
        if current in baselines:
          if get_sector_coords(current_coords) == get_sector_coords(baselines[current]):
            extra = " CORRECT"
          else:
            extra = " INCORRECT"
            
        print("{0} @ {1} / {2}{3}".format(current, get_sector_origin(current_coords), get_sector_coords(current_coords), extra))
        frags = get_fragments(current)
        
        suffix_idx = cx_suffixes[1].index(frags[-1])
        if suffix_idx + 1 >= len(cx_suffixes[1]):
          frags[-1] = cx_suffixes[1][0]
          done = False
          cur_frag = len(frags) - 2
          while not done:
            cur_idx = cx_infix.index(frags[cur_frag])
            if cur_idx + 1 >= len(cx_infix):
              frags[cur_frag] = cx_infix[0]
            else:
              frags[cur_frag] = cx_infix[cur_idx+1]
              done = True
        else:
          frags[-1] = cx_suffixes[1][suffix_idx+1]
        current = "".join(frags)
        current_coords.x += cube_size

    elif sys.argv[1] == "run1":
      input = sys.argv[2] # "Smooreau"
      frags = get_fragments(input)
      
      start_x = base_coords.x - (int(sys.argv[3]) * 1280)
      
      cur_idx = cx_suffixes_s1.index(frags[-1])
      
      for i in range(0, int(sys.argv[4])):
        frags[-1] = cx_suffixes_s1[cur_idx]
        print ("[{1}] {0}".format("".join(frags), start_x + (i * 1280)))
        if cur_idx + 1 == len(cx_suffixes_s1):
          cur_idx = 0
          frags[0] = cx_prefixes[cx_prefixes.index(frags[0])+1]
        else:
          cur_idx += 1
        
      
    elif sys.argv[1] == "run2":
      input = sys.argv[2] # "Schuae Flye"

      frags = get_fragments(input)

      # This should put us at -49985
      start_x = base_coords.x - (39 * 1280)
      end_x = base_coords.x + (39 * 1280)

      # The index in the valid set of suffixes we believe we're at
      base_idx_0 = 0
      base_idx_1 = 0
      # The state that we think this system is at in the run
      base_slot_0 = 0
      base_slot_1 = 0
      # Calculate the actual starting suffix index
      start_idx_0 = cx_suffixes_s1.index(frags[1]) - base_idx_0
      start_idx_1 = cx_suffixes_s1.index(frags[3]) - base_idx_1

      for i in range(0, int(sys.argv[3])):
        # Calculate the run state indexes for phonemes 1 and 3
        idx0 = (i+base_slot_0) % len(c2_run_states)
        idx1 = (i+base_slot_1) % len(c2_run_states)
        # Calculate the current base index
        # (in case we've done a full run and are onto the next set of phoneme 3s)
        cur_base_0 = start_idx_0
        cur_base_1 = start_idx_1 + int((i + base_slot_1) / len(c2_run_states)) * 8
        # print("idx0 = {0}, idx1 = {1}, cb0 = {2}, cb1 = {3}".format(idx0, idx1, cur_base_0, cur_base_1))
        # print("slots[{0}] = {1}, slots[{2}] = {3}".format(idx0, slots[idx0][0], idx1, slots[idx1][1]))
        frags[1] = cx_suffixes_s1[(cur_base_0 + c2_run_states[idx0][0]) % len(cx_suffixes_s1)]
        frags[3] = cx_suffixes_s1[(cur_base_1 + c2_run_states[idx1][1]) % len(cx_suffixes_s1)]
        print ("[{4}/{5},{6}/{7},{8}] {0}{1} {2}{3}".format(frags[0], frags[1], frags[2], frags[3], start_x + (i * 1280), idx0, idx1, cur_base_0, cur_base_1))
        