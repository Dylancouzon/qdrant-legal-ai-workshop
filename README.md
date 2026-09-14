# The Qdrant Legal Retrieval Lab

A law firm's document store sits in a Qdrant collection: three client matters, and several hundred real commercial contracts belonging to other clients. Someone asks a dated question about one matter. Your job is to return the evidence that answers it.

The retrieval you have been given works. It is also wrong in ways that would end a career in a regulated practice, and it will not tell you that.

## Setup

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and about two minutes.

```bash
git clone <this repo> && cd qdrant-legal-ai-workshop
uv sync
uv run python -m workshop.run preflight
```

The repository already contains a `.env` holding the cluster address and a read-only key scoped to this one collection. If it does not, ask the facilitator: the values are on the setup slide, and you copy them into `.env.example` and save it as `.env`.

`preflight` prints a line per check and ends with `ready`. If it does not, fix the `FAIL` lines before you tune anything. The collection is hosted and read-only, so nothing runs on your laptop and there is no model to download.

## The loop

Two ways to run it. The browser is easier to read in a room with a drink in your hand, and it carries the applicability playbook, which is the legal half of this exercise and is not written down anywhere else.

```bash
uv run python -m workshop.app     # http://localhost:8000
```

Or stay in the terminal:

```bash
# See what comes back, and read it the way a person would.
uv run python -m workshop.run ask "how long do we have to fix the problem?" -m harbor -d 2026-01-20

# Score yourself against the calibration questions.
uv run python -m workshop.run score
```

Edit `workshop/lab.py`. Score again. Watch the numbers move. That is the whole loop.

Read the playbook panel before you start tuning. It is eight short rules about which document answers a dated question about a client, and the questions are written to reward following them.

## The rules

1. You edit `workshop/lab.py` and nothing else.
2. Keep the signature of `retrieve()` exactly as it is. The scorer calls it.
3. Query-time Qdrant code only. The collection is read-only and preloaded.
4. Do not rewrite the question. The agent that consumes your evidence makes one retrieval call and never tries again, so the answer is only ever as good as what `retrieve()` returned.

## What you are scored on

`score` prints six numbers. Two of them rank you.

| Column | Meaning |
| --- | --- |
| `cover` | Share of the controlling passages you retrieved. This ranks you first. |
| `rank` | How well the remaining graded results were ordered. Tiebreaker. |
| `leak` | Passages from another client's files. |
| `stale` | This client's passages, outside their effective window on the question date. |
| `dup` | Rank slots taken by a repeat copy of a document you already returned. |

The three counts are not averaged into a score. They are failures you can see in the result list, and a good run drives them to zero.

The twelve calibration questions are not the questions you are scored on. They teach you the relevance rubric. The held-out set is revealed at the end.

## A note on the documents

The three client matters, their parties, documents, dates, and every clause in them are invented for this workshop. They are not legal advice and they do not describe any real agreement.

The remaining contracts are real public filings from [CUAD](https://www.atticusprojectai.org/cuad), the Contract Understanding Atticus Dataset, published by The Atticus Project under CC BY 4.0. They keep their own names and parties, and no invented history has been attached to any of them.
