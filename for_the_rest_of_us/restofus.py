#!/usr/bin/env python3

"""Advancing ringing for the rest of us

Code to arrange change-ringing learning sessions for those who don't
have suitable ringers around them, or whose tower captains hold them
back.
"""

import argparse
import collections
import csv
import datetime
import json
import os
import random
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

def nbells(method_name: str):
    """Return the number of bells in a method."""
    return STAGE_BELLS.index(method_name.split(' ')[-1].lower())

LARGE_POSITIVE_NUMBER = 1000000000

class Ringer:

    """The data and methods for a ringer."""

    def __init__(self, name: str,
                 email="",
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
                if method_name in self.learning_status:
                    for place, score in enumerate(method_scores):
                        # The incoming data may be from a scoring
                        # system, in which case only one, or only
                        # some, of the place bells may be scored, and
                        # we don't want to disturb those that aren't:
                        if score is not None:
                            self.learning_status[method_name][place] = score
                else:
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
        self.method_learning_status(method)[place_bell-1] = score

    def adjust_method_place_bell_score(self, method, place_bell, score_increment):
        """Adjust this ringer's score for a place bell of a method."""
        self.method_learning_status(method)[place_bell-1] += score_increment

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

    def add_ringer(self, name, email=""):
        """Add a ringer to the attendee group."""
        # registers by side effect
        self.ringer(name, email=email)

    def list_ringers(self):
        for name in sorted(self.ringers.keys()):
            data = self.ringers[name]
            print("Ringer", name, data.email or "(no email)")
            ringer_learning_status = data.learning_status
            method_names = sorted(ringer_learning_status.keys())
            for methname in method_names:
                print("  ", methname, ringer_learning_status[methname])

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

def worst_lead_except(scores, not_these):
    """Return the worst lead for each ringer in the given scores,
    except the not_these leads.
    scores is a list of scores.
    not_these is a list of indices to skip."""
    worst_v = LARGE_POSITIVE_NUMBER
    worst_i = None
    for i, v in enumerate(scores):
        if (not not_these[i]) and v < worst_v:
            worst_i = i
            worst_v = v
    return worst_i

def worst_leads_except(ringers_scores, not_these):
    """Return the worst lead for each ringer in the given scores,
    except the not_these leads.
    scores is a list of scores.
    not_these is a list of indices to skip."""
    return {ringer: worst_lead_except(scores, not_these)
            for ringer, scores in ringers_scores.items()}

def key_of_lowest_value(dictionary):
    lowest_k = None
    lowest_v = LARGE_POSITIVE_NUMBER
    for k, v in dictionary.items():
        if v < lowest_v:
            lowest_k = k
            lowest_v = v
    return lowest_k

class Practice:

    """A session for practicing ringing."""

    def __init__(self, ringers=None, methods=None):
        self.attendees = AttendeeGroup()
        self.methods = {name: asMethod(name) for name in methods or []}
        self._by_method = None

    def from_dict(self, data):
        """Load this practice from a data dictionary as produced by self.to_dict()."""
        for name, data in data.get('records', {}).items():
            ringer = self.attendees.ringer(name)
            ringer.learning_status.update(data['learning-status'])
            ringer.email = data.get('email', '')

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

    def add_ringer(self, table_row):
        name = table_row['Name']
        self.attendees.add_ringer(name, table_row['Email'])
        for raw_method in table_row['Ringing'].split(';'):
            method = raw_method.strip()
            self.attendees.ringers[name].learning_status[method] = [1] * nbells(method)
        for i, raw_method in enumerate(table_row['Learning'].split(';')):
            method = raw_method.strip()
            self.attendees.ringers[name].learning_status[method] = [-1/(i+1)] * nbells(method)

    def scores_by_method(self):
        """Return the current scores for each method."""
        if not self._by_method:
            self._by_method = collections.defaultdict(lambda: collections.defaultdict(dict))
            for ringer in self.attendees.ringers.values():
                for method, scores in ringer.learning_status.items():
                    self._by_method[method][ringer.name] = scores
        return self._by_method

    def ringers_for_method(self, method):
        return self.scores_by_method()[asMethodName(method)]

    def learners_for_method(self, method):
        """Return a dict binding learner names to their scores.

        A ringer counts as a learner if they have any negative scores
        for that method.
        """
        return {name: scores
                for name, scores in self.ringers_for_method(method).items()
                if any(s < 0 for s in scores)}

    def demand_for_method(self, method):
        """Return how much demand there is for learning a method."""
        return -sum(sum(scores)
                    for scores in self.learners_for_method(method).values())

    def methods_by_demand(self):
        """Return a dict binding method names to the demand for the methods."""
        return {name: self.demand_for_method(name)
                for name in self.scores_by_method().keys()}

    def methods_in_order_of_demand(self):
        demands = self.methods_by_demand()
        return sorted(demands.keys(),
                      key=lambda x: demands[x],
                      reverse=True)

    def methods_with_band_available(self):
        print("scores by method are", self.scores_by_method())
        return set([method_name
                    for method_name, scores in self.scores_by_method().items()
                    if len(scores) >= nbells(method_name)])

    def methods_in_order_of_demand_with_band_available(self):
        possible = self.methods_with_band_available()
        return [method
                for method in self.methods_in_order_of_demand()
                if method in possible]

    def most_demanded_method_with_band_available(self):
        """Return the most demanded method for which enough ringers are available."""
        return self.methods_in_order_of_demand_with_band_available()[0]

    def helpers_for_method(self, method):
        """Return a dict binding helper names to their scores.

        A ringer counts as a helper for a method if all their scores
        for that method are positive.
        """
        return {name: scores
                for name, scores in self.ringers_for_method(method).items()
                if all(s >= 0 for s in scores)}

    def place_band(self, method, lower_threshold=-2, upper_threshold=2):
        """Place a band for a method."""
        band = [None] * nbells(method)
        band_scores = [0] * nbells(method)
        learners = self.learners_for_method(method)
        helpers = self.helpers_for_method(method)
        placing_learners = True
        while not all(band):
            if not learners:
                placing_learners = False
            if placing_learners:
                each_worst_lead = worst_leads_except(learners, band)
                most_needs_practice = key_of_lowest_value(each_worst_lead)
                bell_to_allocate = each_worst_lead[most_needs_practice]
                worst_lead_score = learners[most_needs_practice][bell_to_allocate]
                band[bell_to_allocate] = most_needs_practice
                band_scores[bell_to_allocate] = worst_lead_score
                del learners[most_needs_practice]
            else:
                for i, p in enumerate(band):
                    if not p:
                        # place a helper
                        helper = random.choice(list(helpers.keys()))
                        helper_score = helpers[helper][i]
                        band[i] = helper
                        band_scores[i] = helper_score
                        del helpers[helper]
                        # we place just that one helper here, then go to the outer loop:
                        break
            overall_score = sum(band_scores)
            if overall_score < lower_threshold and helpers:
                placing_learners = False
            elif overall_score > upper_threshold and learners:
                placing_learners = True
        return band

    def list_methods(self):
        """List the methods, with their scores."""
        scores = self.scores_by_method()
        for method_name in sorted(scores.keys()):
            print(method_name)
            data = scores[method_name]
            for ringer in sorted(data.keys()):
                print("  ", ringer, data[ringer])

    def list_ringers_for_method(self, method_name):
        print("Ringers for", method_name)
        ringers = self.method_name_method(method_name)
        for name in sorted(ringers.keys()):
            print("  ", name, ringers[name])
        print("Learners for", method_name)
        learners = self.learners_for_method(method_name)
        for name in sorted(learners.keys()):
            print("  ", name, learners[name])
        print("Total demand for learning", method_name, "is", self.demand_for_method(method_name))
        print("Helpers for", method_name)
        helpers = self.helpers_for_method(method_name)
        for name in sorted(helpers.keys()):
            print("  ", name, helpers[name])

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
        "--import-record", "--import", "-i",
        action='append',
        help="""Import a ringer's record from a JSON file,
        or multiple entries from a CSV file.""")
    # Commands:
    parser.add_argument(
        "--place", "--place-for", "-p",
        help="""Place a band for a specified method.""")
    parser.add_argument(
        "--next", "-n",
        action='store_true',
        help="""Place a band for the next touch, choosing the method automatically.""")
    parser.add_argument(
        "--list-ringers", action='store_true')
    parser.add_argument(
        "--list-methods", action='store_true')
    parser.add_argument(
        "--ringers-for")
    return vars(parser.parse_args())

def practice_main(
        method=None,
        ringer=None,
        records=None,
        import_record=None,
        place=None,
        next=False,
        list_ringers=False,
        list_methods=False,
        score=None,
        ringers_for=None,
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
            if record.endswith(".csv"):
                with open(record) as recstr:
                    for row in csv.DictReader(recstr):
                        practice.add_ringer(row)
            elif record.endswith(".json"):
                with open(record) as recstr:
                    rec_data = json.load(recstr)
                    practice.attendees.ringer(rec_data['name']).merge_from_dict(rec_data)
            else:
                print("Cannot import this type of file:", record)

    # practice actions:
    if list_ringers:
        practice.attendees.list_ringers()
    if list_methods:
        practice.list_methods()
    if ringers_for:
        practice.list_ringers_for_method(ringers_for)
    if place:
        print(practice.place_band(place))
    if next:
        print(practice.place_band(practice.most_demanded_method_with_band_available()))

    # save records:
    if records:
        with open(records, 'w') as recs:
            json.dump(practice.to_dict(), recs, indent=4)

if __name__ == "__main__":
    practice_main(**get_args())
