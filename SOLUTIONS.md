# Reference Repairs

Use this after attempting an investigation. Keep the answer model, prompt, corpus, and evaluation rules fixed. The editable behavior lives in `workshop/retrieval.py`; the complete Qdrant implementation lives in `workshop/engine.py` and the bounded agent graph in `workshop/agent.py`.

## Missing Authority

```sh
uv run --frozen --env-file .env python -m workshop.cli checkpoint authority
uv run --frozen --env-file .env python -m workshop.cli evaluate --challenge 1 --reveal
```

This checkpoint sets `SEARCH_MODE = "hybrid"` and `FOLLOW_REFERENCES = True`. Compare meaning and lexical retrieval, then follow explicit source references to obtain the instrument the initial search missed. Keep matter constraints on both the initial and follow-up paths. Inspect the checkpoint's settings and the resulting activity trace before judging it by the answer alone.

Qdrant supports dense and sparse representations and server-side rank fusion; these supply candidates. The application supplies document relationships and chooses which reference to follow. [Qdrant hybrid-query documentation](https://qdrant.tech/documentation/search/hybrid-queries/) describes the retrieval facilities.

## Outdated Sources

```sh
uv run --frozen --env-file .env python -m workshop.cli checkpoint freshness
uv run --frozen --env-file .env python -m workshop.cli evaluate --challenge 2 --reveal
uv run --frozen --env-file .env python -m workshop.cli evaluate --challenge 1 --reveal
```

This checkpoint also sets `CHECK_VERSIONS = True`. Preserve the authority repair and constrain sources by the question's as-of date and supplied applicability rules. Apply the same policy to initial retrieval, reference following, and later searches. A source must have been published by the question date. The effective interval includes `valid_from` and excludes `valid_to` (`valid_from <= as_of < valid_to`); don't replace them with the machine's current date or a rule that always selects the latest version.

Qdrant's [payload filters](https://qdrant.tech/documentation/search/filtering/) enforce conditions on stored metadata. The application is responsible for accurate metadata and policy. A historical question can legitimately require an older source.

## False Consensus

```sh
uv run --frozen --env-file .env python -m workshop.cli checkpoint solution
uv run --frozen --env-file .env python -m workshop.cli evaluate --challenge 3 --reveal
uv run --frozen --env-file .env python -m workshop.cli evaluate --challenge 2 --reveal
uv run --frozen --env-file .env python -m workshop.cli evaluate --challenge 1 --reveal
```

This checkpoint also sets `SEEK_COUNTEREVIDENCE = True` and `DEDUPLICATE = True`. Preserve applicability filtering. Search for evidence that could challenge the preliminary conclusion, avoid treating repeated accounts as independent sources, and assess whether the packet establishes the required conditions. Inspect both supporting and competing records in the final context.

A countersearch isn't a contradiction detector. Source deduplication isn't a credibility score. Neither guarantees sufficiency; the result may need to state a remaining gap. These distinctions belong in the final answer as well as the debrief.

## Evidence to Look For

- **Authority:** Harbor's `rider` points to `acceptance` (Exhibit P-9), which requires the `attempt-log` and `correction-log`. A special exit route is conditional, not a general right.
- **Freshness:** at 1 September 2026, `termination-current` supplies Harbor's 30-day rule. At 1 March 2026, `termination-old` supplies the original 90-day rule. The unsigned seven-day draft never governs.
- **Consensus:** `adverse-report` (OPS-91) distinguishes archive delivery from successful reconstruction. The account memo and its four copies share one source family.

Passage IDs carry a matter prefix, such as `harbor-rider`. Reveal cases require Cedar's authority chain, Atlas's current 60-day timetable, and Cedar's competing operational record.

## Measured Evidence Checks

| Investigation | Starting Checkpoint | Before | Repair | After |
| --- | --- | --- | --- | --- |
| Missing Authority | `baseline` | 0/3 | `authority` | 3/3 |
| Outdated Sources | `authority` | 1/3 | `freshness` | 3/3 |
| False Consensus | `freshness` | 0/3 | `solution` | 3/3 |

The complete solution passes all nine cases, including the three reveal cases. These results use deterministic planning against real Qdrant. The live model can propose different follow-up queries, and a retrieved source can still be misread in the brief. A correct baseline answer can also mask an unreliable evidence set.

Keep the comparison budget fixed: eight candidates per signal, four passages per search, at most 10 passages in final context, six logical retrieval calls, and three reference batches total. Hybrid diagnostics make three server search requests per logical search; this is not an equal-compute comparison.

## Verify the Repair

```sh
uv run --frozen --env-file .env python -m workshop.cli verify
```

This exercises the reference checkpoints against real Qdrant. CLI `evaluate` defaults to investigation one; explicitly select the investigation and add `--reveal` for additional cases. The browser follows the persisted `reveal on` setting. A completed evaluation can report failed checks, so inspect its results rather than only its process exit status. Dependency failures must surface as errors.

Compare source-level results first, then run the live agent and inspect its answer and activity. Deterministic planning makes regression checks repeatable; it doesn't verify every possible live planner query or generated sentence. Retrieval success means the required evidence reached the assessed context, not that every legal conclusion is correct.

## Repairs That Miss the Point

| Change | Why It Falls Short |
| --- | --- |
| Hardcode one customer or source ID | Another matter and additional questions need their own evidence. |
| Increase context until every document fits | It hides selection failures and changes the declared comparison budget. |
| Use only the newest document | Historical questions need the instrument effective at their date. |
| Filter only the initial search | Reference and countersearch paths can reintroduce inapplicable sources. |
| Count repeated passages as corroboration | Several passages may repeat one original account. |
| Assume diversity proves disagreement | Distinct sources can agree, conflict, or remain inconclusive. Inspect them. |
| Rewrite the answer prompt or expected evidence | It changes the experiment instead of repairing evidence gathering. |

To restart, run `uv run --frozen --env-file .env python -m workshop.cli checkpoint baseline`. Backups in `.workshop/backups/` preserve the previous configuration; copy the desired saved file to `workshop/retrieval.py` to recover an edit.
