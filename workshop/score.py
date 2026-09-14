"""The three published dimensions, scored against the rubric in validation.py.

coverage       Share of the controlling passages that were retrieved. Two
               controlling passages means retrieving one earns one half.
ranking        NDCG over graded results. A source family contributes once, so
               the second and later copies of a memo take a rank slot and earn
               nothing.

Rank on coverage first and ranking second, as the brief sets out. Applicability
is reported as three counts rather than one average, because an average of
1.000 hid the concrete failures a reader can see in the result list.
"""

import math

K = 5
GRADE = {"controlling": 3.0, "supporting": 1.0}


def grades(question):
    out = {pid: GRADE["controlling"] for pid in question["controlling"]}
    out.update({pid: GRADE["supporting"] for pid in question["supporting"]})
    return out


def applicable(passage, question):
    return (
        passage["matter_id"] == question["matter_id"]
        and passage["effective_from"] <= question["as_of"] < passage["effective_to"]
    )


def _dcg(gains):
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


def score(question, passages, k=K):
    """Score one ranked list of returned payloads against one validation question.

    Payloads, not ids, so the scorer grades what the system actually returned
    and never needs to look anything up in the corpus.
    """
    ranked = list(passages)[:k]
    table = grades(question)

    seen_families = set()
    gains = []
    duplicate_families = 0
    for payload in ranked:
        family = payload["source_family"]
        gain = table.get(payload["passage_id"], 0.0)
        if family in seen_families:
            gain = 0.0  # repetition is not corroboration
            duplicate_families += 1
        seen_families.add(family)
        gains.append(gain)

    ideal = sorted(table.values(), reverse=True)[:k]
    ranking = _dcg(gains) / _dcg(ideal) if ideal else 0.0

    found = {p["passage_id"] for p in ranked} & set(question["controlling"])
    coverage = len(found) / len(question["controlling"])

    # Counts a person can see in the result list, rather than an average that
    # hides them. A leak is another client's document. A temporal violation is
    # this client's document outside its effective window on the question date.
    leaks = [p["passage_id"] for p in ranked if p["matter_id"] != question["matter_id"]]
    stale = [
        p["passage_id"]
        for p in ranked
        if p["matter_id"] == question["matter_id"] and not applicable(p, question)
    ]

    return {
        "question_id": question["question_id"],
        "coverage": coverage,
        "ranking": ranking,
        "tenant_leaks": len(leaks),
        "temporal_violations": len(stale),
        "duplicate_families": duplicate_families,
        "missing": sorted(set(question["controlling"]) - found),
        "inapplicable": leaks + stale,
        "returned": [p["passage_id"] for p in ranked],
    }


def score_all(questions, retrieve, k=K):
    """retrieve(question, matter_id, as_of) must return ranked payload dicts."""
    rows = [
        score(x, retrieve(x["question"], x["matter_id"], x["as_of"]), k)
        for x in questions
    ]
    mean = lambda key: sum(r[key] for r in rows) / len(rows)
    total = lambda key: sum(r[key] for r in rows)
    return {
        "coverage": mean("coverage"),
        "ranking": mean("ranking"),
        "solved": sum(1 for r in rows if r["coverage"] == 1.0),
        "questions": len(rows),
        "tenant_leaks": total("tenant_leaks"),
        "temporal_violations": total("temporal_violations"),
        "duplicate_families": total("duplicate_families"),
        "rows": rows,
    }


def demo():
    """Self-check: the rubric must reward the right list and punish the traps."""
    from .validation import BY_QUESTION
    from .corpus import BY_ID

    ids = lambda *names: [BY_ID[n] for n in names]
    x = BY_QUESTION["harbor-retention"]
    memos = [f"harbor-retention-note-{n}" for n in range(1, 6)]

    perfect = score(x, ids("harbor-exh-d2", *memos))
    assert perfect["coverage"] == 1.0 and perfect["ranking"] == 1.0, perfect
    assert perfect["tenant_leaks"] == 0 and perfect["temporal_violations"] == 0, perfect

    # Same six passages, instrument last: coverage holds, ranking drops.
    late = score(x, ids(*memos, "harbor-exh-d2"), k=6)
    assert late["coverage"] == 1.0 and late["ranking"] < 0.5, late

    # Repetition must not pay. Five memo copies score as one distractor.
    assert score(x, ids(*memos))["ranking"] == 0.0

    # Two controlling passages, one retrieved, is half coverage.
    dep = BY_QUESTION["harbor-liability-cap"]
    assert score(dep, ids("harbor-msa-13-1"))["coverage"] == 0.5

    # Applicability reads the window, not the status field. The superseded
    # clause is the right answer here and must not be penalised.
    # Leaks and stale hits are counted, not averaged away.
    leak = score(x, ids("harbor-exh-d2", "cedar-cure"))
    assert leak["tenant_leaks"] == 1 and leak["temporal_violations"] == 0, leak
    assert score(x, ids("harbor-exh-d2", *memos))["duplicate_families"] == 3

    hist = BY_QUESTION["harbor-cure-before"]
    assert score(hist, ids("harbor-cure"))["temporal_violations"] == 0
    assert score(hist, ids("harbor-am3-2"))["temporal_violations"] == 1
    assert score(hist, ids("harbor-cure", "cedar-cure"))["tenant_leaks"] == 1

    return "score.py self-check passed"


if __name__ == "__main__":
    print(demo())
