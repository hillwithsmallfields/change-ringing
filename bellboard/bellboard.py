#!/usr/bin/env python3

import csv
import os
import re

"""Read, expand and normalise BellBoard data from its CSV output."""

METADATA_PATTERN_STR = r"[0-9]+ [Cc][Oo][Mm]|[Aa][Tt][Ww]\.?"
METADATA_PATTERN = re.compile(METADATA_PATTERN_STR)
REMOVE_METADATA = re.compile("(.+) " + METADATA_PATTERN_STR)

def _is_metadata(text):
    return METADATA_PATTERN.match(text)

def _normalise(text):
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
    return text

def _methods(details):
    details = details.replace("&", ";").replace(" and ", ";")
    groups = details.split(';') if ';' in details else [details]
    inners = [_normalise(filtered)
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
        self.changes = row['changes']
        methods = row['title']
        self.methods = _methods(row['method_details']) if re.search("([0-9]+m)", methods) else [methods]
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
        return f"<Performance {self.performance_id} {self.date_rung} {self.methods} {list(self.by_ringer.keys())}>"

def parse_performance_list(csv_file="~/Downloads/export.csv"):
    with open(os.path.expanduser(csv_file), 'rb') as stream:
        bytes = stream.read()
        # strip optional header stuff
        while bytes[0] & 0x80:
            bytes = bytes[1:]
        return [Performance(row) for row in csv.DictReader(bytes.decode('utf8').splitlines())]

if __name__ == "__main__":
    for p in parse_performance_list():
        print(p)
