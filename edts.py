#!/usr/bin/env python

import argparse
import json
import logging
import os
import sys
import eddb
from calc import Calc
from route import Routing
from solver import Solver
from station import Station
from system import System

log = logging.getLogger("edts")

class Application:

  def __init__(self):
    ap = argparse.ArgumentParser(description = "Elite: Dangerous TSP Solver", fromfile_prefix_chars="@")
    ap.add_argument("-j", "--jump-range", type=float, required=True, help="The ship's max jump range with full fuel and empty cargo")
    ap.add_argument("-s", "--start", type=str, required=True, help="The starting station, in the form 'system/station'")
    ap.add_argument("-e", "--end", type=str, required=True, help="The end station, in the form 'system/station'")
    ap.add_argument("-n", "--num-jumps", default=None, type=int, help="The number of stations to visit, not including the start/end")
    ap.add_argument("-p", "--pad-size", default="M", type=str, help="The landing pad size of the ship (S/M/L)")
    ap.add_argument("-d", "--jump-decay", type=float, default=0.0, help="An estimate of the range decay per jump in Ly (e.g. due to taking on cargo)")
    ap.add_argument("-v", "--verbose", type=int, default=1, help="Increases the logging output")
    ap.add_argument("-r", "--route", default=False, action='store_true', help="Whether to try to produce a full route rather than just hops")
    ap.add_argument("-o", "--ordered", default=False, action='store_true', help="Whether the stations are already in a set order")
    ap.add_argument("--jump-time", type=float, default=45.0, help="Seconds taken per hyperspace jump")
    ap.add_argument("--diff-limit", type=float, default=1.5, help="The multiplier of the fastest route which a route must be over to be discounted")
    ap.add_argument("--slf", type=float, default=0.9, help="The multiplier to apply to multi-jump hops to account for imperfect system positions")
    ap.add_argument("--route-strategy", default="astar", help="The strategy to use for route plotting. Valid options are 'trundle' and 'astar'")
    ap.add_argument("--solve-full", default=False, action='store_true', help="Uses full route plotting to find an optimal route solution (slow)")
    ap.add_argument("--rbuffer-mult", type=float, default=0.15, help="A buffer distance to help search for valid stars for routing, defined in a multiple of hop straight-line distance")
    ap.add_argument("--hbuffer-ly", type=float, default=15.0, help="A buffer distance to help search for valid stars for routing. Only used by the 'trundle' strategy.")
    ap.add_argument("--eddb-systems-file", type=str, default=eddb.default_systems_file, help="Path to EDDB systems.json")
    ap.add_argument("--eddb-stations-file", type=str, default=eddb.default_stations_file, help="Path to EDDB stations_lite.json or stations.json")
    ap.add_argument("--download-eddb-files", nargs="?", const=True, help="Download EDDB files (or re-download if already present).")
    ap.add_argument("stations", metavar="system/station", nargs="*", help="A station to travel via, in the form 'system/station'")
    self.args = ap.parse_args()

    if self.args.num_jumps == None:
      self.args.num_jumps = len(self.args.stations)

    if self.args.verbose > 1:
      logging.getLogger().setLevel(logging.DEBUG)

    if self.args.download_eddb_files:
      eddb.download_eddb_files(self.args.eddb_systems_file, self.args.eddb_stations_file)
    elif not os.path.isfile(self.args.eddb_systems_file) or not os.path.isfile(self.args.eddb_stations_file):
      log.error("Error: EDDB system/station files not found. Run this script with '--download-eddb-files' to auto-download these.")
      sys.exit(1)

    self.eddb_systems = eddb.load_systems(self.args.eddb_systems_file)
    self.eddb_stations = eddb.load_stations(self.args.eddb_stations_file)
    

  def get_station_from_string(self, statstr):
    parts = statstr.split("/", 1)
    sysname = parts[0]
    statname = parts[1]

    return self.get_station(sysname, statname)

  def get_station(self, sysname, statname):
    for sy in self.eddb_systems:
      if sy["name"].lower() == sysname.lower():
        # Found system
        sysid = sy["id"]

        for st in self.eddb_stations:
          if st["system_id"] == sysid and st["name"].lower() == statname.lower():
            # Found station
            sysobj = System(sy["x"], sy["y"], sy["z"], sy["name"], bool(sy["needs_permit"]))
            stobj = Station(sysobj, st["distance_to_star"], st["name"], st["type"], bool(st["has_refuel"]), st["max_landing_pad_size"])
            
            if stobj.distance == None:
              log.warning("Warning: station {0} ({1}) is missing SC distance in EDDB. Assuming 0.".format(stobj.name, stobj.system_name))
              stobj.distance = 0
            
            return stobj
    return None


  def run(self):

    start = self.get_station_from_string(self.args.start)
    end = self.get_station_from_string(self.args.end)

    if start == None:
      log.error("Error: start station {0} could not be found. Stopping.".format(self.args.start))
      return
    if end == None:
      log.error("Error: end station {0} could not be found. Stopping.".format(self.args.end))
      return

    stations = []
    for st in self.args.stations:
      sobj = self.get_station_from_string(st)
      if sobj != None:      
        if self.args.pad_size == "L" and sobj.max_pad_size != "L":
          log.warning("Warning: station {0} ({1}) is not usable by the specified ship size. Discarding.".format(sobj.name, sobj.system_name))
          continue
        else:
          log.debug("Adding station: {0} ({1}, {2}Ls)".format(sobj.name, sobj.system_name, sobj.distance))
          stations.append(sobj)
          
      else:
        log.warning("Warning: station {0} could not be found. Discarding.".format(st))

    calc = Calc(self.args)
    r = Routing(calc, self.eddb_systems, self.args.rbuffer_mult, self.args.hbuffer_ly, self.args.route_strategy)
    s = Solver(calc, r, self.args.jump_range, self.args.diff_limit, self.args.solve_full)

    if self.args.ordered:
      route = [start] + stations + [end]
    else:
      # Add 2 to the jump count for start + end
      route = s.solve(stations, start, end, self.args.num_jumps + 2)

    totaldist = 0.0
    totaljumps = 0
    totalsc = 0
    totalsc_accurate = True

    print ""
    print route[0].to_string()
    for i in xrange(1, len(route)):
      cur_max_jump = self.args.jump_range - (self.args.jump_decay * (i-1))

      jumpcount = calc.jump_count(route[i-1], route[i], route[0:i-1])
      if self.args.route:
        hop_route = r.plot(route[i-1].system, route[i].system, cur_max_jump)
        if hop_route != None:
          jumpcount = len(hop_route)-1
        else:
          log.warning("No valid route found for hop: {0} --> {1}".format(route[i-1].system_name, route[i].system_name))

      hopsldist = (route[i-1].position - route[i].position).length
      totaldist += hopsldist
      totaljumps += jumpcount
      if route[i].distance != None and route[i].distance != 0:
        totalsc += route[i].distance
      else:
        totalsc_accurate = False

      if self.args.route and hop_route != None:
        lastdist = (hop_route[-1].position - hop_route[-2].position).length
        if len(hop_route) > 2:
          hopdist = 0.0
          for j in xrange(1, len(hop_route)-1):
            hdist = (hop_route[j-1].position - hop_route[j].position).length
            hopdist += hdist
            print "    --- {0: >6.2f}Ly ---> {1}".format(hdist, hop_route[j].name)
          hopdist += lastdist
        else:
          hopdist = hopsldist
    
      route_str = "{0}, SC: ~{1}s".format(route[i].to_string(), "{0:.0f}".format(calc.sc_cost(route[i].distance)) if route[i].distance != None and route[i].distance != 0 else "???")
      if self.args.route and hop_route != None:
        print "    === {0: >6.2f}Ly ===> {1} -- hop of {2:.2f}Ly for {3:.2f}Ly".format(lastdist, route_str, hopdist, hopsldist)
      else:
        print "    === {0: >6.2f}Ly ({1:2d} jump{2}) ===> {3}".format(hopsldist, jumpcount, "s" if jumpcount != 1 else " ", route_str)

    print ""
    print "Total distance: {0:.2f}Ly; total jumps: {1:d}; total SC distance: {2:d}Ls{3}".format(totaldist, totaljumps, totalsc, "+" if not totalsc_accurate else "")
    print ""



if __name__ == '__main__':
  logging.basicConfig(level = logging.INFO, format="[%(asctime)-15s] [%(name)-6s] %(message)s")
  a = Application()
  a.run()


