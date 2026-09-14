# Build ledger

## Verify everything in one go

```bash
uv run python -m workshop.validation      # corpus and calibration annotations
uv run python -m workshop.heldout         # held-out annotations
uv run python -m workshop.score           # scoring rubric self-check
uv run python -m workshop.clausebank      # CUAD loader
uv run python -m workshop.run preflight   # live cluster, must end "ready"
uv run python -m workshop.bench --parity  # the bench runs the query participants ship
uv run python -m workshop.bench           # the full grid, appends to experiments.jsonl
uv run python scripts/ship.py /tmp/check  # build the participant tree and sweep it
```

All eight pass as of this writing. The participant tree is seven Python files and carries no held-out ids, no lever notes, and no model inventory.

What was decided, what it was measured against, and what was rejected. Written for the session that reviews this next. Newest section last.

The brief is `instructions.md`. Every measurement in this file is reproducible with `uv run python -m workshop.bench`, and every configuration ever measured is in `experiments.jsonl` with its options, per-question outcomes, and provenance.

## Where the project stands

Working end to end. Collection live at `legal_lab_v1` with 3,653 passages. Participants clone, `uv sync`, `preflight`, and tune. The cumulative ladder on the 29 scored questions:

| Rung | Change | Solved | Coverage | Leaks | Stale | Dupes |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | starter as shipped | 13/29 | 0.517 | 90 | 0 | 9 |
| 1 | filter by matter | 17/29 | 0.707 | 0 | 0 | 11 |
| 2 | drop the `status` filter | 21/29 | 0.828 | 0 | 2 | 11 |
| 3 | exclusive end date | 21/29 | 0.828 | 0 | 0 | 11 |
| 4 | deeper candidate pool | 21/29 | 0.828 | 0 | 0 | 11 |
| 5 | group by source family | 22/29 | 0.862 | 0 | 0 | 0 |
| 6 | add the context vector | 23/29 | 0.862 | 0 | 0 | 0 |
| 7 | tune RRF weights 2:2:1 | 24/29 | 0.897 | 0 | 0 | 0 |

Measured 2026-09-14T00:18:52, git 5962901, 3653 points. Taken from `experiments.jsonl`, which is the source of truth for every number in this file. Rung 0 jitters by about one solved question between runs because a deliberately small candidate pool produces many exactly-tied RRF scores; tuned rungs are stable.

Blocked on one thing only: the Qdrant Cloud cluster has no billing attached, so `mixedbread-ai/mxbai-embed-large-v1` and `prithivida/Splade_PP_en_v1` refuse with "Authentication failed for inference". Both are declared in the collection and load the moment billing lands. Re-run `uv run python -m workshop.ingest` and then `uv run python -m workshop.bench`.

## The corpus

**Two layers, and the split is deliberate.** 110 hand-authored fictional passages across three matters carry all the teaching. 3,543 real CUAD clause passages across 150 real contracts are the rest of the firm's document store.

**Why the constructions are hand-authored and will stay that way.** A supersession relationship has to be readable in the sentence. Amendment No. 3 says "a notice of default received before the Amendment Effective Date remains governed by Section 11.1 as originally executed". No real corpus contains matched amendment pairs that cross-reference each other like that, and grafting an invented amendment history onto real contract text is the exact trap the brief names: participants would learn to obey our metadata instead of reading evidence.

**Why CUAD, and what it is and is not for.** Chosen over LEDGAR, ContractNLI, EUR-Lex, CaseHOLD, Caselaw Access Project, and ToS;DR. CC BY 4.0, 510 contracts, clause-level spans, no authentication, and clauses short enough for every model's context window (median 46 words). It exists to make the missing matter filter a real failure: 96 leaked passages at rung 0, zero at rung 1. It does nothing after that, because a matter filter removes all of it. Both reviewers flagged this as "stage scenery", and that is accepted: it buys the opening story and nothing else. LEDGAR is the scale-up if 3,543 ever proves thin, but its dataset card leaves the licence section blank and that needs checking before it ships.

**There is no `authority` payload field, on purpose.** It would make the authority-versus-repetition case a one-line filter. `instrument_type` records what a document *is*; the reader supplies the judgment.

**`source_family` means duplicate copies of one memo, nothing else.** It first defaulted to the document, which made every section of an agreement a "duplicate" of its siblings and silently zeroed the second controlling passage on every dependency question. Caught by running the scorer, not by reading it. Ranking rose 0.41 to 0.48 on the fix.

## What was rejected, and why

**Rejected: `avg_len` on BM25.** The brief called it "the best candidate we have". Measured through Cloud Inference at `avg_len` 80 and 5000: byte-identical scores. Inert.

**Rejected: unfiltered prefetch as a planted bug.** Qdrant propagates the outer `query_filter` into prefetches, so the bug does not manifest. Controlling evidence found 12/16 either way.

**Rejected: `should` instead of `must` to fake tenant leakage.** A `should` clause is required when present, so it behaves like `must`. Zero leaks.

**Rejected: miniCOIL.** Returns "Unsupported model" across five name spellings. Not on the cluster.

**Rejected: a FormulaQuery authority prior over `instrument_type`.** Coverage stayed at exactly 0.639 at every boost from 0.005 to 0.1, because grouping already removes the memo crowding it was meant to fix.

**Rejected: MMR.** Exists as `models.Mmr`. Monotonically harmful here: 18, 14, 11 solved at diversity 0.2, 0.5, 0.8.

**Rejected: ColBERT as the hidden centrepiece.** It is in the collection and it is a real capability. It costs four to five solved questions once grouping is on. Kept precisely because it is an attractive experiment that does not pay, which is a better lesson than a hidden win.

**Rejected: query rewriting and multi-query as participant levers.** This is a Qdrant workshop. Rephrasing belongs to the agent, and the agent does not do it either.

**Rejected: encrypting the held-out questions.** Security theatre for an honour-based event. Held-out questions ship in a separate organizer-side file instead, which actually works.

## Scoring

**Applicability was cut as a published dimension.** It read 1.000 for every configuration that filters correctly, so it measured filter correctness, not retrieval quality. It is replaced by three counts a person can see in the result list: `leak`, `stale`, `dup`. The averaged value is still computed as `_applicability_internal` and is never printed or ranked on.

**The scorer grades returned payloads, not passage ids.** It therefore never looks anything up in the corpus, and it grades exactly what the system returned.

**Rank on coverage, break ties on NDCG@5.** `solved` is identical across repeated runs at every rung. RRF ties are common and Qdrant does not order them stably, which moves the ranking tiebreaker by at most 0.013, well under the 0.03 to 0.06 gaps between rungs. The best configuration is perfectly deterministic, because weights break the ties.

## The question set

37 annotated questions, split by measurement.

**8 are headroom and are never scored.** No configuration tried reaches their evidence: every fusion weighting, DBSF, ColBERT, each signal alone, a 150-deep pool. Their controlling passages sit at ranks 8 to 23. Ranking people on them would be ranking them on nothing. Two are shown as unscored ceiling probes.

**29 are scored.** 12 disclosed as the calibration set, 17 held out.

**The calibration set is chosen by measured sensitivity, not taste.** The first version returned 5/12 for every configuration tested, so participants would have tuned blind, which is the one failure the brief explicitly set out to prevent. It now moves across the ladder and tracks the held-out set, so tuning against what they see generalises to what they do not.

**One memo is controlling evidence.** Codex caught that every memo being wrong made "down-weight memos" a corpus exploit rather than a lesson. `atlas-qa-memo` is the only record of whether the first article inspection passed. It evidences a factual event; the Engineering Change Notice still supplies the rule. It is disclosed in the calibration set so the cost of a blanket memo penalty is visible immediately.

## Things that were wrong and got fixed

**The bench did not run the query participants ship.** `lab.py` filtered only the outer query while the bench also filtered inside every prefetch. `uv run python -m workshop.bench --parity` now proves them identical: 37/37 return the same passages at depth 20. Without this every number in the log was a claim about code nobody runs.

**The experiment log was not auditable.** It discarded per-question rows, so "never solved" could not be reconstructed. It now records per-question coverage, ranking, returned ids, and missing ids, plus git SHA, question-set hash, collection name, point count, vector inventory, and client version.

**Preflight failed the whole check on an optional model.** It treated every declared vector as required, so a participant would read "not ready" because `dense_strong` needs billing, even though the workshop path works. Required is now `dense_weak` and `bm25` only; everything else is a note. It also exercises one weighted-grouped-fusion request, not just each vector alone.

**Questions quoting clause language made BM25 unbeatable.** The first drafts used contract vocabulary, so lexical matching won outright: BM25 alone scored 0.958 coverage and beat every semantic lever. Rewritten into practitioner phrasing ("how long do we have to put it right before they can walk away" rather than "cure period after a notice of default"). BM25 alone dropped to 0.708 and the semantic levers started paying.

**The expansion overshot.** 28 extra clauses per matter were added for realism. 33 of them were referenced by no question and were crowding the top four of every hard question. Removed. Reachability did not change, which is what makes the headroom set a model ceiling rather than a corpus-noise artefact.

## Shipping, the app, and the playbook

**The participant repository is built, not curated.** `uv run python scripts/ship.py <target>` copies the fifteen files a participant needs and regenerates `workshop/questions.py` with the twelve calibration questions inline, so nothing in the shipped tree imports the held-out set. It then greps the result for held-out question ids and refuses to finish if any appear. Verified: nine Python files ship, zero held-out ids, `preflight` reports ready and `score` runs from the shipped tree.

**The reference solution is reachable through the permitted interface.** `scripts/reference_lab.py` is `lab.py` with every lever applied and nothing else changed. Measured: 10/12 calibration, 14/17 held out, 24/29 scored, with leaks, stale and duplicates all at zero. Tuning against the disclosed set transfers to the hidden set, which is the property the calibration split exists to provide.

**There is a web app, and it earns its place on one point.** `uv run python -m workshop.app`, standard library only, one process per participant, no framework and no new dependency. Ranked passages read better in a bar than terminal output, another client's document is flagged in Amaranth where it cannot be missed, and the first score of the evening is saved as the baseline every later run is compared against. Branded from the official palette: Amaranth `#DC244C` and Neon Blue `#6047FF` as accents on `#0B0B19` and white, Mona Sans with a system fallback stack.

**The playbook is encoded, and that is honest rather than secure.** Eight applicability rules render in the app's right-hand panel and appear in no readable file. The point is that the legal judgment reaches the person rather than their coding agent. Encoding stops a repository grep; it stops nothing else, and `workshop/playbook.py` says so in its own docstring. `AGENTS.md` still hands an agent the mechanical facts, the payload fields and the existence of extra vectors, because rediscovering those wastes the participant's thirty minutes and they are not the lesson. The judgment is.

**What the app does not do.** No leaderboard, no submission flow, no organizer-side scoring service. The brief settled that the competition is honour-based and low stakes, and a service nobody needs is the easiest thing to build and the hardest to justify.

## Spoilers found in the shipped tree, and closed

A review of the built participant copy found four places where the answers leaked. All four were mine, and all four were introduced while making something else better.

**`corpus.py` named the case constructions in its own comments.** Section headers read `A. Historical applicability: cure period, original versus Amendment No. 3` and `C. Authority versus repetition: retention schedule versus a memo family`. Anyone reading the corpus source got the lever list free. The corpus source no longer ships; participants read passages through the app, which is how they should meet them anyway. `MATTERS` moved to `questions.py` so the runners never import it.

**The generated `questions.py` shipped the `improvement` field.** Each calibration question carried a note such as "Filter on the effective-date interval with the question date". That is the answer, one question at a time. `scripts/ship.py` now strips `construction`, `rationale`, and `improvement`, and keeps only what the scorer needs to grade.

**Preflight executed the reference solution.** A check added to exercise a realistic query used weighted three-prefetch fusion over `dense_weak`, `dense_context` and `bm25`, grouped by `source_family`, with weights `[2.0, 2.0, 1.0]`. That is rungs five, six and seven printed in the setup step. Preflight now tests only the two models `lab.py` itself names.

**`vectors.py` listed every model behind every representation.** Withheld. Participants still see six vector names from the collection, which is the intended hint, and `dense_context` uses the same model id `lab.py` already declares, so the discovery stays possible without being handed over.

The sweep that catches this class of mistake is in `scripts/ship.py`: it greps the built tree for held-out question ids and refuses to finish if any appear. Re-run it after any change to what ships.

## Late changes

**Deleted the averaged applicability metric.** It was computed on every scoring call and printed nowhere. A metric with no reader is a metric that quietly comes back in a report.

**`CLAUDE.md` is now one line pointing at `AGENTS.md`.** They were byte-identical, which is two files that can drift into disagreeing.

**`scripts/ship.py` writes a filled `.env` when the read-only key exists**, and prints a loud warning when it does not, because `client.py` falls back to the write key and thirty laptops must not hold a key that can delete the collection.

**The reveal demo changed question.** It was going to re-run the opening cure-period question after tuning, except that question is one of the two ceiling probes and the tuned solution does not solve it either. The connector question does flip, and it flips further than expected: the starter returns five identically titled memos and the agent says it cannot tell, while the tuned version answers "No. You are not cleared to build" and cites the failed inspection. Same agent, same model, different evidence. Verified end to end, both halves.

## Open, for the morning

1. **Attach billing to the cluster.** It unblocks two of six representations and is the only untested lever plausibly able to move the eight headroom questions. Cost is real but negligible: about 8k tokens to ingest and roughly 60k tokens for a full room, well under a cent at the Mixedbread rate.
2. **Create the read-only, collection-scoped API key.** `QDRANT_READONLY_API_KEY` is empty, so `client.py` falls back to the write key. Thirty laptops must not hold a key that can delete the collection.
3. **"The model is your ceiling" is not yet proven.** Ranks 8 to 23 show the evidence is in first-stage recall; they do not prove an embedding ceiling rather than a top-5, fusion, or interface ceiling. Do not put it on a slide until the Mixedbread measurement exists.
4. **Rehearse it.** Play the workshop solo and in a pair, and run a coding agent against the shipped tree unattended for thirty minutes and score it. If the agent alone reaches most of what a person reaches, the legal reasoning is decorative and the questions need rebalancing. The tooling for that test is already here: `scripts/ship.py` builds the tree, `workshop/bench.py` scores anything.
5. **The corpus runs slightly denser than the five-second bar.** Clauses average four sentences. The playbook rules hit the bar; passages such as `harbor-cure` take ten to fifteen seconds. Worth one trimming pass if there is time, and harmless if there is not.
