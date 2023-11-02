#!/usr/bin/env python3

import argparse
import csv
import math
import os
import requests
import pyperclip

R_EARTH = 6378000               # metres

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", "-s",
                        help="""Where to start, in alphabetical order.""")
    parser.add_argument("--end", "-e",
                        help="""Where to end, in alphabetical order.""")
    parser.add_argument("--towers-file", "-t",
                        default="~/Downloads/dove.csv",
                        help="""The location of the towers file.""")
    parser.add_argument("--bounding-box",
                        type=float,
                        default=75,
                        help="""The size of the bounding box to set in JOSM.""")
    return vars(parser.parse_args())

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

def dove_josm_main(start, end, towers_file, bounding_box: float):
    with open(os.path.expanduser(towers_file)) as dovestream:
        towers = list(csv.DictReader(dovestream))
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
    print(len(towers), "towers selected")
    dove_josm_drive(towers, bb_size=bounding_box)

if __name__ == "__main__":
    dove_josm_main(**get_args())
