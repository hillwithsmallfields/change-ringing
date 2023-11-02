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
    return vars(parser.parse_args())

def get_done_doves(output_file):
    api = overpy.Overpass()
    result = api.query("""[out:json]; nwr ["ref:dove"]; out tags;""")
    with open(os.path.expanduser(output_file), "w") as outstream:
        writer = csv.writer(outstream)
        writer.writerow(["OSM ID", "Dove ID"])
        for way in result.ways:
            writer.writerow([way.id, way.tags["ref:dove"]])

if __name__ == "__main__":
    get_done_doves(**get_args())
