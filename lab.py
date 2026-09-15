"""THE WORKED SOLUTION. Organizer copy, never shipped.

Participants receive `scripts/starter_lab.py` as their `lab.py`. This file is
where that one ends up, and every comment below marks one change and what it
was worth. Measured on the fourteen-case board: the starter reads 9 to 13, this
reads 78 to 81 with every visible failure at zero and 11 or 12 of 14 solved.
The spread is one case whose last two chunks score equally and swap, which is
the same approximate-search tie the starter shows more loudly.

The two it does not solve are the challenge cases, and they stay shut for a
reason: the only chunk pointing at the answer to the cure question was replaced
before the question date, so a correct date filter removes it.

    uv run python -m workshop.run score
"""

from qdrant_client import models

DENSE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SPARSE_MODEL = "Qdrant/bm25"

# Five candidates per branch left nothing for fusion to fuse. Sixty is worth two
# points, and worth nothing at all until the BM25 statistics are scoped below.
CANDIDATES = 60
LIMIT = 5


def build_filter(matter_id, as_of):
    return models.Filter(
        must=[
            # The largest single change, worth 64 points: without it another
            # client's contracts answer the question, which is the confidentiality
            # failure the whole exercise is built around.
            models.FieldCondition(
                key="matter_id", match=models.MatchValue(value=matter_id)
            ),
            # The starter filtered status == "operative", which reads as obviously
            # correct and throws away every historical answer. Dropping it is
            # worth 15 points and six questions.
            models.FieldCondition(
                key="effective_from", range=models.DatetimeRange(lte=as_of)
            ),
            # gt, not gte: a clause replaced on 1 April does not govern on 1 April.
            # Worth two points, and it clears three chunks that were not in effect.
            models.FieldCondition(
                key="effective_to", range=models.DatetimeRange(gt=as_of)
            ),
        ]
    )


def retrieve(client, collection, question, matter_id, as_of, limit=LIMIT):
    query_filter = build_filter(matter_id, as_of)

    # Qdrant 1.19 computes BM25 rarity inside this client's matter instead of
    # across every client in the shard. Worth four points and three questions.
    idf = models.SearchParams(
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

    prefetch = [
        models.Prefetch(
            query=models.Document(text=question, model=model),
            using=vector,
            filter=query_filter,
            params=idf if vector == "bm25" else None,
            limit=CANDIDATES,
        )
        # The second dense vector is the same model over the document title and
        # heading as well as the clause. What you embed is a larger lever than
        # which model you use, and it solves a question nothing else reaches.
        for vector, model in (
            ("minilm_l6_clause", DENSE_MODEL),
            ("minilm_l6_document", DENSE_MODEL),
            ("bm25", SPARSE_MODEL),
        )
    ]

    groups = client.query_points_groups(
        collection,
        prefetch=prefetch,
        # The document-context vector contributes one answer the other signals
        # miss, but it is a weaker clause ranker. A quarter-weight keeps that
        # recall gain while lifting ranking on both the calibration and held-out
        # questions. Clause-level MiniLM and matter-scoped BM25 remain peers.
        query=models.RrfQuery(rrf=models.Rrf(weights=[1.0, 0.25, 1.0])),
        query_filter=query_filter,
        # One hit per source family, so five forwarded copies of one memo cannot
        # fill the list. Worth six points and two questions.
        group_by="source_family",
        group_size=1,
        limit=limit,
        with_payload=True,
    ).groups
    hits = [hit for group in groups for hit in group.hits]

    # A clause that is expressly subject to a definition or an exclusion is half
    # an answer, and no ranking change ever retrieves the other half. The payload
    # names it, so fetch it: worth four to seven points and two dependency questions.
    have = {hit.payload["passage_id"] for hit in hits}
    wanted = [r for hit in hits for r in hit.payload["references"] if r not in have]
    if not wanted:
        return hits[:limit]

    # scroll, because this is a lookup by id with no query vector. Same filter
    # as the search: a referenced clause that was not in effect on the question
    # date is still a chunk a lawyer cannot use.
    referenced, _ = client.scroll(
        collection,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="passage_id", match=models.MatchAny(any=wanted)
                ),
                *query_filter.must,
            ]
        ),
        limit=len(wanted),
        with_payload=True,
    )

    # Each referenced clause sits directly behind the clause that points at it,
    # so the pair reads as one answer and the weakest results fall off the end.
    by_id = {point.payload["passage_id"]: point for point in referenced}
    ordered = []
    for hit in hits:
        ordered.append(hit)
        for ref in hit.payload["references"]:
            if ref in by_id:
                ordered.append(by_id.pop(ref))
    return ordered[:limit]
