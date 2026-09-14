"""The twelve validation questions, adjudicated before the competition is built.

Relevance rubric, written down before annotation so that annotation choices do
not dominate the apparent effect of tuning:

controlling   Evidence the answer cannot be given without. A question with two
              controlling passages needs both, and retrieving one of the two
              earns half of the coverage score for that question.
supporting    Evidence a careful reader would cite in addition. It raises
              ranking quality and never substitutes for a controlling passage.
inapplicable  Wrong matter, or outside the effective window on the question
              date. Returning one of these costs applicability.
distractor    In scope and readable, and still not evidence for this question.
              A memo that restates a clause is a distractor, not authority.

A superseded clause is controlling whenever the question is dated inside its
effective window. Old material returned is not a failure by itself.

A duplicated memo family counts once. Five copies of the same memo in the
result list score as one distractor, and the ranking score reads the family
rather than the document identifier.

Every date below is a question date. Applicability is judged as
effective_from <= question date < effective_to.
"""

from .corpus import BY_ID, MATTERS

QUESTIONS = []


def build(
    qid,
    *,
    matter,
    as_of,
    question,
    construction,
    controlling,
    supporting=(),
    inapplicable=(),
    distractor=(),
    rationale,
    improvement,
):
    """One annotated question. Shared by the calibration set and the held-out set."""
    return (
        {
            "question_id": qid,
            "matter_id": matter,
            "as_of": as_of,
            "question": question,
            "construction": construction,
            "controlling": list(controlling),
            "supporting": list(supporting),
            "inapplicable": list(inapplicable),
            "distractor": list(distractor),
            "rationale": rationale,
            "improvement": improvement,
        }
    )


def q(qid, **kw):
    QUESTIONS.append(build(qid, **kw))


# --- Harbor ----------------------------------------------------------------

q(
    "harbor-cure-before",
    matter="harbor",
    as_of="2026-01-20",
    question=(
        "Meridian says we broke the contract and sent us a letter about it on 20 January 2026. "
        "How long do we have to put it right before they can walk away?"
    ),
    construction="historical applicability",
    controlling=["harbor-cure"],
    supporting=["harbor-convenience"],
    inapplicable=["harbor-am3-2", "cedar-cure", "atlas-cure"],
    distractor=["harbor-notices", "harbor-s14-2", "harbor-s11-4"],
    rationale=(
        "Section 11.1 as originally executed governs a notice received before 1 April 2026. "
        "Amendment No. 3 says so in its own text, and its effective window starts after the "
        "question date. The controlling passage carries status superseded, which is correct "
        "for this question."
    ),
    improvement=(
        "Filter on the effective-date interval with the question date instead of filtering "
        "on status."
    ),
)
q(
    "harbor-cure-boundary",
    matter="harbor",
    as_of="2026-04-01",
    question=(
        "Meridian sent us that same letter on 1 April 2026 instead. How long do we have to put "
        "things right?"
    ),
    construction="historical applicability, changeover date",
    controlling=["harbor-am3-2"],
    supporting=[],
    inapplicable=["harbor-cure", "cedar-cure", "atlas-cure"],
    distractor=["harbor-convenience"],
    rationale=(
        "The amendment applies from and after 1 April 2026, so the fifteen day period "
        "governs a notice received on that date. The original window ends on the same day "
        "and does not include it."
    ),
    improvement=(
        "Use an exclusive upper bound on the effective-date interval so the changeover date "
        "falls to the amendment."
    ),
)
q(
    "harbor-liability-cap",
    matter="harbor",
    as_of="2026-09-01",
    question=(
        "If Meridian leaks our patient data, is the most we can claim back from them capped at a "
        "year of fees?"
    ),
    construction="evidence dependency",
    controlling=["harbor-msa-13-1", "harbor-msa-1-14"],
    supporting=[],
    inapplicable=[],
    distractor=["harbor-msa-13-2", "harbor-confidentiality"],
    rationale=(
        "Section 13.1 states the cap and sends the reader to Section 1.14 for the carve-out. "
        "Section 1.14 puts a Section 9 breach outside the cap. One passage alone gives the "
        "wrong answer in either direction."
    ),
    improvement=(
        "Follow the cross-references in the payload, or raise the candidate pool so the "
        "definition survives fusion."
    ),
)
q(
    "harbor-retention",
    matter="harbor",
    as_of="2026-09-01",
    question=(
        "How long does Meridian have to keep our patient files before it is allowed to delete them?"
    ),
    construction="authority versus repetition",
    controlling=["harbor-exh-d2"],
    supporting=[],
    inapplicable=["harbor-exh-d1"],
    distractor=[f"harbor-retention-note-{n}" for n in range(1, 6)] + ["harbor-s7-2"],
    rationale=(
        "Exhibit D-2 fixes seven years for clinical records from 1 February 2026. Exhibit D-1 "
        "said three years and no longer governs. Five internal memos still repeat the three year "
        "figure, so they are stale rather than merely wrong, and each memo carries its own "
        "document identifier, so deduplicating by identifier keeps all five. Section 7.2 sets a "
        "three year general period and defers to a Schedule that fixes a longer one."
    ),
    improvement=(
        "Group results by source family before ranking, and prefer the instrument over "
        "documents that cite it."
    ),
)

# --- Cedar -----------------------------------------------------------------

q(
    "cedar-uplift-before",
    matter="cedar",
    as_of="2025-06-10",
    question=(
        "Our Cedar renewal lands on 1 July 2025. How much can Tessellate put the price up?"
    ),
    construction="historical applicability",
    controlling=["cedar-sub-6-2"],
    supporting=[],
    inapplicable=["cedar-am1-3", "cedar-addendum-a"],
    distractor=["cedar-sub-6-3"],
    rationale=(
        "The renewal date falls before the Amendment Effective Date of 1 January 2026, and "
        "Amendment No. 1 preserves the index-linked cap for those renewals. The superseded "
        "clause is the controlling evidence."
    ),
    improvement="Filter on the effective-date interval with the question date.",
)
q(
    "cedar-uplift-boundary",
    matter="cedar",
    as_of="2026-01-01",
    question=(
        "Same question for the renewal that lands on 1 January 2026. How much can Tessellate put "
        "the price up?"
    ),
    construction="historical applicability, changeover date",
    controlling=["cedar-am1-3"],
    supporting=[],
    inapplicable=["cedar-sub-6-2", "cedar-addendum-a"],
    distractor=["cedar-sub-6-3"],
    rationale=(
        "The amendment applies from and after 1 January 2026, so the five percent cap governs "
        "a renewal on that date."
    ),
    improvement="Use an exclusive upper bound on the effective-date interval.",
)
q(
    "cedar-service-credit",
    matter="cedar",
    as_of="2026-09-01",
    question=(
        "The platform was down for six hours in August 2026, during a planned maintenance slot "
        "they told us about in advance. Do we get any money back?"
    ),
    construction="evidence dependency",
    controlling=["cedar-sla-4", "cedar-sla-1"],
    supporting=[],
    inapplicable=[],
    distractor=["cedar-sub-9-1"],
    rationale=(
        "Section 4 sets the credit and defers to the Monthly Uptime definition. Section 1 "
        "removes announced maintenance minutes from the calculation, so the outage does not "
        "count. The credit clause alone suggests the opposite answer."
    ),
    improvement="Follow the cross-reference, or raise the candidate pool before fusion.",
)
q(
    "cedar-renewal-notice",
    matter="cedar",
    as_of="2026-09-01",
    question=(
        "How far ahead do we have to tell Tessellate we are leaving, so the contract does not roll "
        "over for another year?"
    ),
    construction="authority versus repetition",
    controlling=["cedar-sub-3-1"],
    supporting=[],
    inapplicable=[],
    distractor=[f"cedar-renewal-note-{n}" for n in range(1, 5)],
    rationale=(
        "Section 3.1 requires ninety days. Four deal desk memos repeat a thirty day figure "
        "and state that the agreement controls. Repetition across four documents is not "
        "corroboration."
    ),
    improvement="Group by source family and prefer the instrument the memos cite.",
)

# --- Atlas -----------------------------------------------------------------

q(
    "atlas-rejection-before",
    matter="atlas",
    as_of="2026-05-20",
    question=(
        "A shipment landed on 20 May 2026 and the parts are wrong. How long do we have to send "
        "them back?"
    ),
    construction="historical applicability",
    controlling=["atlas-sup-4-2"],
    supporting=[],
    inapplicable=["atlas-am2-1"],
    distractor=["atlas-sup-4-3"],
    rationale=(
        "Amendment No. 2 applies to deliveries from 1 June 2026 and preserves the thirty day "
        "window for earlier deliveries. The superseded clause is the controlling evidence."
    ),
    improvement="Filter on the effective-date interval with the delivery date.",
)
q(
    "atlas-rejection-boundary",
    matter="atlas",
    as_of="2026-06-01",
    question=(
        "Same problem with a shipment that landed on 1 June 2026. How long do we have to send them "
        "back?"
    ),
    construction="historical applicability, changeover date",
    controlling=["atlas-am2-1"],
    supporting=[],
    inapplicable=["atlas-sup-4-2"],
    distractor=["atlas-sup-4-3"],
    rationale=(
        "The amendment applies from and after 1 June 2026, so the ten business day window "
        "governs a delivery on that date."
    ),
    improvement="Use an exclusive upper bound on the effective-date interval.",
)
q(
    "atlas-warranty-modified",
    matter="atlas",
    as_of="2026-09-01",
    question=(
        "Our own shop reworked a servo assembly and it failed a few months later. Can we still make "
        "Fairweather pay to put it right?"
    ),
    construction="evidence dependency",
    controlling=["atlas-sup-8-1", "atlas-sup-8-4"],
    supporting=[],
    inapplicable=[],
    distractor=["atlas-sup-8-2"],
    rationale=(
        "Section 8.1 grants the remedy and is expressly subject to Section 8.4, which removes "
        "Goods reworked by Buyer without written approval. The warranty period clause looks "
        "responsive and answers a different question."
    ),
    improvement="Follow the cross-reference from the operative clause to its exclusion.",
)
q(
    "atlas-substitution-approved",
    matter="atlas",
    as_of="2026-09-01",
    question=(
        "Are we cleared to build with the new 8841-C connector?"
    ),
    construction="authority versus repetition",
    controlling=["atlas-ecn-114", "atlas-sup-5-3"],
    supporting=[],
    inapplicable=["atlas-ecn-109"],
    distractor=[f"atlas-change-note-{n}" for n in range(1, 6)],
    rationale=(
        "The Engineering Change Notice records a conditional approval with both conditions "
        "still open, and Section 5.3 says a conditional approval takes effect only on written "
        "confirmation. Five program memos report the change as approved."
    ),
    improvement=(
        "Group by source family, and follow the reference from the memo to the record it "
        "cites."
    ),
)

BY_QUESTION = {x["question_id"]: x for x in QUESTIONS}


def covers(passage, as_of):
    """Applicability window, half open: effective_from <= as_of < effective_to."""
    return passage["effective_from"] <= as_of < passage["effective_to"]


def check(questions=None, expect=12, require_constructions=True):
    ids = set(BY_ID)
    for p in BY_ID.values():
        for r in p["references"]:
            assert r in ids, f"{p['passage_id']} references missing passage {r}"
        assert p["text"].strip() and p["heading"].strip(), p["passage_id"]

    questions = QUESTIONS if questions is None else questions
    assert len(questions) == expect, len(questions)
    assert len({x["question_id"] for x in questions}) == expect, "duplicate question id"

    for x in questions:
        named = x["controlling"] + x["supporting"] + x["inapplicable"] + x["distractor"]
        assert len(named) == len(set(named)), f"{x['question_id']}: passage named twice"
        assert x["controlling"], x["question_id"]
        for pid in named:
            assert pid in ids, f"{x['question_id']} names missing passage {pid}"
        for pid in x["controlling"] + x["supporting"]:
            p = BY_ID[pid]
            assert p["matter_id"] == x["matter_id"], f"{x['question_id']}: {pid} wrong matter"
            assert covers(p, x["as_of"]), f"{x['question_id']}: {pid} outside window"
        for pid in x["inapplicable"]:
            p = BY_ID[pid]
            assert p["matter_id"] != x["matter_id"] or not covers(p, x["as_of"]), (
                f"{x['question_id']}: {pid} is applicable and must not be listed inapplicable"
            )
        for pid in x["distractor"]:
            p = BY_ID[pid]
            assert p["matter_id"] == x["matter_id"] and covers(p, x["as_of"]), (
                f"{x['question_id']}: {pid} is out of scope, list it as inapplicable"
            )

    # Each matter carries all three constructions, and each construction is
    # reachable only by reading the text rather than by trusting one field.
    for matter in (MATTERS if require_constructions else {}):
        kinds = {x["construction"].split(",")[0] for x in questions if x["matter_id"] == matter}
        assert kinds == {
            "historical applicability",
            "evidence dependency",
            "authority versus repetition",
        }, (matter, kinds)

    # The historical questions must turn on a superseded passage, or the
    # status-filter bug has nothing to break.
    superseded = [
        x
        for x in questions
        if any(BY_ID[p]["status"] == "superseded" for p in x["controlling"])
    ]
    assert len(superseded) >= 3, [x["question_id"] for x in superseded]

    # The changeover questions must flip on an exclusive upper bound.
    lookup = {x["question_id"]: x for x in questions}
    for qid in [k for k in lookup if k.endswith("-boundary")]:
        x = lookup[qid]
        old = BY_ID[x["inapplicable"][0]]
        assert old["effective_to"] == x["as_of"], f"{qid}: boundary date does not match"

    # Three memo families are duplicated, so ranking must read the family rather
    # than the document id. At least one memo stands alone and carries a fact no
    # instrument records, so down-weighting memos as a class has to cost something.
    families = {}
    for p in BY_ID.values():
        if p["instrument_type"] == "memo":
            families.setdefault(p["source_family"], []).append(p["passage_id"])
    duplicated = [v for v in families.values() if len(v) >= 4]
    singletons = [v for v in families.values() if len(v) == 1]
    assert len(duplicated) == 3, families
    assert singletons, "no memo carries unique evidence; memo down-weighting is an exploit"

    return f"{len(BY_ID)} passages, {len(questions)} questions, all checks pass"


if __name__ == "__main__":
    print(check())
