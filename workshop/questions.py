"""The question pool, and which questions count.

Thirty-seven annotated questions live in two authoring files. This module is
the only place that decides which are disclosed and which are ranked.
Rebalancing the workshop is an edit here, not a move between files.

Three groups, all chosen from measurement rather than taste. Re-derive them
with `uv run python -m workshop.bench` after any corpus change.

HEADROOM    No permitted configuration retrieves the controlling evidence for
            these, so ranking people on them would be ranking them on nothing.
            They are shown, never scored. They are also the honest test of
            whether a stronger embedding model is the ceiling: if one arrives
            and moves these, that is a measurement, not a belief.
SCORED      Everything else. At least one configuration reaches the evidence,
            so effort can pay.
CALIBRATION A disclosed subset of SCORED, picked so the numbers move when a
            change helps. It carries eight questions that flip across the lever
            ladder and four that the starter already solves, so a first run is
            not a column of zeroes.

A calibration set that stops discriminating is worse than none, because it
tells a team their change did nothing when it did.
"""

from .corpus import MATTERS as _MATTERS
from .heldout import QUESTIONS as _AUTHORED_B
from .validation import QUESTIONS as _AUTHORED_A

# Matter id to the client and the supplier on the other side of the agreement.
# Re-exported so the runners never import the corpus source, whose comments
# document the case constructions. Both names are for the reader: a question
# that carries them would identify the matter lexically, which is the failure
# this corpus is built to produce.
MATTERS = {
    key: {"name": value["name"], "counterparty": value["supplier"]}
    for key, value in _MATTERS.items()
}

ALL = _AUTHORED_A + _AUTHORED_B

# Measured unreachable: best coverage 0.0 across every configuration tried,
# including all fusion weightings, DBSF, ColBERT rescore, each signal alone,
# and a 150-deep candidate pool. Their evidence sits at ranks 8 to 23.
#
# Two uplift questions left this list in September 2026. Their wording opened
# with the client's own name, and removing it put their evidence inside the top
# five, so they are scored now. Re-measure this list after any question edit:
# a question that became reachable and stays here is a question nobody is
# credited for solving.
HEADROOM_IDS = [
    "harbor-cure-before",
    "harbor-liability-cap",
    "cedar-uplift-promotional",
    "cedar-renewal-notice",
    "atlas-warranty-modified",
    "atlas-flood-payment",
]

# Flip across the ladder, covering every rung that pays.
_RESPONSIVE = [
    "atlas-rejection-before",         # drop the status filter
    "harbor-retention-earlier",       # drop the status filter
    "harbor-dispute-pauses-cure",     # matter filter and status filter together
    "cedar-service-credit",           # matter filter
    "atlas-substitution-approved",    # group by source family
    "atlas-substitution-conditions",  # group by source family
    "cedar-subcontractor",            # matter filter
    "cedar-exit-midterm",             # the second dense vector
]
# Solved by the starter, so the first run shows something working.
_ALREADY_SOLVED = [
    "harbor-retention",
    "atlas-rejection-boundary",
    "cedar-credit-deadline",
    # Disclosed on purpose: a memo is the controlling evidence here, so a team
    # that down-weights memos as a class to win the substitution question is
    # shown the cost immediately rather than at scoring time.
    "atlas-inspection-result",
]

CALIBRATION_IDS = _RESPONSIVE + _ALREADY_SOLVED
# Two ceiling probes, shown with the calibration set and never counted.
PROBE_IDS = ["harbor-cure-before", "harbor-liability-cap"]

HEADROOM = [x for x in ALL if x["question_id"] in HEADROOM_IDS]
SCORED = [x for x in ALL if x["question_id"] not in HEADROOM_IDS]
CALIBRATION = [x for x in SCORED if x["question_id"] in CALIBRATION_IDS]
PROBES = [x for x in ALL if x["question_id"] in PROBE_IDS]
HELD_OUT = [x for x in SCORED if x["question_id"] not in CALIBRATION_IDS]

assert len(HEADROOM) == len(HEADROOM_IDS), "unknown id in HEADROOM_IDS"
assert len(CALIBRATION) == len(CALIBRATION_IDS), "unknown id in CALIBRATION_IDS"
assert len(PROBES) == len(PROBE_IDS), "unknown id in PROBE_IDS"
assert set(PROBE_IDS) <= set(HEADROOM_IDS), "a probe must be unreachable, or score it"
assert len(SCORED) == len(CALIBRATION) + len(HELD_OUT)
