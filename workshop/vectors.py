"""Vector names and the Cloud Inference models behind them.

One place, imported by the ingest and by the query layer, so a participant
reads the same names in the editable file that the collection actually holds.
"""

DENSE_WEAK = "dense_weak"
DENSE_CONTEXT = "dense_context"
DENSE_STRONG = "dense_strong"
BM25 = "bm25"
SPLADE = "splade"
COLBERT = "colbert"

# Cloud Inference model identifiers, and the dimension each one returns.
MODELS = {
    # Same model, different content. dense_weak sees the clause body alone;
    # dense_context also sees which document and which heading it sits under.
    DENSE_WEAK: ("sentence-transformers/all-MiniLM-L6-v2", 384),
    DENSE_CONTEXT: ("sentence-transformers/all-MiniLM-L6-v2", 384),
    DENSE_STRONG: ("mixedbread-ai/mxbai-embed-large-v1", 1024),
    BM25: ("Qdrant/bm25", None),
    SPLADE: ("prithivida/Splade_PP_en_v1", None),
    COLBERT: ("answerdotai/answerai-colbert-small-v1", 96),
}

DENSE = (DENSE_WEAK, DENSE_CONTEXT, DENSE_STRONG)
SPARSE = (BM25, SPLADE)


def embed_text(name, passage):
    """What each representation is built from at ingest time."""
    if name == DENSE_CONTEXT:
        return f"{passage['document_title']}. {passage['heading']}. {passage['text']}"
    return passage["text"]
