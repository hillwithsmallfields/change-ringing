#!/usr/bin/env python3

import argparse
import collections
import csv
import math
import os
import re
import requests
import pyperclip

"""JOSM remote control driver for Dove's bell-ringing database.

JOSM is directed to each tower location in turn, with the clipboard containing the Dove ID for the tower.

There are several ways to select the towers:

  * by --start and --end in alphebetical order
  * by --match on a regexp
  * within a distance of a place named in the Dove data

The towers selected are the intersection of all of these."""

R_EARTH = 6378000               # metres

def get_args():
    parser = argparse.ArgumentParser(description="JOSM remote control driver for Dove's bell-ringing database.")
    # Tower selection
    parser.add_argument("--start", "-s",
                        help="""Where to start, in alphabetical order.""")
    parser.add_argument("--end", "-e",
                        help="""Where to end, in alphabetical order.""")
    parser.add_argument("--match", "-m",
                        help="""Regexp to match place names against.""")
    parser.add_argument("--around", "-a",
                        help="""Tower to include towers within a distance of.
                        The first tower with a 'Place' equal to or after this name is used.""")
    parser.add_argument("--within", "-w", type=float,
                        help="""Distance in Km to use for --around.""")
    parser.add_argument("--county",
                        help="""Filter to towers in this county.""")
    parser.add_argument("--diocese",
                        help="""Filter to towers in this diocese.""")
    parser.add_argument("--dedication",
                        help="""Filter to towers with this dedication.""")
    # Action
    parser.add_argument("--count",
                        action='store_true',
                        help="""Only count how many towers are selected in each diocese and county.""")
    # Data files
    parser.add_argument("--towers-file", "-t",
                        default="~/Downloads/dove.csv",
                        help="""The location of the towers file, as downloaded from Dove (https://dove.cccbr.org.uk/).""")
    parser.add_argument("--done", "-d",
                        default="~/ringing/doves-done.csv",
                        help="""The location of the "done" file, as created by get_done_doves.py.""")
    # JOSM settings
    parser.add_argument("--bounding-box", "-b",
                        type=float,
                        default=75,
                        help="""The size of the bounding box (in metres) to set in JOSM.
                        This is how much of the map is downloaded around the location given in Dove.""")
    return vars(parser.parse_args())

def distance(latdeg1, londeg1, latdeg2, londeg2):
    """Return the distance in kilometres between two points."""
    # based on https://stackoverflow.com/questions/57294120/calculating-distance-between-latitude-and-longitude-in-python
    R = 6370
    lat1 = math.radians(latdeg1)
    lon1 = math.radians(londeg1)
    lat2 = math.radians(latdeg2)
    lon2 = math.radians(londeg2)

    dlon = lon2 - lon1
    dlat = lat2- lat1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def index_after(in_order, key, field):
    "Find the index of the first entry at or after the key in the sorting order."
    key = key.lower()
    for i, elt in enumerate(in_order):
        if elt[field].lower() >= key:
            return i
    return None

def filter_by_field(towers_list, field, value):
    """Filter a tower list by a given field."""
    return [tower
            for tower in towers_list
            if tower[field] == value]

def dove_josm_drive(tower_list, bb_size: float, changeset_comment_details: str):
    """Send commands to the JOSM remote control, to bring up each tower in the tower list."""
    count = len([t for t in tower_list if t['RingType'] == 'Full-circle ring' and t['UR'] == ""])
    progress = 1
    for tower in tower_list:
        name = tower['Place'] + " " + tower['Dedicn']
        latitude = float(tower['Lat'])
        longitude = float(tower['Long'])
        tower_id = tower['TowerID']
        # copy the tower ID into the clipboard, for easy pasting into JOSM
        pyperclip.copy(tower_id)
        # see https://stackoverflow.com/questions/7477003/calculating-new-longitude-latitude-from-old-n-meters
        dx = bb_size/2
        dy = bb_size/2
        # see https://josm.openstreetmap.de/wiki/Help/RemoteControlCommands#load_and_zoom
        requests.get("""http://127.0.0.1:8111/load_and_zoom?changeset_comment=semi-automatic tagging of bell towers%s&changeset_source=Dove&left=%f&right=%f&bottom=%f&top=%f"""
                     % (changeset_comment_details,
                        longitude - (dx / R_EARTH) * (180 / math.pi) / math.cos(latitude * math.pi/180), # left
                        longitude + (dx / R_EARTH) * (180 / math.pi) / math.cos(latitude * math.pi/180), # right,
                        latitude - (dy / R_EARTH) * (180 / math.pi), # bottom,
                        latitude + (dy / R_EARTH) * (180 / math.pi) # top
                        ))
        print("[% 4d/% 4d]" % (progress, count), tower_id, name, "at", latitude, longitude, "type return to continue")
        progress += 1
        _ = input()

def count_by(tower_list, selector):
    counts = collections.defaultdict(int)
    for tower in tower_list:
        counts[tower[selector]] += 1
    print("By", selector)
    fmt = "%% %ds: %%d" % max(*[len(name) for name in counts.keys()])
    for place in sorted(counts.keys()):
        print(fmt % (place, counts[place]))

def dove_josm_main(
        # files
        towers_file, done,
        # JOSM control
        bounding_box: float,
        # actions
        count: bool,
        # selection:
        match,
        start, end,
        around, within: float,
        county,
        diocese,
        dedication):
    with open(os.path.expanduser(towers_file)) as dovestream:
        towers = list(csv.DictReader(dovestream))
    already_done = set()
    if done:
        with open(os.path.expanduser(done)) as donestream:
            already_done = set(tower["Dove ID"] for tower in csv.DictReader(donestream))
    if end:
        end_index = index_after(towers, end, 'Place')
        if end_index is None:
            raise ValueError
        towers = towers[:end_index]
    if start:
        start_index = index_after(towers, start, 'Place')
        if start_index is None:
            raise ValueError
        towers = towers[start_index:]
    if match:
        towers = [tower
                  for tower in towers
                  if re.search(match, tower['Place'])]
    if around:
        around_index = index_after(towers, around, 'Place')
        if not around_index:
            raise ValueError
        around_tower = towers[around_index]
        around_lat = float(around_tower['Lat'])
        around_long = float(around_tower['Long'])
        towers = [tower
                  for tower in towers
                  if (tower['Lat']
                      and tower['Long']
                      and abs(distance(float(tower['Lat']), float(tower['Long']),
                                       around_lat, around_long))
                      <= within)]
    for selector, value in {"County": county,
                            "Diocese": diocese,
                            "BareDedicn": dedication}.items():
        if value:
            towers = filter_by_field(towers, selector, value)
    towers = [tower
              for tower in towers
              if (tower["TowerID"] not in already_done
                  and tower['RingType'] == 'Full-circle ring'
                  and tower['UR'] == "")]
    print(len(towers), "towers selected")
    if count:
        count_by(towers, 'Diocese')
        count_by(towers, 'County')
    else:
        dove_josm_drive(
            towers,
            bb_size=bounding_box,
            changeset_comment_details=(
                ""
                + ((" in %s" % county) if county else "")
                + ((" in %s diocese" % diocese) if diocese else "")
                + ((" dedicated to %s" % dedication) if dedication else "")
                + ((" matching %s" % match) if match else "")
                + ((" within %g km of %s" % (float(within), around)) if around else "")
            ))

if __name__ == "__main__":
    dove_josm_main(**get_args())
