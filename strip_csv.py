#!/usr/bin/env python3

import os

with open(os.path.expanduser("~/Downloads/dove.csv"), 'rb') as dovestream:
    contents = dovestream.read()

start = 0

while contents[start] & 0x80:
    start += 1

print("skipping", start, "bytes")

with open(os.path.expanduser("~/Downloads/dove-fixed.csv"), 'wb') as dovestream:
    dovestream.write(contents[start:])
