Advancing ringing for the rest of us
====================================

The problem
-----------

I think it's quite common for ringers to be frustrated at the lack of
opportunity to increase the range of methods they can ring.

There are several possible reasons for not getting chances to ring new methods:

* none of the practices you can get to have ringers to ring those methods with you

* your tower captain doesn't think you're ready to try a new method, no matter how thoroughly you have learnt it

* there are ringers around who can ring the methods you're interested in, but they form a clique that you're not part of

A possible solution
-------------------

I have devised a type of learning session that is intended to get
around these problems.  The instance I have in mind is for learning a
range of Surprise Major methods, but it could be applied to any group
of methods.

I assume that tower captains who hold ringers back from method
learning, and cliques of advanced ringers, will not be interested in
supporting this, so the approach is designed to do without their
participation.  This means that there may not be people around who can
correct other ringers, which leads to **ringing one lead at a time**,
so that if it goes wrong, the band can stand immediately, or shortly
afterwards, and discuss between them what went wrong.  This also means
that the mistakes will be fresher in the ringers' short-term memories
than if the mistakes had been corrected and a longer touch completed.

The sessions will be advertised for a **range of methods**, in the
hope that ringers looking for an opportunity to ring methods at the
more advanced end of the range will sign up and be available as
helpers for those learning the more basic methods.  For example, you
might get ringers who can ring the Standard Eight and are looking for
opportunities to ring Belfast and Glasgow, who will be available to
reinforce the bands for those learning methods from the Standard
Eight.

As this is learner-driven rather than expert-driven, the participants
might not include anyone with expertise in running practice sessions.
The software suite to which this document is attached is designed to
track learners' progress and place bands accordingly; it may be able
to do this to a finer grain of tracking than any but the best tower
captains could do: it will apply something like spaced repetition at
the level of individual place bells.

Using the system
----------------

Sometime in advance of the session, ringers can sign up, indicating
which methods they are learning (in order of preference) and which of
the methods they already know.  Initially this will probably be by
emailing the organiser, who will use a command line program, but later
through web form.

At the session, the organiser runs the software to generate a band
placement for a method, and the band rings a lead of that method.
Scores are recorded, either by self-reporting whether you think you
got through the lead correctly, or through connecting to a program
that reads some of the intermediate files of HawkEar, and the ringers'
progress is stored on the computer and used to place bands for
subsequent touches (leads).

At the end of the session, each participant can receive a data file
recording how they are doing on each method.  In early versions, this
will probably be emailed to them by the organiser, but later versions
should provide a human-readable web page for each learner, with a link
to download their records.  These files can then be uploaded when
signing up for future sessions that use the same (or compatible)
software; these don't have to be at the same tower.

Some details
------------

The system keeps a table of methods for each user, with a score for
how well they are doing for each place bell of each method.  The
initial contents are set up when the user registers for the session,
with a negative score for all the place bells of the methods they want
to learn, and a positive score for the methods they already know.  The
priority the learners give to the methods will be represented by a
more negative number for their higher-priority methods.

At the start of the session, the software filters out any methods for
which there aren't enoughn people signed up to make a band.

When setting up a lead to ring, the software first picks a method, by
looking for the most negative number of the total scores for a method
(from all users); that is, the method for which there is most learning
demand.

Then it starts placing ringers: first it puts learners into the band,
and it watches the total score of how the placed ringers have
previously done on the place bells they have been placed on.  If that
score goes below (more negative) than a set threshold, it switches to
placing helpers; if that brings the total score up above another
threshold, it returns to placing learners, and so on.

After the lead has been rung, the software takes in the scores, either
from users indicating whether they feel they succeeded, or from
HawkEar.  If a user completed their place bell successfully, their
score for that place bell for that method is increased, indicating
that they have less need to learn it (and will eventually go above
zero, indicating that they are now a helper for that place bell);
otherwise, the number is decreased, indicating a greater need to try
that piece again.

The score thresholds for adding more helpers or more learners will be
configurable; likewise the amounts to add or subtract to the score on
ringing a lead successfully or failing to do so.

Development status
------------------

I'm well into writing the placement code (as of early September 2025)
and expect to have the rest of the command-line form of the system
done within a couple of weeks.  After that, I hope to put a web
front-end onto it, but I'm really a back-end developer so I'm further
from making any promises on that.
