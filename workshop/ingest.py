"""Create the Qdrant Cloud collection and load the corpus.

Organizer only. Every representation is embedded by Qdrant Cloud Inference, so
neither ingest nor query needs a local model.

The script probes each model before it builds points and loads only the ones
the cluster currently serves. A cluster without billing attached serves the
free models and refuses the paid ones, so a partial load is expected until the
upgrade lands. Re-run after the upgrade to fill the remaining vectors.

    uv run python -m workshop.ingest [--recreate]
"""

import os
import sys
import uuid
from qdrant_client import models
from .client import connect
from .clausebank import load as load_clause_bank
from .corpus import PASSAGES as FICTIONAL
from .vectors import MODELS, DENSE, SPARSE, COLBERT, embed_text

NAMESPACE = uuid.UUID("b1f0c0de-0000-4000-8000-000000000001")
BATCH = 32
PROBE_TEXT = "A written notice of default identifying the provision breached."


def document(name, text):
    return models.Document(text=text, model=MODELS[name][0])


def create(qc, collection, recreate):
    if qc.collection_exists(collection):
        if not recreate:
            return False
        qc.delete_collection(collection)
    dense = {
        name: models.VectorParams(size=MODELS[name][1], distance=models.Distance.COSINE)
        for name in DENSE
    }
    # The multivector is a rescorer over prefetched candidates, never a first
    # stage, so it needs no HNSW graph of its own. m=0 keeps it off disk index
    # build and off the critical path of every other query.
    dense[COLBERT] = models.VectorParams(
        size=MODELS[COLBERT][1],
        distance=models.Distance.COSINE,
        multivector_config=models.MultiVectorConfig(
            comparator=models.MultiVectorComparator.MAX_SIM
        ),
        hnsw_config=models.HnswConfigDiff(m=0),
        on_disk=True,
    )
    qc.create_collection(
        collection,
        vectors_config=dense,
        # IDF belongs on BM25, whose raw term counts carry no corpus weighting.
        # SPLADE already emits learned term weights, so adding IDF double counts.
        sparse_vectors_config={
            "bm25": models.SparseVectorParams(modifier=models.Modifier.IDF),
            "splade": models.SparseVectorParams(),
        },
    )
    for field, schema in [
        ("matter_id", models.PayloadSchemaType.KEYWORD),
        ("status", models.PayloadSchemaType.KEYWORD),
        ("instrument_type", models.PayloadSchemaType.KEYWORD),
        ("source_family", models.PayloadSchemaType.KEYWORD),
        ("document_id", models.PayloadSchemaType.KEYWORD),
        ("passage_id", models.PayloadSchemaType.KEYWORD),
        ("effective_from", models.PayloadSchemaType.DATETIME),
        ("effective_to", models.PayloadSchemaType.DATETIME),
        ("executed_on", models.PayloadSchemaType.DATETIME),
    ]:
        qc.create_payload_index(collection, field_name=field, field_schema=schema)
    return True


def served(qc, collection):
    """Return the vector names this cluster can currently embed."""
    ok, refused = [], {}
    for name in MODELS:
        try:
            qc.upsert(
                collection,
                points=[
                    models.PointStruct(
                        id=str(uuid.uuid5(NAMESPACE, "probe")),
                        vector={name: document(name, PROBE_TEXT)},
                    )
                ],
                wait=True,
            )
            ok.append(name)
        except Exception as exc:
            text = str(exc)
            refused[name] = (
                "not on the cluster model list"
                if "Unsupported model" in text
                else "needs billing on the cluster"
                if "Authentication failed" in text
                else text.replace("\n", " ")[:110]
            )
    qc.delete(
        collection,
        points_selector=models.PointIdsList(points=[str(uuid.uuid5(NAMESPACE, "probe"))]),
        wait=True,
    )
    return ok, refused


def load(qc, collection, names, passages):
    for start in range(0, len(passages), BATCH):
        chunk = passages[start : start + BATCH]
        qc.upsert(
            collection,
            points=[
                models.PointStruct(
                    id=str(uuid.uuid5(NAMESPACE, p["passage_id"])),
                    vector={n: document(n, embed_text(n, p)) for n in names},
                    payload=p,
                )
                for p in chunk
            ],
            wait=True,
        )
        print(f"  loaded {min(start + BATCH, len(passages))}/{len(passages)}", flush=True)


def main():
    collection = os.getenv("QDRANT_COLLECTION", "legal_lab_v1")
    qc = connect(write=True)
    fresh = create(qc, collection, "--recreate" in sys.argv)
    print(f"collection {collection}: {'created' if fresh else 'already exists'}")

    names, refused = served(qc, collection)
    for name in names:
        print(f"  serving  {name:13} {MODELS[name][0]}")
    for name, why in refused.items():
        print(f"  refused  {name:13} {MODELS[name][0]} :: {why}")
    if not names:
        sys.exit("No model is reachable. Check the cluster Inference tab.")

    passages = FICTIONAL + load_clause_bank()
    print(f"corpus: {len(FICTIONAL)} fictional + {len(passages) - len(FICTIONAL)} real clause-bank passages")
    load(qc, collection, names, passages)
    count = qc.count(collection, exact=True).count
    print(f"done: {count} points, vectors loaded: {', '.join(names)}")
    if refused:
        print(f"re-run after the upgrade to fill: {', '.join(refused)}")


if __name__ == "__main__":
    main()
