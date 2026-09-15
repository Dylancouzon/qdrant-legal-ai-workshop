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
            # Keep every search inside the client's matter.
            models.FieldCondition(
                key="matter_id",
                match=models.MatchValue(value=matter_id),
            ),
            # A superseded clause can still govern a historical question, so
            # filter on its effective window rather than its current status.
            models.FieldCondition(
                key="effective_from",
                range=models.DatetimeRange(lte=as_of),
            ),
            models.FieldCondition(
                key="effective_to",
                range=models.DatetimeRange(gt=as_of),
            ),
        ]
    )


def retrieve(client, collection, question, matter_id, as_of, limit=LIMIT):
    query_filter = build_filter(matter_id, as_of)

    # Compute BM25 rarity inside this matter, not across every client.
    bm25_params = models.SearchParams(
        idf=models.IdfCorpusParams(
            corpus=models.Filter(
                must=[
                    models.FieldCondition(
                        key="matter_id",
                        match=models.MatchValue(value=matter_id),
                    )
                ]
            )
        )
    )

    # Each prefetch retrieves candidates from one named vector. Qdrant fuses
    # the three ranked lists in the outer query below.
    prefetch = [
        models.Prefetch(
            query=models.Document(text=question, model=DENSE_MODEL),
            using="minilm_l6_clause",
            filter=query_filter,
            limit=CANDIDATES,
        ),
        models.Prefetch(
            query=models.Document(text=question, model=DENSE_MODEL),
            using="minilm_l6_document",
            filter=query_filter,
            limit=CANDIDATES,
        ),
        models.Prefetch(
            query=models.Document(text=question, model=SPARSE_MODEL),
            using="bm25",
            filter=query_filter,
            params=bm25_params,
            limit=CANDIDATES,
        ),
    ]

    groups = client.query_points_groups(
        collection,
        prefetch=prefetch,
        # The document-context vector contributes one answer the other signals
        # miss, but it is a weaker clause ranker, so it gets less weight.
        query=models.RrfQuery(rrf=models.Rrf(weights=[1.0, 0.25, 1.0])),
        query_filter=query_filter,
        # Return at most one copy from each source family.
        group_by="source_family",
        group_size=1,
        limit=limit,
        with_payload=True,
    ).groups
    hits = [hit for group in groups for hit in group.hits]

    # Fetch definitions and exceptions referenced by the retrieved clauses.
    retrieved_ids = {hit.payload["passage_id"] for hit in hits}
    missing_references = []
    for hit in hits:
        for passage_id in hit.payload["references"]:
            if passage_id not in retrieved_ids:
                missing_references.append(passage_id)
    if not missing_references:
        return hits[:limit]

    # Apply the same matter and date rules to reference lookups.
    reference_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="passage_id",
                match=models.MatchAny(any=missing_references),
            ),
            models.FieldCondition(
                key="matter_id",
                match=models.MatchValue(value=matter_id),
            ),
            models.FieldCondition(
                key="effective_from",
                range=models.DatetimeRange(lte=as_of),
            ),
            models.FieldCondition(
                key="effective_to",
                range=models.DatetimeRange(gt=as_of),
            ),
        ]
    )
    referenced, _ = client.scroll(
        collection,
        scroll_filter=reference_filter,
        limit=len(missing_references),
        with_payload=True,
    )

    # Place each referenced clause directly after the clause that cites it.
    referenced_by_id = {
        point.payload["passage_id"]: point for point in referenced
    }
    ordered = []
    for hit in hits:
        ordered.append(hit)
        for passage_id in hit.payload["references"]:
            reference = referenced_by_id.pop(passage_id, None)
            if reference is not None:
                ordered.append(reference)

    return ordered[:limit]
