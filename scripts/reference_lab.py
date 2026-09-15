"""Reference solution. Organizer copy, never shipped.

Every change here is reachable by editing lab.py alone, which is the point:
the measured ladder must be climbable through the permitted interface.
"""

from qdrant_client import models

DENSE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SPARSE_MODEL = "Qdrant/bm25"

CANDIDATES = 60
LIMIT = 5


def build_filter(matter_id, as_of):
    """Scope to this client, and to what was in effect on the question date."""
    return models.Filter(
        must=[
            # Without this, another client's contracts answer the question.
            models.FieldCondition(
                key="matter_id", match=models.MatchValue(value=matter_id)
            ),
            # Not status: a superseded clause is the right answer to a question
            # dated while it was in effect.
            models.FieldCondition(
                key="effective_from", range=models.DatetimeRange(lte=as_of)
            ),
            # Exclusive: a document whose window ends on the question date has
            # already been replaced by then.
            models.FieldCondition(
                key="effective_to", range=models.DatetimeRange(gt=as_of)
            ),
        ]
    )


def retrieve(client, collection, question, matter_id, as_of, limit=LIMIT):
    query_filter = build_filter(matter_id, as_of)
    prefetch = [
        models.Prefetch(
            query=models.Document(text=question, model=model),
            using=vector,
            filter=query_filter,
            # Qdrant 1.19 can compute BM25 rarity inside this client's matter
            # instead of across every client's documents in the shard.
            params=(
                models.SearchParams(
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
                if vector == "bm25"
                else None
            ),
            limit=CANDIDATES,
        )
        for vector, model in (
            ("minilm_l6_clause", DENSE_MODEL),
            ("minilm_l6_document", DENSE_MODEL),
            ("bm25", SPARSE_MODEL),
        )
    ]
    groups = client.query_points_groups(
        collection,
        prefetch=prefetch,
        # Unweighted. Weighting the dense signals up was worth one question
        # before the BM25 statistics were scoped to the matter, and costs three
        # after it: 92 unweighted against 89 at 2:2:1.
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        query_filter=query_filter,
        # One hit per source family, so five copies of one memo cannot fill
        # the result list.
        group_by="source_family",
        group_size=1,
        limit=limit,
        with_payload=True,
    ).groups
    return [hit for group in groups for hit in group.hits]
