#!/usr/bin/env python3

import argparse
import collections
import csv
import os
import re
import requests

import pyproj

import towers

"""Read, expand and normalise BellBoard data from its CSV output."""

STAGES_PATTERN = re.compile(" (Singles|Minimus|Doubles|Minor|Triples|Major|Caters|Royal|Cinques|Maximus|Max)")

METADATA_PATTERN_STR = r"[0-9]+ [Cc][Oo][Mm]|[Aa][Tt][Ww]\.?"
METADATA_PATTERN = re.compile(METADATA_PATTERN_STR)
REMOVE_METADATA = re.compile("(.+) " + METADATA_PATTERN_STR)

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--place", "-p")
    parser.add_argument("--region", "--county", "-c")
    parser.add_argument("--filename", "--file", "-f")
    parser.add_argument("--since", "-s")
    parser.add_argument("--bells", "-b", default='4+')
    parser.add_argument("--tower-details", "--towers", action='store_true')
    parser.add_argument("--verbose", "-v", action='store_true')
    return vars(parser.parse_args())

def _is_metadata(text):
    return METADATA_PATTERN.match(text)

def _normalise(text, stage):
    text = m.group(1) if (m := re.match("[0-9]+(?: each)? (.+)", text)) else text
    text = m.group(1) if (m := re.match(r"\([0-9]+\) (.+)", text)) else text
    text = m.group(1) if (m := re.match(REMOVE_METADATA, text)) else text
    for prefix in ["one ", "two ", "three ", "extents ", "extent ", "each ", "of "]:
        text = text.removeprefix(prefix)
    for suffix in ["."]:
        text = text.removesuffix(suffix)
    for abbreviation, expansion in [("S", "Surprise"),
                                    ("D", "Delight"),
                                    ("TB", "Treble Bob"),
                                    ("T B", "Treble Bob"),
                                    ("TP", "Treble Place"),
                                    ("T P", "Treble Place"),
                                    ]:
        if text.endswith(abbreviation):
            text = text.replace(abbreviation, expansion)
        if not STAGES_PATTERN.search(text):
            text += " " + stage
    return text.strip(' ')

def _methods(details, stage):
    details = details.replace("&", ";").replace(" and ", ";")
    groups = details.split(';') if ';' in details else [details]
    inners = [_normalise(filtered, stage)
              for filtered in (method.strip()
                             for group in groups
                             for method in (group.split(',') if ',' in group else [group]))
              if not _is_metadata(filtered)]
    # print("processing", details, "to", inners)
    return inners

class Performance:

    def __init__(self, row):
        self.performance_id = row['performance_id']
        self.date_rung = row['date_rung']
        self.association = row['association']
        self.place = row['place']
        self.address = row['address']
        self.region = row['region']
        self.bells_type = row['bells_type']
        self.tenor = row['tenor']
        self.duration = row['duration']
        changes = row['changes']
        self.changes = int(changes) if changes else None
        methods = row['title']
        staged = STAGES_PATTERN.search(methods)
        self.methods = _methods(row['method_details'],
                                staged.group(1) if staged else "") if re.search("([0-9]+m)", methods) else [methods]
        self.composer = row['composer']
        self.footnotes = row['footnotes']
        self.by_ringer = {}
        maxbell = 0
        for bell in range(1, 17):
            colname = "ringer_%d" % bell
            if colname in row:
                bells = row["bell_%d" % bell]
                if bells:
                    maxbell = max(maxbell, int(bells.split('-')[1]) if '-' in bells else int(bells))
                    self.by_ringer[row[colname]] = bells
        self.by_bell = [None] * (maxbell+1)
        for ringer, bells in self.by_ringer.items():
            if '-' in bells:
                for bell in bells.split('-'):
                    self.by_bell[int(bell)] = ringer
            else:
                self.by_bell[int(bells)] = ringer

    def __str__(self):
        return f"<Performance {self.performance_id} {self.date_rung} {self.place} ({self.address}) {self.methods} {list(self.by_ringer.keys())}>"

def parse_performance_list(byte_data):
    # strip optional header stuff
    while byte_data[0] & 0x80:
        byte_data = byte_data[1:]
    return [Performance(row) for row in csv.DictReader(byte_data.decode('utf8').splitlines())]

def parse_performance_list_file(csv_file="~/Downloads/export.csv"):
    with open(os.path.expanduser(csv_file), 'rb') as stream:
        return parse_performance_list(stream.read())

def performances(place=None, region=None, since=None, bells='4+', verbose=False):
    if since and (m := re.match("([0-9]{4})/([0-9]{2})/([0-9]{2})", since)):
        since = "%02d/%02d/%04d" % (m.group(3), m.group(2), m.group(1))
    query = {'bells': bells,
             'ring_type': 'english',
             'bells_type': 'tower',
             'fmt': 'csv_header'}
    if place:
        query['place'] = place
    if region:
        query['region'] = region
    if since:
        query['from'] = since
    if verbose:
        print("Using query:", query)
    response = requests.get("https://bb.ringingworld.co.uk/export.php", query)
    if (response.status_code == 200):
        result = parse_performance_list(response.content)
        return result
    return None

dove_data = None

def get_dove_data():
    global dove_data
    if not dove_data:
        dove_data = towers.read_dove()
    return dove_data

def by_tower(perfs):
    """Combine performance and tower data."""
    by_tower = collections.defaultdict(list)
    tower_data = get_dove_data()
    for performance in perfs:
        address = performance.address.replace("St ", "S ") # Dove uses S for Saint, not St, but people usually enter St in bellboard
        full = performance.place + ", " + address
        by_tower[full if full in tower_data else performance.place].append(performance)
    return by_tower

def list_tower_performances(by_towers):
    """List the performances by tower."""
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857")
    tower_data = get_dove_data()
    for tower_name in sorted(by_towers.keys(), key=lambda place: len(by_towers[place]), reverse=True):
        tower_details = tower_data.get(tower_name)
        rung_here = by_towers[tower_name]
        osm = ""
        bells = ""
        if tower_details:
            latitude = float(tower_details['Lat'])
            longitude = float(tower_details['Long'])
            eastings, northings = transformer.transform(longitude, latitude)
            osm = "https://www.openstreetmap.org/#map=18/%f/%f" % (latitude, longitude)
            weight = int(tower_details['Wt'])
            cwt = weight // 112
            qt = (weight - (cwt * 112)) // 28
            lbs  = weight - ((cwt * 112) + (qt * 28))
            bells = " %d %d-%d-%d" % (int(tower_details['Bells']), cwt, qt, lbs)
        print("%s%s: (%d performances) %s" % (tower_name,
                                            bells,
                                            len(rung_here),
                                            osm
                                            ))
        for touch in rung_here:
            print("  ", ", ".join(touch.methods))

def main(place=None, region=None, filename=None, since=None, bells='4+', tower_details=False, verbose=False):
    data = (parse_performance_list(filename)
            if filename
            else performances(place=place, region=region, since=since, bells=bells, verbose=verbose))
    if tower_details:
        list_tower_performances(by_tower(data))
    else:
        for p in data:
            print(p)

if __name__ == "__main__":
    main(**get_args())
