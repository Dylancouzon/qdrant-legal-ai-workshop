# Working in this repository

This is a timed retrieval-tuning exercise. A person has thirty minutes. Do not spend their budget reading the repository.

## The only file you may edit

`workshop/lab.py`. Everything else is fixed, including the scorer, the corpus, and the questions. Keep the signature of `retrieve()` exactly as it is.

## What you are optimising

Run `uv run python -m workshop.run score`. It prints, per question and in total:

- `cover`, the share of controlling passages retrieved. This is the primary score.
- `rank`, ordering quality of the remaining graded results. Tiebreaker.
- `leak`, `stale`, `dup`, three counts of visible failures. Drive them to zero.

Change one thing in `lab.py`, run `score`, keep the change if the numbers improve. That is the whole method.

## Facts about the collection you would otherwise have to discover

- It is read-only and preloaded. Do not try to write, re-ingest, or re-embed.
- Every embedding is produced by Qdrant Cloud Inference. No model runs locally. Use `models.Document(text=..., model=...)`.
- It holds more named vectors than `lab.py` currently queries. `score` prints how many it uses against how many exist. Inspecting the collection is allowed and encouraged.
- Every passage payload carries: `matter_id`, `effective_from`, `effective_to`, `status`, `instrument_type`, `source_family`, `document_id`, `section_id`, `heading`, `references`.
- `effective_from` and `effective_to` are ISO dates, filterable with `models.DatetimeRange`.

## Out of scope

Do not rewrite or expand the question text, and do not call `retrieve()` more than once per question. The agent that consumes this evidence makes exactly one call and never retries. Tuning the query string is not the exercise; tuning Qdrant is.

Do not look for the held-out questions. They are not in this repository.
