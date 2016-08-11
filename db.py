import decimal
import json
import logging
import math
import os
import re
import sqlite3
import time

log = logging.getLogger("db")

default_db_file = os.path.normpath('data/edts.db')
schema_version = 6

FIND_EXACT = 0
FIND_GLOB = 1
FIND_REGEX = 2

_find_operators = ['=','LIKE','REGEXP']
# This is nasty, and it may well not be used up in the main code
_bad_char_regex = re.compile("[^a-zA-Z0-9'&+:*^%_?.,/#@!=`() -]")


def _regexp(expr, item):
  rgx = re.compile(expr)
  return rgx.search(item) is not None


def _vec3_len(x1, y1, z1, x2, y2, z2):
  xdiff = (x2-x1)
  ydiff = (y2-y1)
  zdiff = (z2-z1)
  return math.sqrt(xdiff*xdiff + ydiff*ydiff + zdiff*zdiff)


def open_db(filename = default_db_file, check_version = True):
  conn = sqlite3.connect(filename)
  conn.row_factory = sqlite3.Row
  conn.create_function("REGEXP", 2, _regexp)
  conn.create_function("vec3_len", 6, _vec3_len)
 
  if check_version:
    c = conn.cursor()
    c.execute('SELECT db_version FROM edts_info')
    (db_version, ) = c.fetchone()
    if db_version != schema_version:
      log.warning("DB file's schema version {0} does not match the expected version {1}.".format(db_version, schema_version))
      log.warning("This is likely to cause errors; you may wish to rebuild the database by running update.py")
    log.debug("DB connection opened")
  return DBConnection(conn)


def initialise_db(filename = default_db_file):
  dbc = open_db(filename, check_version=False)
  dbc._create_tables()
  return dbc


class DBConnection(object):
  def __init__(self, conn):
    self._conn = conn

  def close(self):
    self._conn.close()
    log.debug("DB connection closed")

  def _create_tables(self):
    log.debug("Creating tables...")
    c = self._conn.cursor()
    c.execute('CREATE TABLE edts_info (db_version INTEGER, db_mtime INTEGER)')
    c.execute('INSERT INTO edts_info VALUES (?, ?)', (schema_version, int(time.time())))

    c.execute('CREATE TABLE systems (edsm_id INTEGER, eddb_id INTEGER, name TEXT COLLATE NOCASE, pos_x REAL, pos_y REAL, pos_z REAL, needs_permit BOOLEAN, allegiance TEXT, data TEXT)')
    c.execute('CREATE TABLE stations (eddb_id INTEGER, eddb_system_id INTEGER, name TEXT COLLATE NOCASE, sc_distance INTEGER, station_type TEXT, max_pad_size TEXT, data TEXT)')
    c.execute('CREATE TABLE coriolis_fsds (id TEXT, data TEXT)')

    c.execute('CREATE INDEX idx_systems_name ON systems (name COLLATE NOCASE)')
    c.execute('CREATE INDEX idx_systems_pos ON systems (pos_x, pos_y, pos_z)')
    c.execute('CREATE INDEX idx_systems_edsm_id ON systems (edsm_id)')
    c.execute('CREATE INDEX idx_systems_eddb_id ON systems (eddb_id)')
    c.execute('CREATE INDEX idx_stations_name ON stations (name COLLATE NOCASE)')
    c.execute('CREATE INDEX idx_stations_sysid ON stations (eddb_system_id)')

    self._conn.commit()
    log.debug("Done.")

  def populate_table_systems(self, many):
    c = self._conn.cursor()
    log.debug("Going for INSERT INTO systems...")
    c.executemany('INSERT INTO systems VALUES (?, NULL, ?, ?, ?, ?, NULL, NULL, NULL)', many)
    self._conn.commit()
    log.debug("Done, {} rows inserted.".format(c.rowcount))

  def update_table_systems(self, many):
    c = self._conn.cursor()
    log.debug("Going for UPDATE systems...")
    c.executemany('UPDATE systems SET eddb_id=?, needs_permit=?, allegiance=?, data=? WHERE edsm_id=? AND eddb_id IS NULL', many)
    self._conn.commit()
    log.debug("Done, {} rows affected.".format(c.rowcount))

  def populate_table_stations(self, many):
    c = self._conn.cursor()
    log.debug("Going for INSERT INTO stations...")
    c.executemany('INSERT INTO stations VALUES (?, ?, ?, ?, ?, ?, ?)', many)
    self._conn.commit()
    log.debug("Done, {} rows inserted.".format(c.rowcount))

  def populate_table_coriolis_fsds(self, many):
    log.debug("Going for INSERT INTO coriolis_fsds...")
    c = self._conn.cursor()
    c.executemany('INSERT INTO coriolis_fsds VALUES (?, ?)', many)
    self._conn.commit()
    log.debug("Done, {} rows inserted.".format(c.rowcount))

  def retrieve_fsd_list(self):
    c = self._conn.cursor()
    cmd = 'SELECT id, data FROM coriolis_fsds'
    log.debug("Executing: {}".format(cmd))
    c.execute(cmd)
    results = c.fetchall()
    log.debug("Done.")
    return dict([(k, json.loads(v)) for (k, v) in results])

  def get_system_by_name(self, name):
    c = self._conn.cursor()
    cmd = 'SELECT name, pos_x, pos_y, pos_z, data FROM systems WHERE name = ?'
    log.debug("Executing: {}; name = {}".format(cmd, name))
    c.execute(cmd, (name, ))
    result = c.fetchone()
    log.debug("Done.")
    if result != None:
      return _process_system_result(result)
    else:
      return None

  def get_station_by_names(self, sysname, stnname):
    c = self._conn.cursor()
    cmd = 'SELECT sy.name AS name, sy.pos_x AS pos_x, sy.pos_y AS pos_y, sy.pos_z AS pos_z, sy.data AS data, st.data AS stndata FROM systems sy, stations st WHERE sy.name = ? AND st.name = ? AND sy.eddb_id = st.eddb_system_id'
    log.debug("Executing: {}; sysname = {}, stnname = {}".format(cmd, sysname, stnname))
    c.execute(cmd, (sysname, stnname))
    result = c.fetchone()
    log.debug("Done.")
    if result != None:
      return (_process_system_result(result), json.loads(result['stndata']))
    else:
      return (None, None)

  def get_stations_by_system_id(self, sysid):
    c = self._conn.cursor()
    cmd = 'SELECT data FROM stations WHERE eddb_system_id = ?'
    log.debug("Executing: {}; sysid = {}".format(cmd, sysid))
    c.execute(cmd, (sysid, ))
    results = c.fetchall()
    log.debug("Done.")
    return [json.loads(r[0]) for r in results]

  def get_systems_by_aabb(self, min_x, min_y, min_z, max_x, max_y, max_z):
    c = self._conn.cursor()
    cmd = 'SELECT name, pos_x, pos_y, pos_z, data FROM systems WHERE ? <= pos_x AND pos_x < ? AND ? <= pos_y AND pos_y < ? AND ? <= pos_z AND pos_z < ?'
    log.debug("Executing: {}; min_x = {}, max_x = {}, min_y = {}, max_y = {}, min_z = {}, max_z = {}".format(cmd, min_x, max_x, min_y, max_y, min_z, max_z))
    c.execute(cmd, (min_x, max_x, min_y, max_y, min_z, max_z))
    results = c.fetchall()
    log.debug("Done.")
    return [_process_system_result(r) for r in results]

  def find_systems_close_to(self, refs):
    c = self._conn.cursor()
    params = []
    select = ["other.name, other.pos_x, other.pos_y, other.pos_z, other.data"]
    tables = ["systems other"]
    where = []
    debug = []
    debug_params = []
    idx = 1
    for ref in refs:
      name, min_dist, max_dist = ref
      select.append("(((ref{0}.pos_x - other.pos_x) * (ref{0}.pos_x - other.pos_x)) + ((ref{0}.pos_y - other.pos_y) * (ref{0}.pos_y - other.pos_y)) + ((ref{0}.pos_z - other.pos_z) * (ref{0}.pos_z - other.pos_z))) as diff{0}".format(idx))
      tables.append("systems ref{0}".format(idx))
      clause = "ref{0}.name = ? AND other.edsm_id != ref{0}.edsm_id".format(idx)
      params.append(name)
      debug_clause = "name{0} = {1}".format(idx, '{}')
      debug_params.append(name)
      if min_dist is not None:
        clause += " AND diff{0} >= ? * ?".format(idx)
        params += [min_dist, min_dist]
        debug_clause += ", min_dist{0} = {1}".format(idx, '{}')
        debug_params.append(min_dist)
      if max_dist is not None:
        clause += " AND diff{0} <= ? * ?".format(idx)
        params += [max_dist, max_dist]
        debug_clause += ", max_dist{0} = {1}".format(idx, '{}')
        debug_params.append(max_dist)
      where.append(clause)
      debug.append(debug_clause)
      idx += 1
    cmd = "SELECT {0} FROM {1} WHERE {2}".format(', '.join(select), ', '.join(tables), ' AND '.join(where))
    log.debug("Executing: {}; {}".format(cmd, ', '.join(debug).format(*debug_params)))

    c.execute(cmd, params)
    results = c.fetchall()
    log.debug("Done")
    return [_process_system_result(r) for r in results]

    
  def find_systems_by_name(self, name, mode=FIND_EXACT):
    if mode == FIND_GLOB and _find_operators[mode] == 'LIKE':
      name = name.replace('*','%').replace('?','_')
    c = self._conn.cursor()
    cmd = 'SELECT name, pos_x, pos_y, pos_z, data FROM systems WHERE name {0} ?'.format(_find_operators[mode])
    log.debug("Executing: {}; name = {}".format(cmd, name))
    c.execute(cmd, (name, ))
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield _process_system_result(result)
      result = c.fetchone()

  def find_stations_by_name(self, name, mode=FIND_EXACT):
    if mode == FIND_GLOB and _find_operators[mode] == 'LIKE':
      name = name.replace('*','%').replace('?','_')
    c = self._conn.cursor()
    cmd = 'SELECT sy.name AS name, sy.pos_x AS pos_x, sy.pos_y AS pos_y, sy.pos_z AS pos_z, sy.data AS data, st.data AS stndata FROM systems sy, stations st WHERE st.name {0} ? AND sy.eddb_id = st.eddb_system_id'.format(_find_operators[mode])
    log.debug("Executing: {}; name = {}".format(cmd, name))
    c.execute(cmd, (name, ))
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield (_process_system_result(result), json.loads(result['stndata']))
      result = c.fetchone()
  
  # WARNING: VERY UNSAFE, USE WITH CARE
  # These methods exist due to a bug in the Python sqlite3 module
  # Using bound parameters as the safe versions do results in indexes being ignored
  # This significantly slows down searches (~500x at time of writing) due to doing full table scans
  # So, these methods are fast but vulnerable to SQL injection due to use of string literals
  # This will hopefully be unnecessary in Python 2.7.11+ / 3.6.0+ if porting of a newer pysqlite2 version is completed
  def find_systems_by_name_unsafe(self, name, mode=FIND_EXACT):
    if mode == FIND_GLOB and _find_operators[mode] == 'LIKE':
      name = name.replace('*','%').replace('?','_')
    name = _bad_char_regex.sub("", name)
    name = name.replace("'", r"''")
    c = self._conn.cursor()
    cmd = "SELECT name, pos_x, pos_y, pos_z, data FROM systems WHERE name {0} '{1}'".format(_find_operators[mode], name)
    log.debug("Executing (U): {}".format(cmd))
    c.execute(cmd)
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield _process_system_result(result)
      result = c.fetchone()

  def find_stations_by_name_unsafe(self, name, mode=FIND_EXACT):
    if mode == FIND_GLOB and _find_operators[mode] == 'LIKE':
      name = name.replace('*','%').replace('?','_')
    name = _bad_char_regex.sub("", name)
    name = name.replace("'", r"''")
    c = self._conn.cursor()
    cmd = "SELECT sy.name AS name, sy.pos_x AS pos_x, sy.pos_y AS pos_y, sy.pos_z AS pos_z, sy.data AS data, st.data AS stndata FROM systems sy, stations st WHERE st.name {0} '{1}' AND sy.eddb_id = st.eddb_system_id".format(_find_operators[mode], name)
    log.debug("Executing (U): {}".format(cmd))
    c.execute(cmd)
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield (_process_system_result(result), json.loads(result['stndata']))
      result = c.fetchone()

  # Slow as sin; avoid if at all possible
  def get_all_systems(self):
    c = self._conn.cursor()
    cmd = 'SELECT name, pos_x, pos_y, pos_z, data FROM systems'
    log.debug("Executing: {}".format(cmd))
    c.execute(cmd)
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield _process_system_result(result)
      result = c.fetchone()

  # Slow as sin; avoid if at all possible
  def get_all_stations(self):
    c = self._conn.cursor()
    cmd = 'SELECT sy.name AS name, sy.pos_x AS pos_x, sy.pos_y AS pos_y, sy.pos_z AS pos_z, sy.data AS data, st.data AS stndata FROM stations st, systems sy WHERE st.eddb_system_id = sy.eddb_id'
    log.debug("Executing: {}".format(cmd))
    c.execute(cmd)
    result = c.fetchone()
    log.debug("Done.")
    while result is not None:
      yield (_process_system_result(result), json.loads(result['stndata']))
      result = c.fetchone()


def _process_system_result(result):
  if result['data'] is not None:
    return json.loads(result['data'])
  else:
    return {'name': result['name'], 'x': result['pos_x'], 'y': result['pos_y'], 'z': result['pos_z']}
