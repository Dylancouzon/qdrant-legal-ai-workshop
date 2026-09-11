"""Real Qdrant retrieval. Dense FastEmbed + corpus TF-IDF sparse vectors."""

import hashlib
import json
import math
import os
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from qdrant_client import QdrantClient, models
from fastembed import TextEmbedding
from .data import MATTERS, PASSAGES, VERSION

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".workshop"
COLLECTION = os.getenv("QDRANT_COLLECTION", "fix_the_search_v2")
MODEL = "BAAI/bge-small-en-v1.5"
TOP_K = 4
MAX_CONTEXT = 10
CANDIDATE_LIMIT = 8
CORPUS_HASH = hashlib.sha256(json.dumps(PASSAGES, sort_keys=True).encode()).hexdigest()
PROVENANCE = {
    "version": VERSION,
    "corpus_hash": CORPUS_HASH,
    "model": MODEL,
    "sparse": "tfidf-v1-compound-tokenizer",
    "top_k": TOP_K,
    "candidate_limit": CANDIDATE_LIMIT,
}
BASELINE = {
    "SEARCH_MODE": "dense",
    "FOLLOW_REFERENCES": False,
    "CHECK_VERSIONS": False,
    "SEEK_COUNTEREVIDENCE": False,
    "DEDUPLICATE": False,
}
AUTHORITY = dict(BASELINE, SEARCH_MODE="hybrid", FOLLOW_REFERENCES=True)
FRESHNESS = dict(AUTHORITY, CHECK_VERSIONS=True)
SOLUTION = dict(FRESHNESS, SEEK_COUNTEREVIDENCE=True, DEDUPLICATE=True)
CHECKPOINTS = {
    "baseline": BASELINE,
    "authority": AUTHORITY,
    "freshness": FRESHNESS,
    "solution": SOLUTION,
}


def config():
    namespace = {}
    path = ROOT / "workshop/retrieval.py"
    exec(compile(path.read_text(), str(path), "exec"), namespace)
    cfg = {k: namespace[k] for k in BASELINE}
    if cfg["SEARCH_MODE"] not in ("dense", "sparse", "hybrid") or any(
        type(cfg[k]) is not bool for k in BASELINE if k != "SEARCH_MODE"
    ):
        raise ValueError(
            "Use dense/sparse/hybrid and boolean investigation settings in retrieval.py"
        )
    return cfg


def client():
    return QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY") or None,
        timeout=10,
    )


@lru_cache(maxsize=1)
def encoder():
    return TextEmbedding(
        model_name=MODEL,
        cache_dir=os.getenv("FASTEMBED_CACHE_PATH", str(STATE_DIR / "models")),
        threads=2,
        local_files_only=os.getenv("FASTEMBED_OFFLINE", "1") == "1",
    )


# Preserve compound identifiers as single lowercase terms; no stemming or stopwords.
def tokens(text):
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower())


@lru_cache(maxsize=1)
def vocabulary():
    counts = Counter(
        t for p in PASSAGES for t in set(tokens(p["section_id"] + " " + p["text"]))
    )
    return {
        t: (i, math.log((len(PASSAGES) + 1) / (n + 1)) + 1)
        for i, (t, n) in enumerate(sorted(counts.items()))
    }


def sparse(text):
    vocab = vocabulary()
    pairs = sorted(
        (vocab[t][0], (1 + math.log(n)) * vocab[t][1])
        for t, n in Counter(tokens(text)).items()
        if t in vocab
    )
    norm = math.sqrt(sum(v * v for _, v in pairs)) or 1
    return models.SparseVector(
        indices=[i for i, _ in pairs], values=[v / norm for _, v in pairs]
    )


@lru_cache(maxsize=256)
def dense_query(question):
    return next(encoder().query_embed(question)).tolist()


def scope_filter(matter_id, as_of, cfg, extra=()):
    from datetime import date

    if matter_id not in MATTERS:
        raise ValueError("Unknown matter")
    day = date.fromisoformat(as_of).toordinal()
    conditions = [
        models.FieldCondition(
            key="matter_id", match=models.MatchValue(value=matter_id)
        ),
        *extra,
    ]
    if cfg["CHECK_VERSIONS"]:
        conditions.extend(
            [
                models.FieldCondition(key="published_day", range=models.Range(lte=day)),
                models.FieldCondition(
                    key="valid_from_day", range=models.Range(lte=day)
                ),
                models.FieldCondition(key="valid_to_day", range=models.Range(gt=day)),
            ]
        )
    return models.Filter(must=conditions)


def _rows(points):
    return [
        dict({k: v for k, v in p.payload.items() if k != "_provenance"}, score=p.score)
        for p in points
    ]


def retrieve(question, matter_id, as_of, config=None, limit=TOP_K, purpose="initial"):
    if not question.strip():
        raise ValueError("Question must not be empty")
    cfg = config if config is not None else globals()["config"]()
    scope = scope_filter(matter_id, as_of, cfg)
    mode = cfg["SEARCH_MODE"]
    qclient = client()
    candidates = {}
    try:
        ready(qclient)
        vectors = {}
        for signal in ["dense", "sparse"] if mode == "hybrid" else [mode]:
            vectors[signal] = (
                dense_query(question) if signal == "dense" else sparse(question)
            )
            points = qclient.query_points(
                COLLECTION,
                query=vectors[signal],
                using=signal,
                query_filter=scope,
                limit=CANDIDATE_LIMIT,
                with_payload=True,
            ).points
            candidates[signal] = [
                {"passage_id": p.payload["passage_id"], "score": p.score}
                for p in points
            ]
        if mode == "hybrid":
            points = qclient.query_points(
                COLLECTION,
                prefetch=[
                    models.Prefetch(
                        query=vec, using=signal, filter=scope, limit=CANDIDATE_LIMIT
                    )
                    for signal, vec in vectors.items()
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                query_filter=scope,
                limit=CANDIDATE_LIMIT,
                with_payload=True,
            ).points
            candidates["fused"] = [
                {"passage_id": p.payload["passage_id"], "score": p.score}
                for p in points
            ]
        evidence = _rows(points[:limit])
        trace = [
            {
                "node": "countersearch" if purpose == "counterevidence" else "retrieve",
                "title": (
                    "Search for contrary evidence"
                    if purpose == "counterevidence"
                    else "Retrieve evidence"
                ),
                "summary": f"{mode} search returned {len(evidence)} passages for {matter_id}.",
                "query": question,
                "evidence_ids": [r["passage_id"] for r in evidence],
                "candidates": candidates,
                "qdrant": {
                    "collection": COLLECTION,
                    "filter": scope.model_dump(exclude_none=True),
                    "mode": mode,
                    "candidates_per_signal": CANDIDATE_LIMIT,
                    "limit": limit,
                    "fusion": "rrf" if mode == "hybrid" else None,
                },
            }
        ]
        return {"evidence": evidence, "trace": trace}
    finally:
        qclient.close()


def search(question, matter_id, config=None, as_of="2026-09-01"):
    return retrieve(question, matter_id, as_of, config)["evidence"]


def fetch_references(evidence, matter_id, as_of, config=None):
    cfg = config if config is not None else globals()["config"]()
    seen = {p["passage_id"] for p in evidence}
    refs = list(
        dict.fromkeys(
            ref for p in evidence for ref in p.get("references", []) if ref not in seen
        )
    )[:6]
    if not refs:
        return {
            "evidence": [],
            "trace": [
                {
                    "node": "references",
                    "title": "Follow cited sources",
                    "summary": "No unseen references in this evidence.",
                    "evidence_ids": [],
                }
            ],
        }
    scope = scope_filter(
        matter_id,
        as_of,
        cfg,
        [models.FieldCondition(key="passage_id", match=models.MatchAny(any=refs))],
    )
    qclient = client()
    try:
        ready(qclient)
        points, _ = qclient.scroll(
            COLLECTION, scroll_filter=scope, limit=6, with_payload=True
        )
        rows = [
            dict({k: v for k, v in p.payload.items() if k != "_provenance"}, score=None)
            for p in points
        ]
        rows.sort(key=lambda p: refs.index(p["passage_id"]))
        return {
            "evidence": rows,
            "trace": [
                {
                    "node": "references",
                    "title": "Follow cited sources",
                    "summary": f"Resolved {len(rows)} of {len(refs)} explicit references within matter/date scope.",
                    "requested_ids": refs,
                    "evidence_ids": [p["passage_id"] for p in rows],
                    "qdrant": {
                        "collection": COLLECTION,
                        "filter": scope.model_dump(exclude_none=True),
                        "operation": "scroll",
                    },
                }
            ],
        }
    finally:
        qclient.close()


def deduplicate(evidence):
    """Collapse derivative documents, preserving separate sections of primary sources."""
    seen = set()
    output = []
    for row in evidence:
        key = (
            row["source_family"]
            if row["kind"] in ("account_memo", "derived_memo")
            else row["passage_id"]
        )
        if key not in seen:
            seen.add(key)
            output.append(row)
    return output


def counter_query(question, matter_id=None):
    return "Independent operational exception report: failed or incomplete testing, disputed conclusions, contrary evidence and unresolved defects."


def ready(qclient=None):
    owned = qclient is None
    qclient = qclient or client()
    try:
        records = qclient.retrieve(COLLECTION, [1], with_payload=True)
        if not records or records[0].payload.get("_provenance") != PROVENANCE:
            raise RuntimeError(
                "Collection is not prepared for this corpus/model. Organizer: run python -m workshop.cli prepare."
            )
        if qclient.count(COLLECTION, exact=True).count != len(PASSAGES):
            raise RuntimeError(
                "Collection point count differs from the workshop corpus. Use a fresh QDRANT_COLLECTION and prepare."
            )
        return True
    finally:
        if owned:
            qclient.close()


def seed():
    """Idempotent upsert; never deletes other collections or participant files."""
    qclient = client()
    try:
        if not qclient.collection_exists(COLLECTION):
            qclient.create_collection(
                COLLECTION,
                vectors_config={
                    "dense": models.VectorParams(
                        size=384, distance=models.Distance.COSINE
                    )
                },
                sparse_vectors_config={"sparse": models.SparseVectorParams()},
            )
        qclient.create_payload_index(
            COLLECTION, "matter_id", models.PayloadSchemaType.KEYWORD, wait=True
        )
        for field in ("valid_from_day", "valid_to_day", "published_day"):
            qclient.create_payload_index(
                COLLECTION, field, models.PayloadSchemaType.INTEGER, wait=True
            )
        qclient.create_payload_index(
            COLLECTION, "passage_id", models.PayloadSchemaType.KEYWORD, wait=True
        )
        embeddings = list(encoder().passage_embed([p["text"] for p in PASSAGES]))
        qclient.upsert(
            COLLECTION,
            points=[
                models.PointStruct(
                    id=i + 1,
                    vector={
                        "dense": emb.tolist(),
                        "sparse": sparse(p["section_id"] + " " + p["text"]),
                    },
                    payload=dict(p, _provenance=PROVENANCE),
                )
                for i, (p, emb) in enumerate(zip(PASSAGES, embeddings))
            ],
            wait=True,
        )
        return qclient.count(COLLECTION, exact=True).count
    finally:
        qclient.close()
