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
    """Scope to this client, and to what was in force on the question date."""
    return models.Filter(
        must=[
            # Without this, another client's contracts answer the question.
            models.FieldCondition(
                key="matter_id", match=models.MatchValue(value=matter_id)
            ),
            # Not status: a superseded clause is the right answer to a question
            # dated while it was in force.
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
            limit=CANDIDATES,
        )
        for vector, model in (
            ("dense_weak", DENSE_MODEL),
            ("dense_context", DENSE_MODEL),
            ("bm25", SPARSE_MODEL),
        )
    ]
    groups = client.query_points_groups(
        collection,
        prefetch=prefetch,
        # Down-weight the lexical signal: these questions are asked in business
        # language and the clauses are written in contract language.
        query=models.RrfQuery(rrf=models.Rrf(weights=[2.0, 2.0, 1.0])),
        query_filter=query_filter,
        # One hit per source family, so five copies of one memo cannot fill
        # the result list.
        group_by="source_family",
        group_size=1,
        limit=limit,
        with_payload=True,
    ).groups
    return [hit for group in groups for hit in group.hits]
