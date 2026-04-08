#!/usr/bin/env python3

import collections
import csv
import os

DOVE_FILE = os.path.expanduser("~/Downloads/dove.csv")
DOVE_URL = "https://dove.cccbr.org.uk/towers.csv"

def tower_names(tower):
    """Return various names by which a tower may be known."""
    return set([tower['PlaceCL'] or tower['Place'],
                tower['Place'],
                tower['AltName'] or tower['Place'],
                "%s, %s" % (tower['Place'], tower['Dedicn']),
                "%s (%s)" % (tower['Place'], tower['County']),
                ])

def download_dove():
    if not os.path.exists(DOVE_FILE):
        print("Downloading tower data from Dove's Guide")
        download = requests.get(DOVE_URL)
        if download.status_code == 200:
            print("Saving Dove data")
            start = 0
            while ord(download.text[start]) & 0x80:
                start += 1
            with open(DOVE_FILE, 'w') as dove_save:
                dove_save.write(download.text[start:])
        else:
            print("Failed to fetch Dove data")

def read_dove():
    """Read the Dove data as a dictionary of lists.

    Each tower appears under multiple names, as returned by the function `tower_names`.

    Each entry is a list of towers with that name (so you can tell
    whether you need more information for disambiguation).
    """
    download_dove()
    dove = collections.defaultdict(list)
    for tower in csv.DictReader(dovestream):
        for name in tower_names(tower):
            if (tower['RingType'] == 'Full-circle ring'
                and tower['Bells'] != "1"):
                dove[name].append(tower)
    return dove
