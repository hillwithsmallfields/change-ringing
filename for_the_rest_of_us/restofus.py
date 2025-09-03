#!/usr/bin/env python3

"""Advancing ringing for the rest of us

Code to arrange change-ringing learning sessions for those who don't
have suitable ringers around them, or whose tower captains hold them
back.

"""

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
                 email: str or None,
                 learning_status: dict or None,
                 group=None):
        self.name = name
        self.email = email
        self.learning_status = learning_status or dict() # method names to lists of place bell scores
        if group:
            group.ringers[name] = self

    def __str__(self):
        return "%s <%s>" % (self.name, self.email)

    def __repr__(self):
        return "<Ringer %s <%s> with %d methods>" % (self.name, self.email, len(self.learning_status))

    def to_dict(self):
        """Return a JSON-serializable dictionary representing this ringer."""
        return {
            'name': self.name,
            'email': self.email,
            'learning_status': self.learning_status
        }

    # maybe do this at the AttendeeGroup level?
    # @staticmethod
    # def from_dict(data):
    #     return Ringer(**data)

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

        If there is already an object for a ringer of that name, that existing object is returned."""
        return (ringer
                if isinstance(ringer, Ringer)
                else (self.ringers[ringer]
                      if ringer in self.ringers
                      else Ringer(name=ringer, group=self, **kwargs)))

class Method:

    """A change-ringing method."""

    def __init__(self, name: str, stage: int or None):
        self.name = name
        self.stage = stage or nbells(name)
        self.place_notation = None
        self.bob = None
        self.single = None
        self._rows = None

def asMethod(method):
    return method if isinstance(method, Method) else Method(method)

def asMethodName(method):
    return method.name if isinstance(method, Method) else method

class Call:

    pass

class Lead(Call):

    def __init__(self, method: Method, place: int):
        self.method = method
        self.place = place

class LeadEndVariant(Call):

    def __init__(self, call_type: str):
        self.call_type = call_type

class Touch:

    def __init__(self, ringers, calls):
        self.ringers = ringers
        self.calls = calls
