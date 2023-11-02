#!/usr/bin/env python3

import argparse
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

def dove_josm_drive(tower_list, bb_size: float):
    count = len(tower_list)
    progress = 1
    for tower in tower_list:
        if tower['RingType'] == 'Full-circle ring' and tower['UR'] == "":
            name = tower['Place'] + " " + tower['Dedicn']
            latitude = float(tower['Lat'])
            longitude = float(tower['Long'])
            tower_id = tower['TowerID']
            # copy the tower ID into the clipboard, for easy pasting into JOSM
            pyperclip.copy(tower_id)
            # see https://stackoverflow.com/questions/7477003/calculating-new-longitude-latitude-from-old-n-meters
            dx = bb_size/2
            dy = bb_size/2
            bottom  = latitude - (dy / R_EARTH) * (180 / math.pi)
            top  = latitude + (dy / R_EARTH) * (180 / math.pi)
            left = longitude - (dx / R_EARTH) * (180 / math.pi) / math.cos(latitude * math.pi/180)
            right = longitude + (dx / R_EARTH) * (180 / math.pi) / math.cos(latitude * math.pi/180)
            # see https://josm.openstreetmap.de/wiki/Help/RemoteControlCommands#load_and_zoom
            requests.get("""http://127.0.0.1:8111/load_and_zoom?changeset_comment=semi-manual tagging of bell towers&changeset_source=Dove&left=%f&right=%f&bottom=%f&top=%f""" % (left, right, bottom, top))
            print("[% 4d/% 4d]" % (progress, count), tower_id, name, "at", latitude, longitude, "type return to continue")
            progress += 1
            _ = input()

def dove_josm_main(start, end, towers_file, done, match, bounding_box: float, around, within: float):
    with open(os.path.expanduser(towers_file)) as dovestream:
        towers = list(csv.DictReader(dovestream))
    already_done = []
    if done:
        with open(os.path.expanduser(done)) as donestream:
            already_done = [tower["Dove ID"] for tower in csv.DictReader(donestream)]
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
    towers = [tower
              for tower in towers
              if tower["TowerID"] not in already_done]
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
    print(len(towers), "towers selected")
    dove_josm_drive(towers, bb_size=bounding_box)

if __name__ == "__main__":
    dove_josm_main(**get_args())
