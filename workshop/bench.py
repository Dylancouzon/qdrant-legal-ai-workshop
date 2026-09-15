"""Organizer bench. Measure wide, and keep every result.

Nothing counts as a lever until it shows up here, and nothing measured is
thrown away: every run appends to experiments.jsonl so a configuration we
rejected in September can be re-read in October without re-running it.

    uv run python -m workshop.bench              # run the whole grid
    uv run python -m workshop.bench --only rrf   # run matching rows only
    uv run python -m workshop.bench --report     # best results from the log
"""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from qdrant_client import models
from .client import collection, connect, lab
from .questions import HEADROOM, SCORED as QUESTIONS
from .score import case_score, score_all
from .vectors import MODELS, MINILM_CLAUSE, MINILM_DOCUMENT, BM25 as BM25_NAME, SPLADE, COLBERT as COLBERT_NAME
LOG = Path(__file__).resolve().parents[1] / "experiments.jsonl"
K = 5


def provenance(qc, name):
    """Everything needed to know what a logged number was measured against."""
    import importlib.metadata as meta

    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        sha = None
    info = qc.get_collection(name)
    digest = hashlib.sha256(
        json.dumps([q["question_id"] for q in QUESTIONS], sort_keys=True).encode()
    ).hexdigest()[:12]
    return {
        "git_sha": sha,
        "question_set": digest,
        "question_count": len(QUESTIONS),
        "collection": name,
        "points": qc.count(name, exact=True).count,
        "vectors": sorted(
            set(info.config.params.vectors or {}) | set(info.config.params.sparse_vectors or {})
        ),
        "qdrant_client": meta.version("qdrant-client"),
    }

DENSE = MODELS[MINILM_CLAUSE][0]
BM25 = MODELS[BM25_NAME][0]
COLBERT = MODELS[COLBERT_NAME][0]

BASE = dict(
    matter=True,
    status_filter=False,
    dated=True,
    exclusive_end=True,
    signals=(MINILM_CLAUSE, BM25_NAME),
    fusion="rrf",
    rrf_k=None,
    weights=None,
    group="source_family",
    colbert=False,
    mmr=None,
    tenant_idf=False,
    candidates=60,
    limit=None,
)


def model_for(signal):
    return BM25 if signal in (BM25_NAME, SPLADE) else DENSE


def scope(matter_id, as_of, o):
    must = []
    if o["matter"]:
        must.append(
            models.FieldCondition(key="matter_id", match=models.MatchValue(value=matter_id))
        )
    if o["status_filter"]:
        must.append(
            models.FieldCondition(key="status", match=models.MatchValue(value="operative"))
        )
    if o["dated"]:
        must.append(
            models.FieldCondition(key="effective_from", range=models.DatetimeRange(lte=as_of))
        )
        end = {"gt": as_of} if o["exclusive_end"] else {"gte": as_of}
        must.append(
            models.FieldCondition(key="effective_to", range=models.DatetimeRange(**end))
        )
    return models.Filter(must=must)


def fusion_query(o):
    if o["fusion"] == "dbsf":
        return models.FusionQuery(fusion=models.Fusion.DBSF)
    if o["rrf_k"] is not None or o["weights"] is not None:
        return models.RrfQuery(rrf=models.Rrf(k=o["rrf_k"], weights=o["weights"]))
    return models.FusionQuery(fusion=models.Fusion.RRF)


def build(qc, name, **overrides):
    o = dict(BASE, **overrides)

    def run(question, matter_id, as_of):
        flt = scope(matter_id, as_of, o)
        tenant_corpus = models.SearchParams(
            idf=models.IdfCorpusParams(
                corpus=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="matter_id", match=models.MatchValue(value=matter_id)
                        )
                    ]
                )
            )
        )
        pre = [
            models.Prefetch(
                query=models.Document(text=question, model=model_for(s)),
                using=s,
                filter=flt,
                params=tenant_corpus if o["tenant_idf"] and s == BM25_NAME else None,
                limit=o["candidates"],
            )
            for s in o["signals"]
        ]
        if o["colbert"]:
            main = dict(
                prefetch=pre,
                query=models.Document(text=question, model=COLBERT),
                using=COLBERT_NAME,
            )
        elif o["mmr"] is not None:
            main = dict(
                prefetch=pre,
                using=o["signals"][0],
                query=models.NearestQuery(
                    nearest=models.Document(text=question, model=DENSE),
                    mmr=models.Mmr(diversity=o["mmr"], candidates_limit=o["candidates"]),
                ),
            )
        elif len(o["signals"]) == 1:
            main = dict(query=pre[0].query, using=o["signals"][0])
        else:
            main = dict(prefetch=pre, query=fusion_query(o))

        limit = o["limit"] or K
        if o["group"]:
            groups = qc.query_points_groups(
                name, group_by=o["group"], group_size=1, limit=limit,
                query_filter=flt, with_payload=True, **main
            ).groups
            return [h.payload for g in groups for h in g.hits]
        return [
            p.payload
            for p in qc.query_points(
                name, query_filter=flt, limit=limit, with_payload=True, **main
            ).points
        ]

    return run, o


# label, overrides, why it is in the grid
GRID = [
    ("correct baseline", {}, "reference"),
    # Filters: the planted defects, one at a time.
    ("BUG starter as shipped", dict(matter=False, status_filter=True, exclusive_end=False,
                                    candidates=5, group=None), "defect"),
    ("BUG no matter filter", dict(matter=False), "defect"),
    ("BUG status==operative", dict(status_filter=True), "defect"),
    ("BUG inclusive end date", dict(exclusive_end=False), "defect"),
    ("BUG no date filter", dict(dated=False), "defect"),
    # Which representation to query.
    ("minilm clause alone", dict(signals=(MINILM_CLAUSE,)), "signal"),
    ("minilm document alone", dict(signals=(MINILM_DOCUMENT,)), "signal"),
    ("bm25 alone", dict(signals=(BM25_NAME,)), "signal"),
    ("clause + bm25", dict(signals=(MINILM_CLAUSE, BM25_NAME)), "signal"),
    ("document + bm25", dict(signals=(MINILM_DOCUMENT, BM25_NAME)), "signal"),
    ("clause + document", dict(signals=(MINILM_CLAUSE, MINILM_DOCUMENT)), "signal"),
    ("clause + document + bm25", dict(signals=(MINILM_CLAUSE, MINILM_DOCUMENT, BM25_NAME)), "signal"),
    # Fusion.
    ("fusion DBSF", dict(fusion="dbsf"), "fusion"),
    ("rrf k=4", dict(rrf_k=4), "fusion"),
    ("rrf k=10", dict(rrf_k=10), "fusion"),
    ("rrf k=20", dict(rrf_k=20), "fusion"),
    ("rrf k=200", dict(rrf_k=200), "fusion"),
    ("weights dense 3 : bm25 1", dict(weights=[3.0, 1.0]), "fusion"),
    ("weights dense 1 : bm25 3", dict(weights=[1.0, 3.0]), "fusion"),
    ("weights dense 5 : bm25 1", dict(weights=[5.0, 1.0]), "fusion"),
    ("weights dense 1 : bm25 5", dict(weights=[1.0, 5.0]), "fusion"),
    # Qdrant 1.19 can compute BM25 rarity within one tenant instead of across
    # the whole shard. This collection models a legal matter as the tenant.
    ("tenant-scoped BM25 IDF", dict(tenant_idf=True), "sparse"),
    # Grouping.
    ("no grouping", dict(group=None), "grouping"),
    ("group by document_id", dict(group="document_id"), "grouping"),
    # Reranking.
    ("colbert rescore", dict(colbert=True), "rerank"),
    ("colbert, no grouping", dict(colbert=True, group=None), "rerank"),
    ("mmr diversity 0.2", dict(mmr=0.2, group=None), "rerank"),
    ("mmr diversity 0.5", dict(mmr=0.5, group=None), "rerank"),
    ("mmr diversity 0.8", dict(mmr=0.8, group=None), "rerank"),
    # Candidate depth.
    ("candidates 10", dict(candidates=10), "depth"),
    ("candidates 20", dict(candidates=20), "depth"),
    ("candidates 150", dict(candidates=150), "depth"),
    # Promising combinations.
    ("weak+bm25, k=10, group", dict(rrf_k=10), "combo"),
    ("3-way, k=10, group", dict(signals=(MINILM_CLAUSE, MINILM_DOCUMENT, BM25_NAME), rrf_k=10), "combo"),
    ("3-way, weights 2:2:1", dict(signals=(MINILM_CLAUSE, MINILM_DOCUMENT, BM25_NAME),
                                  weights=[2.0, 2.0, 1.0]), "combo"),
    ("3-way weighted + tenant IDF", dict(signals=(MINILM_CLAUSE, MINILM_DOCUMENT, BM25_NAME),
                                           weights=[2.0, 2.0, 1.0], tenant_idf=True), "combo"),
    # The cumulative path a participant would actually walk. Each row adds one
    # change to the row above it.
    ("LADDER 0 starter", dict(matter=False, status_filter=True, exclusive_end=False,
                              candidates=5, group=None), "ladder"),
    ("LADDER 1 matter filter", dict(status_filter=True, exclusive_end=False,
                                    candidates=5, group=None), "ladder"),
    ("LADDER 2 drop status", dict(exclusive_end=False, candidates=5, group=None), "ladder"),
    ("LADDER 3 exclusive end", dict(candidates=5, group=None), "ladder"),
    ("LADDER 4 deeper pool", dict(candidates=60, group=None), "ladder"),
    ("LADDER 5 group by family", dict(candidates=60), "ladder"),
    ("LADDER 6 add document vector", dict(signals=(MINILM_CLAUSE, MINILM_DOCUMENT, BM25_NAME)), "ladder"),
    ("LADDER 7 tune weights 2:2:1", dict(signals=(MINILM_CLAUSE, MINILM_DOCUMENT, BM25_NAME),
                                         weights=[2.0, 2.0, 1.0]), "ladder"),
]

HEADER = f"{'variant':30} {'score':>5} {'cover':>6} {'rank':>6} {'solved':>7} {'leak':>5} {'stale':>6} {'dup':>4}"


def row(label, result):
    # score_all always sets "score". Reading it through a default that called
    # total() crashed every grid row, because main() pops "rows" before this.
    return (
        f"{label:30} {result['score']:5} "
        f"{result['coverage']:6.3f} {result['ranking']:6.3f} "
        f"{result['solved']:4}/{result['questions']:<2} {result['tenant_leaks']:5} "
        f"{result['temporal_violations']:6} {result['duplicate_families']:4}"
    )


def report():
    if not LOG.exists():
        sys.exit("no experiments.jsonl yet")
    best = {}
    for line in LOG.read_text().splitlines():
        entry = json.loads(line)
        best[entry["label"]] = entry
    print(HEADER + "   measured")
    print("-" * 84)
    for entry in sorted(best.values(), key=lambda e: (-e["solved"], -e["coverage"])):
        stamp = entry.get("run_at", "")[:16].replace("T", " ")
        n = entry.get("questions")
        print(row(entry["label"], entry) + f"   {stamp} n={n}")


def parity():
    """Prove the bench measures what editing lab.py produces.

    The starter rung is defined twice: once as bench options, once as the file
    participants receive. If those two ever diverge, every number in the log is
    a claim about code nobody runs.
    """
    # The starter, which is what ship.py hands participants.
    current = lab(Path(__file__).resolve().parents[1] / "scripts/starter_lab.py")
    qc, name = connect(write=True), collection()
    # Compare at depth 20. At depth 5 the cut lands inside a run of equally
    # scored chunks, so which one survives is arbitrary and tells us nothing
    # about whether the two queries are the same query.
    depth = 20
    run, _ = build(qc, name, matter=False, status_filter=True, exclusive_end=False,
                   candidates=5, group=None, limit=depth)
    # Compare sets, not order. Equal RRF scores are common and Qdrant does not
    # promise a stable order among them, so the same query run twice can swap
    # two tied chunks. That moves the ranking tiebreaker by about 0.013 and
    # never moves the solved count. A different SET is a real defect.
    bad, churn = [], 0
    for x in QUESTIONS:
        theirs = [
            p.payload["passage_id"]
            for p in current.retrieve(qc, name, x["question"], x["matter_id"], x["as_of"], limit=depth)
        ]
        ours = [p["passage_id"] for p in run(x["question"], x["matter_id"], x["as_of"])]
        if set(theirs) != set(ours):
            bad.append((x["question_id"], theirs, ours))
        elif theirs != ours:
            churn += 1
    for qid, theirs, ours in bad:
        print(f"MISMATCH {qid}\n  lab.py: {theirs}\n  bench : {ours}")
    print(f"parity at depth {depth}: {len(QUESTIONS) - len(bad)}/{len(QUESTIONS)} "
          f"return the same chunks")
    print(f"        {churn} differ only in the order of equally scored chunks")
    if bad:
        sys.exit("bench does not measure the shipped query; fix before trusting the log")


BEST = dict(
    signals=(MINILM_CLAUSE, MINILM_DOCUMENT, BM25_NAME),
    tenant_idf=True,
    weights=None,
    candidates=60,
    group="source_family",
)

# Each lever, and the configuration that switches only that lever off.
LEVERS = [
    ("filter by matter", dict(matter=False)),
    ("filter on the effective dates", dict(dated=False)),
    ("stop filtering on status", dict(status_filter=True)),
    ("group by source family", dict(group=None)),
    ("scope BM25 statistics to the matter", dict(tenant_idf=False)),
    ("treat the end date as exclusive", dict(exclusive_end=False)),
    ("add the document-context vector", dict(signals=(MINILM_CLAUSE, BM25_NAME))),
    ("raise the candidate pool to 60", dict(candidates=5)),
]

# Off in the best configuration. Measured by switching them on, so the number
# printed is what they cost rather than what they are worth.
REJECTED = [
    ("weight the fusion 2:2:1", dict(weights=(2, 2, 1))),
    ("weight the fusion 1:1:3", dict(weights=(1, 1, 3))),
    ("rescore with ColBERT", dict(colbert=True)),
    ("diversify with MMR", dict(mmr=0.3)),
]


def levers():
    """What each lever is worth with every other lever switched on.

    A cumulative ladder hides a lever that only pays once the rest is on, and
    the order it is tested in decides its apparent value. This does not.
    Re-run it after any question edit.
    """
    qc, name = connect(write=True), collection()
    # Exact means, not the rounded score: a lever worth part of a point is not
    # worth zero, and two rounded scores subtracted would say it is.
    exact = lambda result: sum(case_score(row) for row in result["rows"]) / len(result["rows"])
    run, _ = build(qc, name, **BEST)
    best = score_all(QUESTIONS, run, k=K)
    best_exact = exact(best)
    reference = {r["question_id"]: r["coverage"] for r in best["rows"]}
    print(f"best configuration: score {best['score']} ({best_exact:.1f} exact), "
          f"{best['solved']}/{best['questions']} solved, every visible failure at zero\n")
    print(f"{'lever':36} {'worth':>5} {'solved':>7}  questions it alone solves")
    print("-" * 96)
    for label, off in LEVERS:
        run, _ = build(qc, name, **dict(BEST, **off))
        result = score_all(QUESTIONS, run, k=K)
        lost = sorted(q for q, cover in reference.items()
                      if result["rows"] and cover > next(
                          r["coverage"] for r in result["rows"] if r["question_id"] == q))
        print(f"{label:36} {best_exact - exact(result):6.1f} pts {result['solved']:4}/"
              f"{result['questions']:<2}  {', '.join(lost) if lost else 'none, it removes visible failures only'}")

    print(f"\n{'measured and rejected':36} {'costs':>5} {'solved':>7}")
    print("-" * 60)
    for label, on in REJECTED:
        run, _ = build(qc, name, **dict(BEST, **on))
        result = score_all(QUESTIONS, run, k=K)
        print(f"{label:36} {best_exact - exact(result):6.1f} pts {result['solved']:4}/"
              f"{result['questions']:<2}")


def main():
    if "--report" in sys.argv:
        return report()
    if "--levers" in sys.argv:
        return levers()
    if "--parity" in sys.argv:
        return parity()
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]

    qc, name = connect(write=True), collection()
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    prov = provenance(qc, name)
    results = []
    print(HEADER)
    print("-" * 70)
    with LOG.open("a") as log:
        for label, overrides, kind in GRID:
            if only and only not in label:
                continue
            run, opts = build(qc, name, **overrides)
            result = score_all(QUESTIONS, run, k=K)
            rows = result.pop("rows")
            entry = dict(
                run_at=stamp, label=label, kind=kind, k=K,
                questions=result["questions"], provenance=prov,
                options={
                    key: list(value) if isinstance(value, tuple) else value
                    for key, value in opts.items()
                },
                per_question={
                    r["question_id"]: {
                        "coverage": round(r["coverage"], 4),
                        "ranking": round(r["ranking"], 4),
                        "returned": r["returned"],
                        "missing": r["missing"],
                    }
                    for r in rows
                },
                **{key: value for key, value in result.items() if key != "questions"},
            )
            log.write(json.dumps(entry) + "\n")
            log.flush()
            results.append((label, result))
            print(row(label, result))

    print(f"\nscored over {len(QUESTIONS)} reachable questions; "
          f"{len(HEADROOM)} headroom questions are excluded from every number above")
    print("\nranked by questions solved")
    print("-" * 70)
    for label, result in sorted(results, key=lambda x: (-x[1]["solved"], -x[1]["coverage"]))[:8]:
        print(row(label, result))
    print(f"\nlogged {len(results)} configurations to {LOG.name}")


if __name__ == "__main__":
    main()
