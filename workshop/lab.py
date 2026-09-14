"""THE ONE FILE YOU EDIT.

Everything else in this repository is fixed. Change this file, run

    uv run python -m workshop.run score

and watch the three numbers move.

The collection is read-only and preloaded. It holds the three fictional
matters this lab is about, and several hundred real public contracts that
belong to other clients. It may also hold more representations than this
starter code asks for; `run score` prints how many it uses against how many
are there.

Keep the signature of retrieve() exactly as it is. The scorer calls it.
"""

from qdrant_client import models

# Cloud Inference embeds the query server-side, so no model runs on your laptop.
DENSE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SPARSE_MODEL = "Qdrant/bm25"

CANDIDATES = 5
LIMIT = 5


def build_filter(matter_id, as_of):
    """Scope the search.

    You are given two facts about every question: which client matter it is
    about, and the date it is asked on. Both are yours to use here.
    """
    return models.Filter(
        must=[
            models.FieldCondition(
                key="status", match=models.MatchValue(value="operative")
            ),
            models.FieldCondition(
                key="effective_from", range=models.DatetimeRange(lte=as_of)
            ),
            models.FieldCondition(
                key="effective_to", range=models.DatetimeRange(gte=as_of)
            ),
        ]
    )


def retrieve(client, collection, question, matter_id, as_of, limit=LIMIT):
    """Return ranked passages for one dated question about one matter.

    Keep this signature. Return a list of ScoredPoint with payloads.
    """
    query_filter = build_filter(matter_id, as_of)
    dense = models.Document(text=question, model=DENSE_MODEL)
    sparse = models.Document(text=question, model=SPARSE_MODEL)

    return client.query_points(
        collection,
        prefetch=[
            models.Prefetch(query=dense, using="dense_weak",
                            filter=query_filter, limit=CANDIDATES),
            models.Prefetch(query=sparse, using="bm25",
                            filter=query_filter, limit=CANDIDATES),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
    ).points
