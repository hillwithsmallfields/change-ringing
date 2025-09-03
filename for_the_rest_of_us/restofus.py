#!/usr/bin/env python3

"""Advancing ringing for the rest of us

Code to arrange change-ringing learning sessions for those who don't
have suitable ringers around them, or whose tower captains hold them
back.
"""

import argparse
import datetime
import json
import os
import shlex
import sys

STAGE_BELLS = [
    None,
    None,
    None,
    "singles",
    "minimus",
    "doubles",
    "minor",
    "triples",
    "major",
    "caters",
    "royal",
    "cinques",
    "maximus",
    ]

def nbells(stage_name: str):
    """Return the number of bells in a method."""
    return STAGE_BELLS.index(stage_name.split(' ')[-1].lower())

class Ringer:

    """The data and methods for a ringer."""

    def __init__(self, name: str,
                 email=None,
                 learning_status=None,
                 group=None):
        self.name = name
        self.email = email
        # method names to lists of place bell scores:
        self.learning_status = learning_status or {}
        if group:
            group.ringers[name] = self

    def __str__(self):
        return "%s <%s>" % (self.name, self.email)

    def __repr__(self):
        return ("<Ringer %s <%s> with %d methods>"
                % (self.name, self.email, len(self.learning_status)))

    def to_dict(self):
        """Return a JSON-serializable dictionary representing this ringer."""
        return {
            'name': self.name,
            'email': self.email,
            'learning-status': self.learning_status
        }

    def merge_from_dict(self, data):
        """Add some data to a ringer's records."""
        if 'name' in data:
            self.name = data['name']
        if 'email' in data:
            self.email = data['email']
        if 'learning-status' in data:
            for method_name, method_scores in data['learning-status'].items():
                self.learning_status[method_name] = method_scores

    def method_learning_status(self, method):
        """Return this ringer's learning status for the specified method.

        A learning status is a list of numbers, indexed by place bell.

        A negative number indicates that this ringer counts as a
        learner for that place bell, and a positive number indicates
        that they have learnt that place bell, and so count as a
        helper.
        """
        method_name = asMethodName(method)
        if method_name not in self.learning_status:
            self.learning_status[method_name] = [0.0] * nbells(method_name)
        return self.learning_status[method_name]

    def set_method_place_bell_score(self, method, place_bell, score):
        """Set this ringer's score for a place bell of a method."""
        self.method_learning_status(method)[place_bell] = score

class AttendeeGroup:

    """A group of ringers."""

    def __init__(self):
        self.ringers = {}

    def ringer(self, ringer, **kwargs):
        """Return a Ringer object, given a name or a Ringer object.

        If there is already an object for a ringer of that name, that
        existing object is returned.

        This registers the ringer in the attendee group, as a side
        effect.
        """
        return (ringer
                if isinstance(ringer, Ringer)
                else (self.ringers[ringer]
                      if ringer in self.ringers
                      else Ringer(name=ringer, group=self, **kwargs)))

    def add_ringer(self, name, email=None):
        """Add a ringer to the attendee group."""
        # registers by side effect
        self.ringer(name, email=email)

    def list_ringers(self):
        for name in sorted(self.ringers.keys()):
            data = self.ringers[name]
            print(name, data.email)
            method_names = sorted(data.learning_status.keys())
            for methname in method_names:
                print("  ", methname, data.learning_status[methname])

class Method:

    """A change-ringing method."""

    def __init__(self, name: str, stage: int or None):
        self.name = name
        self.stage = stage or nbells(name)
        self.place_notation = None
        self.bob = None
        self.single = None
        self._rows = None

    def __str__(self):
        return "<Method %s>" % self.name

def asMethod(method):
    return method if isinstance(method, Method) else Method(method)

def asMethodName(method):
    return method.name if isinstance(method, Method) else method

class Call:

    """Anything that can be called during a touch.

    This will normally be a bob, single, or change of method."""

    pass

class Lead(Call):

    """A call to switch to ringing a specified method."""

    def __init__(self, method: Method):
        self.method = method

class LeadEndVariant(Call):

    """A call, such as a bob or single."""

    def __init__(self, call_type: str):
        self.call_type = call_type

class Touch:

    """A piece of ringing, made up of at least one call."""

    def __init__(self, ringers, calls):
        self.ringers = ringers
        self.calls = calls

class Practice:

    """A session for practicing ringing."""

    def __init__(self, ringers=None, methods=None):
        self.attendees = AttendeeGroup()
        self.ringers = {name: self.attendees.ringer(name) for name in ringers or []}
        self.methods = {name: asMethod(name) for name in methods or []}

    def from_dict(self, data):
        """Load this practice from a data dictionary as produced by self.to_dict()."""
        for name, email in data.get('emails', {}).items():
            self.attendees.add_ringer(name, email=email)
        for name, scores in data.get('records', {}).items():
            self.attendees.ringer(name).learning_status.update(scores)

    def to_dict(self):
        """Make a JSON-serializable data dictionary representing this practice."""
        return {
            'timestamp': datetime.datetime.now().isoformat(timespec='seconds'),
            'command': shlex.join(sys.argv),
            'records': {
                name: ringer.to_dict()
                for name, ringer in self.attendees.ringers.items()
            }
            # TODO: perhaps record what was rung at each practice, as
            # a dict keyed by timestamp
        }

def get_args():
    """Get the command line arguments."""
    parser = argparse.ArgumentParser(
        description="""Program to help run method-learning change-ringing practices.""")
    # Input data:
    parser.add_argument(
        "--method", "-m",
        action='append',
        help="""Add this method to the methods available to the session.""")
    parser.add_argument(
        "--ringer", "-r",
        action='append',
        help="""Add this ringer to the ringers attending the session.""")
    parser.add_argument(
        "--records", "-R",
        help="""The file to load training records from and save them to.""")
    parser.add_argument(
        "--import-record", "-i",
        action='append',
        help="""Import a ringer's record from a file.""")
    # Commands:
    parser.add_argument(
        "--place", "-p",
        action='store_true',
        help="""Place a band.""")
    parser.add_argument(
        "--list-ringers", action='store_true')
    return vars(parser.parse_args())

def practice_main(
        method=None,
        ringer=None,
        records=None,
        import_record=None,
        place=False,
        list_ringers=False,
        score=None,
):
    """Run a practice action."""
    practice = Practice()
    # load initial data:
    if records and os.path.exists(records):
        with open(records) as recs:
            try:
                practice.from_dict(json.load(recs))
            except json.decoder.JSONDecodeError:
                print("Could not load records from", records)
    for method_name in method or []:
        practice.methods[method_name] = asMethod(method_name)
    for ringer_name in ringer or []:
        practice.attendees.add_ringer(ringer_name)
    for record in import_record or []:
        if record and os.path.exists(record):
            with open(record) as recstr:
                rec_data = json.load(recstr)
                practice.attendees.ringer(rec_data['name']).merge_from_dict(rec_data)

    # practice actions:
    if list_ringers:
        practice.attendees.list_ringers()
    if place:
        print(practice.place_band())

    # save records:
    if records:
        with open(records, 'w') as recs:
            json.dump(practice.to_dict(), recs, indent=4)

if __name__ == "__main__":
    practice_main(**get_args())
