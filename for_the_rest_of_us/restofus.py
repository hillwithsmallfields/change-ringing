#!/usr/bin/env python3

"""Advancing ringing for the rest of us

Code to arrange change-ringing learning sessions for those who don't
have suitable ringers around them, or whose tower captains hold them
back.

"""

class Ringer:

    def __init__(self, name: str):
        self.name = name

class Method:

    def __init__(self, stage: int, name: str):
        self.stage = stage
        self.name = name
        self.place_notation = None
        self.bob = None
        self.single = None

class Lead:

    def __init__(self, method: Method, place: int):
        self.method = method
        self.place = place

class Touch:

    def __init__(self, ringers, calls):
        self.ringers = ringers
        self.calls = calls
