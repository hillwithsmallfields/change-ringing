#!/usr/bin/env python3

import json
import random
import sys

PEOPLE = [
    # selected and modified from output of https://1000randomnames.com/
    "Emma Schaefer", "Isaac Nicholson", "Sage Hardy",
    "Madeleine Pritchard", "Charles Hendricks", "Jacob Walsh",
    "Richard Charlton", "Owen Smith", "Arthur Davidson", "Solomon Ford",
    "Matthias Griffiths", "Alicia Nicholson", "Duncan Morgan",
    "Delilah Graham", "Zechariah Perry", "Clara Hodges", "Thea Newman",
    "Micah Reed", "Quinn Davenport", "Eloise McKenzie", "Scott Roberson",
    "Sasha Vaughan", "Hannah Barber", "Elias Peck", "Austin Cooper",
    "Bridget Pope", "Elizabeth Newton", "Victoria Austin", "Frances Bradley",
    "Richard Parrish", "Isaias Buchanan", "Abigail Hudson", "Peter Chapman",
    "Emmitt Phelps", "Catherine Xiong", "Madeline Goodwin", "Donald Shaw",
    "Esme Hartman", "Quentin Manning", "Jennifer Coleman", "Robin Benson",
    "Flora Atkinson", "Matilda Hart", "Joel Combs", "Irene Blackwell",
    "Hazel Cline", "Malachi Gilmore", "Jonas Walsh", "Abraham Woolfe",
]

COMMON =  [
    name + " Surprise Major"
    for name in [
            # popular methods first, more obscure later
            "Cambridge",
            "Yorkshire",
            "Lincolnshire",
            "Rutland",
            "Pudsey",
            "Superlative",]]

METHODS = COMMON + [
    name + " Surprise Major"
    for name in [
           "Cornwall",
            "Lessness",
            "Bristol",
            "London",
            "Belfast",
            "Glasgow",
            "Jersey",
            "Preston",
            "Ipswich",
            "Cray",
            "Ashtead",
            "DoubleDublin",
            "Uxbridge",
            "Whalley",
            "Tavistock",
            "Cassiobury",
            "Lindum",
            "Watford",
            "Wembley"]]

def random_methods():
    methods = {}
    methods_known_names = set(random.sample(COMMON, random.randint(1, len(COMMON)//2)))
    methods_learning_names = set(random.sample(METHODS, random.randint(1, len(METHODS)//4))) - methods_known_names
    for name in methods_known_names:
        methods[name] = [0, 1, 1, 1, 1, 1, 1, 1]
    for name in methods_learning_names:
        methods[name] = [0, -1, -1, -1, -1, -1, -1, -1]
    return methods

def gen_rand_data():
    return {
        'emails': {name: "%s@%s.com" % tuple(n.lower() for n in name.split(' '))
                   for name in PEOPLE},
        'records': {name: random_methods() for name in PEOPLE}
    }

json.dump(gen_rand_data(),
          sys.stdout,
          indent=4)
