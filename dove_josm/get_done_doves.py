#!/usr/bin/env python3

import argparse
import csv
import os

import overpy

"""Program to fetch ref:dove data from OSM and save it with the OSM IDs for the same objects."""

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-file", "-o",
                        default="~/ringing/doves-done.csv")
    parser.add_argument("--towers-file", "-t",
                        default="~/Downloads/dove.csv",
                        help="""The location of the towers file, as downloaded from Dove (https://dove.cccbr.org.uk/).""")
    return vars(parser.parse_args())

def saint(name):
    return (name
            .removeprefix("Cath Ch ")
            .removeprefix("Cathedral ")
            .removeprefix("Church ")
            .removeprefix("of ")
            .removeprefix("the ")
            .removeprefix("St ")
            .removeprefix("St. ")
            .removeprefix("Saint ")
            .removeprefix("S ")
            .split(" ")[0]
            .removesuffix("'s")
            .removesuffix("s")
            )

def get_done_doves(output_file, towers_file):
    api = overpy.Overpass()
    result = api.query("""[out:json]; nwr ["ref:dove"]; out tags;""")
    towers = {}
    with open(os.path.expanduser(towers_file)) as dovestream:
        towers = {tower['TowerID']: tower for tower in csv.DictReader(dovestream)}
    with open(os.path.expanduser(output_file), "w") as outstream:
        writer = csv.writer(outstream)
        writer.writerow(["OSM ID", "Dove ID", "OSM name", "Dove Dedicn", "Dove Place", "Check"])
        for obj_group in [result.ways, result.nodes, result.relations]:
            for obj in obj_group:
                dove_id = obj.tags["ref:dove"]
                dove_data = towers.get(dove_id, {})
                osm_name = obj.tags.get("name", "")
                dove_dedicn = dove_data['Dedicn']
                writer.writerow([obj.id,
                                 dove_id,
                                 osm_name,
                                 dove_dedicn,
                                 dove_data['Place'],
                                 "" if saint(osm_name) == saint(dove_dedicn) else "?"])
    print(len(result.ways) + len(result.nodes) + len(result.relations), "towers tagged")

if __name__ == "__main__":
    get_done_doves(**get_args())
