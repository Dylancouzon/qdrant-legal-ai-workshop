"""Vector names and the Cloud Inference models behind them.

One place, imported by the ingest and by the query layer, so a participant
reads the same names in the editable file that the collection actually holds.

A name states the model and what was embedded, and nothing else. An earlier
naming, `dense_weak` and `dense_strong`, ranked the representations in the
schema: a participant read "strong" and switched to it without measuring, which
is the one habit this workshop exists to break. Whether a representation helps
this corpus is a measurement, and `bench` is where it is made.
"""

MINILM_CLAUSE = "minilm_l6_clause"
MINILM_DOCUMENT = "minilm_l6_document"
MXBAI_LARGE = "mxbai_large_v1"
BM25 = "bm25"
SPLADE = "splade_pp_v1"
COLBERT = "colbert_small_v1"

# Cloud Inference model identifiers, and the dimension each one returns.
MODELS = {
    # Same model, different content. MINILM_CLAUSE sees the clause body alone;
    # MINILM_DOCUMENT also sees which document and which heading it sits under.
    MINILM_CLAUSE: ("sentence-transformers/all-MiniLM-L6-v2", 384),
    MINILM_DOCUMENT: ("sentence-transformers/all-MiniLM-L6-v2", 384),
    MXBAI_LARGE: ("mixedbread-ai/mxbai-embed-large-v1", 1024),
    BM25: ("Qdrant/bm25", None),
    SPLADE: ("prithivida/Splade_PP_en_v1", None),
    COLBERT: ("answerdotai/answerai-colbert-small-v1", 96),
}

DENSE = (MINILM_CLAUSE, MINILM_DOCUMENT, MXBAI_LARGE)
SPARSE = (BM25, SPLADE)


def embed_text(name, chunk):
    """What each representation is built from at ingest time."""
    if name == MINILM_DOCUMENT:
        return f"{chunk['document_title']}. {chunk['heading']}. {chunk['text']}"
    return chunk["text"]
