#!/usr/bin/env python3

import argparse
import csv
import os
import re
import requests

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
    parser.add_argument("--bells", "-b", type=int, default='4+')
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
    return parse_performance_list(response.content) if (response.status_code == 200) else None

def main(place=None, region=None, filename=None, since=None, bells='4+', verbose=False):
    data = (parse_performance_list(filename)
            if filename
            else performances(place, region, since, bells, verbose))
    for p in data:
        print(p)

# https://bb.ringingworld.co.uk/export.php?from=01%2F01%2F2023&region=Cambridgeshire&bells_type=tower&fmt=csv_header

if __name__ == "__main__":
    main(**get_args())
