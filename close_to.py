import argparse
import env
import logging
import math
import sys
from vector3 import Vector3

app_name = "close_to"

log = logging.getLogger(app_name)

class ApplicationAction(argparse.Action):
  def __call__(self, parser, namespace, value, option_strings=None):
    n = vars(namespace)
    system_list = n['system'] if n['system'] is not None else []
    need_new = True
    i = 0
    while i < len(system_list):
      if self.dest not in system_list[i]:
        need_new = False
        break
      i += 1
    if need_new:
      system_list.append({})
    d = system_list[i]
    if self.dest == 'system':
      d['system'] = value[0]
    else:
      d[self.dest] = value
      setattr(namespace, self.dest, value)
    setattr(namespace, 'system', system_list)


class Application:

  def __init__(self, arg, hosted):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Find Nearby Systems", fromfile_prefix_chars="@", parents = ap_parents, prog = app_name)
    ap.add_argument("-n", "--num", type=int, required=False, default=10, help="Show the specified number of nearby systems")
    ap.add_argument("-d", "--min-dist", type=int, required=False, action=ApplicationAction, help="Exclude systems less than this distance from reference")
    ap.add_argument("-m", "--max-dist", type=int, required=False, action=ApplicationAction, help="Exclude systems further this distance from reference")
    ap.add_argument("-a", "--allegiance", type=str, required=False, default=None, help="Only show systems with the specified allegiance")
    ap.add_argument("-s", "--stations", default=False, action='store_true', help="Only show systems with stations")
    ap.add_argument("-p", "--pad-size", default="M", type=str, help="Only show systems with stations matching the specified pad size")
    ap.add_argument("system", metavar="system", nargs=1, action=ApplicationAction, help="The system to find other systems near")

    remaining = arg
    args = argparse.Namespace()
    while remaining:
      args, remaining = ap.parse_known_args(remaining, namespace=args)
      self.args = args

    self.allow_outposts = (self.args.pad_size != "L")

  def run(self):
    for d in self.args.system:
      if not d['system'].lower() in env.eddb_systems_by_name:
        log.error("Could not find start system \"{0}\"!".format(d['system']))
        return

    # Add the system object to each system arg
    for d in self.args.system:
      d['sysobj'] = env.eddb_systems_by_name[d['system'].lower()]
    # Create a list of names for quick checking in the main loop
    start_names = [d['system'].lower() for d in self.args.system]

    asys = []
    
    maxdist = None

    for s in env.eddb_systems:
      # If we don't care about allegiance, or we do and it matches...
      if s['name'].lower() not in start_names and (self.args.allegiance == None or s["allegiance"] == self.args.allegiance):
        has_stns = (s["allegiance"] != None)
        # If we have stations, or we don't care...
        if has_stns or not self.args.stations:
          # If we *don't* have stations (because we don't care), or the stations match the requirements...
          if not has_stns or (s["id"] in env.eddb_stations_by_system and len([st for st in env.eddb_stations_by_system[s["id"]] if (self.allow_outposts or st["max_landing_pad_size"] == "L")])) > 0:
            dist = 0.0 # The total distance from this system to ALL start systems
            is_ok = True
            for d in self.args.system:
              start = d['sysobj']
              this_dist = (Vector3(s["x"],s["y"],s["z"]) - Vector3(start["x"],start["y"],start["z"])).length
              if 'min_dist' in d and this_dist < d['min_dist']:
                is_ok = False
                break
              if 'max_dist' in d and this_dist > d['max_dist']:
                is_ok = False
                break
              dist += this_dist

            if not is_ok:
              continue
              
            if len(asys) < self.args.num or dist < maxdist:
              # We have a new contender; add it, sort by distance, chop to length and set the new max distance
              asys.append(s)
              # Sort the list by distance to ALL start systems
              asys.sort(key=lambda t: math.fsum([
                (Vector3(t['x'],t['y'],t['z']) - Vector3(d['sysobj']['x'], d['sysobj']['y'], d['sysobj']['z'])).length
                for d in self.args.system]))

              asys = asys[0:self.args.num]
              maxdist = max(dist, maxdist)


    if not len(asys):
      print ""
      print "No matching systems"
      print ""
    else:
      print ""
      print "Matching systems close to {0}:".format(', '.join([d["system"] for d in self.args.system]))
      if len(self.args.system) > 1:
        print ""
        for i in xrange(0, len(asys)):
          print "    {0}".format(asys[i]["name"])
      print ""
      for d in self.args.system:
        if len(self.args.system) > 1:
          print "  Distance from {0}:".format(d['system'])
          print ""
        asys.sort(key=lambda t: (Vector3(t["x"],t["y"],t["z"]) - Vector3(d['sysobj']['x'], d['sysobj']['y'], d['sysobj']['z'])).length)
        for i in xrange(0,len(asys)):
          # Print distance from the current candidate system to the current start system
          print "    {0} ({1:.2f}Ly)".format(asys[i]["name"], (Vector3(asys[i]["x"],asys[i]["y"],asys[i]["z"]) - Vector3(d['sysobj']['x'], d['sysobj']['y'], d['sysobj']['z'])).length)
        print ""

if __name__ == '__main__':
  a = Application(env.local_args, False)
  a.run()

