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

All eight pass as of this writing. The participant tree is `lab.py` at the top and nine fixed files in `workshop/`, and it carries no held-out ids, no lever notes, and no model inventory.

What was decided, what it was measured against, and what was rejected. Written for the session that reviews this next. Newest section last.

The brief is `instructions.md`. Every measurement in this file is reproducible with `uv run python -m workshop.bench`, and every configuration ever measured is in `experiments.jsonl` with its options, per-question outcomes, and provenance.

## Where the project stands

Working end to end. Collection live at `legal_lab_v2` with 3,653 chunks, under vector names that state the model and the text rather than a verdict. Participants clone, `uv sync`, `setup`, and tune. What each lever is worth, measured with every other lever switched on, over the 31 scored questions:

| Lever | Worth | Solved without it | Questions it alone solves |
| --- | --- | --- | --- |
| filter by matter | 64 pts | 14/31 | 15 |
| filter on the effective dates | 17 pts | 25/31 | 1, and it clears 26 not-in-effect chunks |
| stop filtering on `status` | 15 pts | 20/31 | 6 |
| group by source family | 6 pts | 25/31 | 2 |
| scope BM25 IDF to the matter | 4 pts | 25/31 | 3 |
| exclusive end date | 2 pts | 26/31 | none, it clears 3 not-in-effect chunks |
| candidate pool 60 rather than 5 | 2 pts | 25/31 | 1 |
| add the document-context vector | 0.9 pts | 25/31 | 1 |

Best configuration: score 87, 26/31 solved, coverage 0.919, ordering quality 0.726, every visible failure at zero. Rejected with numbers: ColBERT costs 13 points, MMR 17, RRF weights 2:2:1 costs 3.

One order of discovery, for the room: starter 21, filter by matter 60, drop the `status` filter 75, exclusive end date 76, group by source family 82, add the document-context vector 83, scope BM25 IDF to the matter 87.

Measured 2026-09-14 on `legal_lab_v2`, 3653 points, with `uv run python -m workshop.bench --levers`. The rename moved nothing: under the score in force at the time, the reference read 92 with 26/31 on both collections. `experiments.jsonl` is the source of truth for every number in this file. The starter jitters by about one solved question between runs because a deliberately small candidate pool produces many exactly-tied RRF scores; tuned configurations are stable.

Blocked on one thing only: the Qdrant Cloud cluster has no billing attached, so `mixedbread-ai/mxbai-embed-large-v1` and `prithivida/Splade_PP_en_v1` refuse with "Authentication failed for inference". Both are declared in the collection and load the moment billing lands. Re-run `uv run python -m workshop.ingest` and then `uv run python -m workshop.bench`.

## The corpus

**Two layers, and the split is deliberate.** 110 hand-authored fictional chunks across three matters carry all the teaching. 3,543 real CUAD clause chunks across 150 real contracts are the rest of the firm's document store.

**Why the constructions are hand-authored and will stay that way.** A supersession relationship has to be readable in the sentence. Amendment No. 3 says "a notice of default received before the Amendment Effective Date remains governed by Section 11.1 as originally executed". No real corpus contains matched amendment pairs that cross-reference each other like that, and grafting an invented amendment history onto real contract text is the exact trap the brief names: participants would learn to obey our metadata instead of reading evidence.

**Why CUAD, and what it is and is not for.** Chosen over LEDGAR, ContractNLI, EUR-Lex, CaseHOLD, Caselaw Access Project, and ToS;DR. CC BY 4.0, 510 contracts, clause-level spans, no authentication, and clauses short enough for every model's context window (median 46 words). It exists to make the missing matter filter a real failure: 96 leaked chunks at rung 0, zero at rung 1. It does nothing after that, because a matter filter removes all of it. Both reviewers flagged this as "stage scenery", and that is accepted: it buys the opening story and nothing else. LEDGAR is the scale-up if 3,543 ever proves thin, but its dataset card leaves the licence section blank and that needs checking before it ships.

**There is no `authority` payload field, on purpose.** It would make the authority-versus-repetition case a one-line filter. `instrument_type` records what a document *is*; the reader supplies the judgment.

**`source_family` means duplicate copies of one memo, nothing else.** It first defaulted to the document, which made every section of an agreement a "duplicate" of its siblings and silently zeroed the second controlling chunk on every dependency question. Caught by running the scorer, not by reading it. Ranking rose 0.41 to 0.48 on the fix.

## What was rejected, and why

**Rejected: `avg_len` on BM25.** The brief called it "the best candidate we have". Measured through Cloud Inference at `avg_len` 80 and 5000: byte-identical scores. Inert.

**Rejected: unfiltered prefetch as a planted bug.** Qdrant propagates the outer `query_filter` into prefetches, so the bug does not manifest. Controlling evidence found 12/16 either way.

**Rejected: `should` instead of `must` to fake tenant leakage.** A `should` clause is required when present, so it behaves like `must`. Zero leaks.

**Rejected: miniCOIL.** Returns "Unsupported model" across five name spellings. Not on the cluster.

**Rejected: a FormulaQuery authority prior over `instrument_type`.** Coverage stayed at exactly 0.639 at every boost from 0.005 to 0.1, because grouping already removes the memo crowding it was meant to fix.

**Rejected: MMR.** Exists as `models.Mmr`. Monotonically harmful here: 18, 14, 11 solved at diversity 0.2, 0.5, 0.8.

**Rejected: ColBERT as the hidden centrepiece.** It is in the collection and it is a real capability. It costs four to five solved questions once grouping is on. Kept precisely because it is an attractive experiment that does not pay, which is a better lesson than a hidden win.

**Accepted: tenant-scoped BM25 IDF as the advanced lever.** The cluster runs Qdrant 1.19.1, `matter_id` has a keyword index, and the BM25 vector uses the IDF modifier. Supplying an `IdfCorpusParams` filter for the matter raises the best configuration from 87 to 92 points and from 25/31 to 26/31 solved, with every visible failure still at zero. It also changed the value of another lever: RRF weights of 2:2:1 gained a question before it and cost three points after it. This is query-time, specific to a multi-tenant legal collection, and recent enough that a generic coding agent is unlikely to suggest it without current documentation.

**Rejected: query rewriting and multi-query as participant levers.** This is a Qdrant workshop. Rephrasing belongs to the agent, and the agent does not do it either.

**Rejected: encrypting the held-out questions.** Security theatre for an honour-based event. Held-out questions ship in a separate organizer-side file instead, which actually works.

## Scoring

**Applicability was cut as a published dimension.** It read 1.000 for every configuration that filters correctly, so it measured filter correctness, not retrieval quality. It is replaced by three counts a person can see in the result list: `leak`, `stale`, `dup`. The averaged value is still computed as `_applicability_internal` and is never printed or ranked on.

**The scorer grades returned payloads, not chunk ids.** It therefore never looks anything up in the corpus, and it grades exactly what the system returned.

**Rank on coverage, break ties on NDCG@5.** `solved` is identical across repeated runs at every rung. RRF ties are common and Qdrant does not order them stably, which moves the ranking tiebreaker by at most 0.013, well under the 0.03 to 0.06 gaps between rungs. The best configuration is perfectly deterministic, because weights break the ties.

## The question set

37 annotated questions, split by measurement.

**6 are headroom and are never scored.** No configuration tried reaches their evidence: every fusion weighting, DBSF, ColBERT, each signal alone, a 150-deep pool. Their controlling chunks sit at ranks 8 to 23. Ranking people on them would be ranking them on nothing. Two are shown as unscored ceiling probes.

**29 are scored.** 12 disclosed as the calibration set, 17 held out.

**The calibration set is chosen by measured sensitivity, not taste.** The first version returned 5/12 for every configuration tested, so participants would have tuned blind, which is the one failure the brief explicitly set out to prevent. It now moves across the ladder and tracks the held-out set, so tuning against what they see generalises to what they do not.

**One memo is controlling evidence.** Codex caught that every memo being wrong made "down-weight memos" a corpus exploit rather than a lesson. `atlas-qa-memo` is the only record of whether the first article inspection passed. It evidences a factual event; the Engineering Change Notice still supplies the rule. It is disclosed in the calibration set so the cost of a blanket memo penalty is visible immediately.

## Things that were wrong and got fixed

**The bench did not run the query participants ship.** `lab.py` filtered only the outer query while the bench also filtered inside every prefetch. `uv run python -m workshop.bench --parity` now proves them identical: 37/37 return the same chunks at depth 20. Without this every number in the log was a claim about code nobody runs.

**The experiment log was not auditable.** It discarded per-question rows, so "never solved" could not be reconstructed. It now records per-question coverage, ranking, returned ids, and missing ids, plus git SHA, question-set hash, collection name, point count, vector inventory, and client version.

**Preflight failed the whole check on an optional model.** It treated every declared vector as required, so a participant would read "not ready" because the Mixedbread vector needs billing, even though the workshop path works. Required is now the two vectors `lab.py` itself names; everything else is a note. It also exercises one weighted-grouped-fusion request, not just each vector alone.

**Questions quoting clause language made BM25 unbeatable.** The first drafts used contract vocabulary, so lexical matching won outright: BM25 alone scored 0.958 coverage and beat every semantic lever. Rewritten into practitioner phrasing ("how long do we have to put it right before they can walk away" rather than "cure period after a notice of default"). BM25 alone dropped to 0.708 and the semantic levers started paying.

**The expansion overshot.** 28 extra clauses per matter were added for realism. 33 of them were referenced by no question and were crowding the top four of every hard question. Removed. Reachability did not change, which is what makes the headroom set a model ceiling rather than a corpus-noise artefact.

## Shipping, the app, and the playbook

**The participant repository is built, not curated.** `uv run python scripts/ship.py <target>` copies the twenty files a participant needs and regenerates `workshop/questions.py` with the twelve calibration questions inline, so nothing in the shipped tree imports the held-out set. It then greps the result for held-out question ids and refuses to finish if any appear. Verified: eleven Python files ship, zero held-out ids, `preflight` reports ready and `score` runs from the shipped tree.

**The reference solution is reachable through the permitted interface.** `scripts/reference_lab.py` is `lab.py` with every lever applied and nothing else changed. Measured: 10/12 calibration scoring 86, 16/19 held out scoring 88, 26/31 scored scoring 87, with wrong client, not in effect, and duplicate at zero. Tuning against the disclosed set transfers to the hidden set, which is the property the calibration split exists to provide.

**There is a web app, and it earns its place on one point.** `uv run python -m workshop.app`, standard library only, one process per participant, no framework and no new dependency. Ranked chunks read better in a bar than terminal output, and the first score of the evening is saved as the baseline every later run is compared against. Branded from the official palette: Amaranth `#DC244C` and Neon Blue `#6047FF` as accents on `#0B0B19` and white, Mona Sans with a system fallback stack.

**The app starts from supplied cases rather than an empty search box.** Participants choose one of the twelve calibration cases and the case carries its question, its client, and its date. A participant can also write their own question, which opens a client file first and is never scored. Nothing on the screen names a controlling chunk or a Qdrant feature. The playbook is grouped into scope, source judgment, and completeness, with each rule collapsed until needed.

**The playbook is encoded, and that is honest rather than secure.** Seven applicability rules render in the app's right-hand panel and appear in no readable file in the participant tree. The point is that the legal judgment reaches the person rather than their coding agent. Encoding stops a repository grep; it stops nothing else, and `workshop/playbook.py` says so in its own docstring. `AGENTS.md` still hands an agent the mechanical facts, the payload fields and the existence of extra vectors, because rediscovering those wastes the participant's thirty minutes and they are not the lesson. The judgment is.

**What the app does not do.** No leaderboard, no submission flow, no organizer-side scoring service. The brief settled that the competition is honour-based and low stakes, and a service nobody needs is the easiest thing to build and the hardest to justify.

## Spoilers found in the shipped tree, and closed

A review of the built participant copy found four places where the answers leaked. All four were mine, and all four were introduced while making something else better.

**`corpus.py` named the case constructions in its own comments.** Section headers read `A. Historical applicability: cure period, original versus Amendment No. 3` and `C. Authority versus repetition: retention schedule versus a memo family`. Anyone reading the corpus source got the lever list free. The corpus source no longer ships; participants read chunks through the app, which is how they should meet them anyway. `MATTERS` moved to `questions.py` so the runners never import it.

**The generated `questions.py` shipped the `improvement` field.** Each calibration question carried a note such as "Filter on the effective-date interval with the question date". That is the answer, one question at a time. `scripts/ship.py` now strips `construction`, `rationale`, and `improvement`, and keeps only what the scorer needs to grade.

**Preflight executed the reference solution.** A check added to exercise a realistic query used weighted three-prefetch fusion over the two MiniLM vectors and `bm25`, grouped by `source_family`, with weights `[2.0, 2.0, 1.0]`. That is rungs five, six and seven printed in the setup step. Preflight now tests only the two models `lab.py` itself names.

**`vectors.py` listed every model behind every representation.** Withheld. Participants still see six vector names from the collection, which is the intended hint, and `minilm_l6_document` uses the same model id `lab.py` already declares, so the discovery stays possible without being handed over.

The sweep that catches this class of mistake is in `scripts/ship.py`: it greps the built tree for held-out question ids and refuses to finish if any appear. Re-run it after any change to what ships.

## Late changes

**Deleted the averaged applicability metric.** It was computed on every scoring call and printed nowhere. A metric with no reader is a metric that quietly comes back in a report.

**`CLAUDE.md` is now one line pointing at `AGENTS.md`.** They were byte-identical, which is two files that can drift into disagreeing.

**Participant credentials ship encrypted.** `scripts/ship.py` requires the read-only Qdrant key, a dedicated OpenAI project key, and a workshop password of at least 10 characters. It encrypts the credentials in memory with scrypt and AES-256-GCM, then writes `.env.enc` without ever writing a plaintext participant `.env`. `uv run python -m workshop.setup` asks for the password, authenticates and decrypts the bundle locally, writes `.env` with owner-only permissions, and runs preflight. This keeps the keys out of the repository, but it is not access control after the password is announced. Keep the Qdrant key collection-scoped and read-only, cap the OpenAI project budget, and revoke both after the event.

**The reveal demo changed question.** It was going to re-run the opening cure-period question after tuning, except that question is one of the two ceiling probes and the tuned solution does not solve it either. The connector question does flip, and it flips further than expected: the starter returns five identically titled memos and the agent says it cannot tell, while the tuned version answers "No, Atlas Robotics is not cleared to build" and cites the failed inspection. Same agent, same model, different evidence. Verified end to end, both halves.

**The browser leads with the agent, not the score.** The first screen takes a question, shows the answer, and puts the five chunks the answer was built from underneath it, each one tagged with its client, its dates, and whether the agent cited it. A person reads a fluent answer and then reads the other client's contract it was built from, which is the lesson the score can only imply. The calibration board moved behind a call to action and keeps the same two things inside every row. A person can also type their own question: exploring the store is how they get a feel for the agent, and the twelve supplied cases stay word for word because those are the ones that are judged.

**The answering agent is shared code, and its citations are checked.** `workshop/agent.py` holds the single call that both the terminal and the browser use, so the stage demo and the participant button cannot drift. It returns the reply, the chunk numbers it cited, and any number it cited that was never retrieved. The three matters are invented, so the model has no memory of them to fall back on, and the citation check covers the other half. A ghost citation renders in red and the answer says not to trust it.

**Column names are plain English, and coverage is a fraction.** `cover`, `rank`, `leak`, `stale`, and `dup` became Evidence Found, Order, Wrong Client, Not in Effect, and Duplicate in both the terminal and the browser, and a case reads `1 of 2` rather than `0.50`. The old names were compact for the author and opaque for the room.

**One word for the unit: chunk.** Qdrant house vocabulary. The prose, the UI, the prompt, and the scorer all say chunk. The payload field `passage_id` keeps its name, because it is a key in the preloaded read-only collection and renaming it means a re-ingest for no reader.

**Three questions no longer depend on the one above them.** "Same problem with a shipment that landed on 1 June 2026" and two others read as a follow-up in a list, which is fine in an authoring file and wrong in a dropdown where a person sees one case at a time. Each now names its own facts. Measured after the rewrite: the reference solution still scores 25 of 29 with coverage 0.914 and zero visible failures, and all three still resolve to their labelled evidence.

**The question date is labelled "as of", not "asked on".** The date is the date the question turns on, which is why a case can carry December 2025: the schedule in effect then is the answer. Ten of the fourteen cases sit at 2026-09-01 and read as today. The four historical ones are the temporal half of the exercise, so they keep their dates, and a question a participant writes uses today.

**The first screen is a conversation, not a console.** A case picker, the question with its client and date, one button, the answer, then the five chunks with the wrong-client ones flagged in red and the cited ones marked. Forty-seven words of interface copy in the whole column, most of them inside blocks that stay hidden. Everything cut was explanation of the exercise, which belongs on the facilitator's slide and in the README, not between a person and the evidence.

**One number, and every term in it is a share.** Superseded by the entry below; the first version was `round(100 x coverage)` minus one point per visible failure, floored at zero. Measured over the ladder on the 29 scored questions: starter 0, matter filter 60, drop the status filter 72, exclusive end date 72, group by source family 86, document-context vector 86, tuned weights 90, tenant-scoped BM25 statistics 91. Every rung moves it, and the starter reads zero because it hands over 90 chunks from other clients' files. An averaged applicability number was deleted earlier in this build for hiding exactly that; subtracting keeps it visible in a single figure a room can shout across a bar.

**"Same source" is now "duplicate", and "wrong date" is now "not in effect".** Duplicate is the plain word. Two other candidates were rejected for the date column. "Superseded" teaches the wrong lesson, because a superseded clause is the correct answer for any question dated while it governed. "Out of force" is not a term commercial practice uses: "in force" belongs to statutes, treaties, and insurance policies, while contracts are "in effect", which is also the word the payload already uses in `effective_from` and `effective_to`. "Expired" would miss half the column, which also counts a clause retrieved for a date before it took effect.

**The playbook was cut from eight rules to seven, and its source is now plain text.** Three rules covered one temporal idea, so the principle and the exclusive end date became one rule with both facts in it. Every rule now states the legal problem in two or three sentences and names no Qdrant feature. "In force" became "in effect" here as everywhere else. The rules live as readable Python in `scripts/panel.py`, which regenerates the encoded `workshop/playbook.py`; the authoring file is withheld from the participant tree. Editing the panel was previously a hand-written encoder, which is why the content went unreviewed for so long.

**Keeping the encoding, with the reason stated plainly.** It stops a grep, which is how a coding agent searches a repository, and the accidental case is the common one: three of the seven rules map onto ladder rungs, so an agent that absorbs them hands back judgment the participant never supplied. It does not stop an agent that decides to decode the blob, and `workshop/playbook.py` says so in its own docstring. The cost that made encoding look like a bad trade, an unreviewable and awkward-to-edit file, is gone now that the source is plain text on the organizer side.

**Every question now names its subject, and none of them names the client's counterparty.** "The platform was down" and "they replaced a part" left a reader asking which platform and who. The fix is "our supplier's platform" and "our supplier replaced a part": the actor is named, the matter is not. Naming Meridian, Tessellate, or Fairweather in every question was measured first and rejected. It identifies the client lexically, which is exactly what the corpus is built to prevent: all three matters carry near-identical clause wording with different numbers, and the leak trap depends on the question not saying whose file it belongs to. Measured, that version dropped the starter from 90 leaked chunks to 50 and cost the tuned configuration six solved questions.

**Two questions left the headroom list, so the scored set is 31.** `cedar-uplift-before` and `cedar-uplift-later` opened with the client's own name. Without it their evidence reaches the top five, and the reference solves both, so ranking people on them is now fair. The remaining six are still measured unreachable, and both ceiling probes are among them. The headroom list has to be re-measured after any question edit: a question that became reachable and stays there is a question nobody is credited for solving.

**Re-measured ladder after the rewrite, over 31 scored questions.** Starter 0 with 97 leaked chunks and 12 solved; matter filter 55 and 17; drop the status filter 69 and 23; exclusive end date 71; deeper pool 71; group by source family 85 and 24; document-context vector 87 and 25; tuned weights 87; tenant-scoped BM25 statistics 89 and 26. The twelve calibration cases keep the property they were chosen for: the same four are solved by the starter, and the same eight flip between the starter and the reference.

**"We" is resolved in the interface, not in the question text.** The question bubble is attributed to the client, "Cedar Labs, in-house legal", so the reader knows who is speaking without a party name in every sentence that would give the matter away.

**Levers are measured one at a time against the best configuration, not as a cumulative ladder.** `uv run python -m workshop.bench --levers` switches every lever on, then switches one off. The cumulative ladder was hiding two things. The candidate pool looked worthless because it was tested before the BM25 statistics were scoped to the matter; it is worth two points after. Weighted fusion looked like a lever because it was tested in a position where nothing contradicted it. Measured properly, all eight surviving levers pay: matter filter 92 points, date filter 28, dropping the status filter 16, grouping 14, tenant-scoped BM25 statistics 5, exclusive end date 3, document-context vector 3, candidate pool 2.

**The reference solution fuses unweighted, and is now 87 with 26 of 31 solved.** Weighting the two dense signals 2:2:1 was worth one question before the BM25 statistics were scoped to the matter, and costs three points after it. One lever changed what another lever was worth, which is the most useful result in this build and is now the thing the slide says. Rejected with numbers: ColBERT costs 15 points, MMR costs 18, both weightings cost 3.

**Two levers pay in counts rather than solved questions, and both stay.** The date filter removes 26 chunks that were not in effect, and the exclusive end date removes three. Neither solves a question by itself. A question that needs the exclusive end date to be solved would need a new corpus fixture, and re-ingesting the collection the day before the workshop is not a trade worth making.

**The story had two narrators, and the app now settles it in one line.** The README called the store a law firm's, while the question bubble attributed the question to the client's in-house team, and nothing on screen said which seat the reader was in or who Meridian was. The frame is stated once under the title: you run retrieval at the firm, every case is a question from one client's in-house team about their own matter, so "we" is the client named on the question. The question now sits under a three-field card, "client asking / about their supplier / as of", because labelled fields answer the question faster than a sentence does. Both names are display only. A counterparty name inside the question text would identify the matter lexically and cost the leak trap, which was measured earlier in this build.

**The agent writes like a legal assistant, not like a retrieval demo.** It was saying "the chunks do not establish", which is our vocabulary leaking into a client-facing answer. The prompt now casts it as a legal assistant writing to the named client about their named supplier: lead with the answer, four sentences at most, plain English, and name the document and section relied on with its number after it, as in "Section 7.2 of the Master Services Agreement [1]". It is told never to mention retrieval or how the documents reached it, and to name the document that would settle the question when the evidence does not. The citation check is unchanged, so a number that points at nothing is still caught.

**The board explains its own zero, and carries three columns instead of five.** A score of 0 next to three solved cases reads as a broken scoreboard until the arithmetic is on screen, so the cards now show the two halves, "29 points of evidence found" and "minus 45 visible failures", with the sentence under them. The three failure counts collapse into one Failures column that names what happened, "3 wrong client" or "4 duplicate", and reads "none" in green when the run is clean. The question text left the rows, because it is on screen the moment a case is opened, and the totals row left too, because the cards say it. "Ceiling probes" became "shown, not scored", with the reason on the same line: no configuration we have tried reaches the evidence for those two, so nobody is ranked on them.

**Vector names state the model and the text, never a verdict.** `dense_weak` and `dense_strong` ranked the representations inside the schema: a participant read "strong" and switched to it without measuring, and "weak" told them the starter was bad before they had seen a result. The six are now `minilm_l6_clause`, `minilm_l6_document`, `mxbai_large_v1`, `bm25`, `splade_pp_v1`, and `colbert_small_v1`. A name now says what a thing is, so deciding whether it helps this corpus takes a measurement. That is a re-ingest, so the collection is `legal_lab_v2` and `legal_lab_v1` stays in place as a rollback.

**The score is a per-case figure, and mixing units was the defect.** Subtracting a count of chunks from a percentage set an exchange rate between them that nothing measured, and it left ordering quality printed but uncounted. A case now scores `100 x (0.75 x coverage + 0.25 x order)` times the usable share of its five slots, and the run's score is the mean. Every term is a share, so they combine honestly; a wrong-client chunk, a chunk that was not in effect, and a duplicate each waste one slot and cost a fifth of that case. The score never looks at how the evidence was retrieved, so two retrievals that return evidence of the same quality score the same, which is asserted in `score.demo()`.

**What the new score changed.** The reference drops from 92 to 87, because its ordering quality is 0.726 and that now counts: there is headroom at the top of the ladder that the old formula hid. The starter reads 21 rather than 0, which is more honest than a floor that made every bad run look identical. Every lever still pays, and two moved: grouping fell from 14 points to 6, and the document-context vector fell to 0.9. That last one is the honest awkward case: it solves a question nothing else reaches, 0.919 coverage against 0.887, and costs ordering quality elsewhere, 0.726 against 0.787. The weights stayed at 0.75 and 0.25 rather than being tuned until that lever looked better, which would be choosing a metric to flatter a result.

**`bench --levers` reports exact differences, not differences of rounded scores.** It printed the document-context vector as "0 pts" while the measured difference was 0.88, because it subtracted two rounded numbers. A lever worth part of a point is not worth zero.

**The browser reports the score and stops talking.** It was writing "4 duplicate of a source already here" and "5 from another client" next to every result, which names the defect and points at the fix before anyone has read a chunk. `source_family` grouping is the hardest lever to find, and a label reading "a source already here" hands it over. The board now carries Score, Evidence Found, and Order, and nothing else. A case with all its controlling evidence in perfect order that still scores 60 is the whole prompt: a team has to open it and read five chunks to find the three slots they cannot use. Each chunk states its client, its heading, and its effective date in plain type, with no colour marking the foreign ones. The three counts stay named in `run score` and in the README, because the scored dimensions are published on purpose: a team has to know what is measured, and is never told which case tripped which one.

## The cleaning pass, 14 September 2026

**Three defects the app had, all found by running it as a participant.**

The browser never picked up an edit to `lab.py`. It imported the module once at startup, so a participant tuning in the browser would change the file, click Run Again, and read the old score. Measured: the terminal read 47 after the matter filter while the running app still read 16. This is the exact feedback failure the calibration set exists to prevent, and the app reintroduced it. `client.lab()` now loads the file from its path on every call. A syntax error in it now reaches the browser as `SyntaxError: '(' was never closed (lab.py, line 78)` instead of a stale number.

The app served one request at a time. A page load fired one second into an answer call took 4.5 seconds, and the agent timeout is 90. `ThreadingHTTPServer` took that to 0.0015 seconds.

The chunk card set the client name in muted grey, at the same weight as the heading, which made the most expensive failure in the exercise the hardest thing to see. It is now ink and medium weight. The CSS already carried `.tag.bad` and `.flags` for a red flag and never emitted either; both are gone.

**The board shows all five columns, reversing the entry above.** Withholding the three counts left the browser saying less than `run score`, the README, and the scoring slide all promised, and sent a participant to the terminal to find out whether a change helped. The line that entry drew was in the wrong place. The counts say how many slots a case wasted; they never say which chunk wasted them, so opening the case and reading its five chunks is still the only diagnosis. The data was already in the `/api/score` payload and simply was not rendered. Four scorecards became two, and a totals row replaced them.

**`lab.py` moved to the top of the repository.** It was one file among fifteen in `workshop/`, all of which are fixed. A participant now sees it on its own at the root, and `git mv` plus a loader in `client.py` was the whole change. `workshop/credentials.py` merged into `workshop/setup.py`, because two files for one encrypt and decrypt pair drift apart.

**The starter score is a range, not a number.** Three runs gave 15, 14, and 11, with 34 to 37 wrong-client chunks and 3 or 4 solved. Three runs of the matter-filtered rung gave 46, 46, 46. The unfiltered starter searches all 3,653 chunks and approximate search returns a slightly different set each time; the filter cuts the candidate set to one matter, which Qdrant resolves exactly. The run sheet quotes ranges now. Two laptops reading a point apart is expected, not a bug report.

**The arrows compare against the previous run, not the first run of the evening.** The state file is `.workshop/last_run.json`, every run overwrites it, and there is nothing to reset. They track the case score rather than coverage, because the score is what a team is trying to move.

**`FACILITATOR.md` and `SLIDES.md` had grown the same content twice**, in different words: the preflight checklist, the legal patterns, the Qdrant glossary, the lever tables, the room prompts, and the post-event steps. They would have drifted by the next run. `SLIDES.md` is now on-screen content plus notes, 18 slides rather than 24, and everything else lives in `FACILITATOR.md`.

## The Codex learner pass, 14 September 2026

Codex reviewed the participant tree as a learner with thirty minutes. Three findings held up under test, and four were declined.

**The shipped playbook printed itself.** `workshop/playbook.py` ships, and its own docstring advertised `uv run python -m workshop.playbook`, which printed all seven rules in plain text. The encoding stopped a grep and then the module handed the rules to anyone who read the docstring and ran the command, which is the first thing an agent pointed at the repository does. The README claim that the rules are written down nowhere else was false. The generated module now renders the panel and runs its self-check, and the print path moved to `scripts/panel.py --show`, which never ships. Encoding was never a security boundary and still is not; what changed is that the participant tree no longer advertises the way around it.

**One rank slot could cost more than one slot.** `case_score` summed the three failure counts, so a chunk that was both another client's and a repeat copy subtracted two fifths for one slot. Measured: one controlling chunk plus two copies of another client's memo scored 40 where the published rule gives 45. `score()` now collects the positions a lawyer could not rely on and counts each once, which took that case to 60. The rule the README states and the rule the code applies are the same rule again. The ladder did not move: the starter still reads 21 over the 31 scored questions and the reference still reads 87, because overlapping faults are rare in practice.

**Order was labeled as ordering alone.** NDCG falls when a controlling chunk is missing, so Order moves with Evidence Found rather than independently. Measured: holding the order identical and dropping one of two controlling chunks took Order from 1.00 to 0.61. The column description, the README, `AGENTS.md`, and the `run score` legend now say so. The weights stay at 0.75 and 0.25.

**`bench` crashed on every grid row.** `row()` read the score through `result.get("score", total(result))`, and Python evaluates that default eagerly, after `main()` had already popped `rows`. So `uv run python -m workshop.bench` raised `KeyError: 'rows'` on the first configuration. The run sheet tells the organizer to reproduce the ladder with this command. It reads `result["score"]` now, which `score_all` always sets.

**Declined, with reasons.** A baseline step before the first edit: the board takes one automatically on the first Run All. A participant-facing API map naming grouping, extra vectors, and tenant IDF: that is the lever ladder, so it is the exercise rather than missing information. Moving the playbook above the fold: it inverts the deliberate order of answer first, evidence second. Labelling the delta arrows as browser-only: true, and the arrows now read from a file both routes write, so they are correct instead of labeled.

**Stale rather than live.** Codex read the open item above about the `legal_lab_v1` key scope and reported it as a live blocker. It was closed and the ledger had not said so. An open-items list nobody closes turns into a false alarm for the next reader.

## The worked solution moves into lab.py, 15 September 2026

**The root `lab.py` is now the solution, and `scripts/starter_lab.py` is what participants receive.** `ship.py` wrote `lab.py` verbatim from the repository root, so a tuned root file would have handed the answer to every laptop in the room on the next rebuild. The starter now lives under `scripts/`, `ship.py` writes it to the participant tree as `lab.py` and strips its organizer note on the way, and it fails loudly if that note is missing. `scripts/reference_lab.py` is deleted, because the root file is the reference and two names for one thing drift apart. `bench --parity` reads the starter explicitly rather than whatever sits at the root.

**A second query that follows `references` is worth seven points.** Measured by switching it off: 81 against 74, and 12 of 14 solved against 10. It solves `cedar-service-credit` and `atlas-substitution-approved`, both of which need a clause and the definition it points at, and no ranking change reaches the second chunk on either. The payload has always carried the field and nothing in the measured ladder had ever used it. The published ceiling moved from 74 to 81 in the README, `AGENTS.md`, and the run sheet.

Both challenge cases stay unsolved, and they are genuinely shut rather than merely hard: the only chunk pointing at the answer to the cure question was replaced before the question date, so a correct date filter removes it.

## The paid models land, and the model was the ceiling after all, 15 September 2026

**The cluster moved to a paid plan and `ingest` filled the last two vectors.** All six representations now carry 3,653 chunks. `ingest` without `--recreate` upserts, so nothing was rebuilt, and it took four minutes.

**The stronger dense model makes the board worse, and that is the interesting half.** Measured on the worked solution: swapping `mxbai_large_v1` in for `minilm_l6_clause` reads 75, adding it as a fourth fusion branch reads 77, against 78 to 81 for the solution that leaves it alone. Adding `splade_pp_v1` as a fourth branch reads 79, inside the same band. Nobody should switch to the big model because it is the big model, which is the habit `vectors.py` was named to break.

**And yet the model was the ceiling for two questions.** `mxbai_large_v1` queried alone, with the matter and date filters and no fusion, retrieves the controlling evidence for `harbor-cure-before` and `cedar-uplift-promotional`, both at rank five, both at full coverage. No other configuration has ever reached either. This closes open item 4: for these two the ceiling was the embedding, not the interface, and the honest test named in `questions.py` has now run.

That leaves a decision rather than a fix. `harbor-cure-before` is one of the two cases the board marks challenge and tells participants nobody has solved. It is solvable, by a configuration that scores worse everywhere else, which is a better lesson than the one currently on the board and a worse fit for the wording. `cedar-uplift-promotional` sits in `HEADROOM_IDS`, which `questions.py` says must not hold a question that became reachable. Both need Dylan's call before the numbers are republished.

**`preflight` no longer reads constants out of `lab.py`.** It checked inference by looking up `DENSE_VECTOR` and `SPARSE_VECTOR` in the participant's file, so renaming a constant broke the health check that exists to explain breakage. The two model ids are fixed in `run.py` now, and `lab.retrieve` is still called at the end as the real check.

## A full sweep of the paid models, and the overfit it nearly caused, 15 September 2026

Eleven realistic configurations, with the filters, grouping, tenant IDF and the reference hop held constant and only the branches, the fusion and the rescore varying.

| Configuration | 14 disclosed | 31 scored |
| --- | --- | --- |
| clause + document + bm25, the worked solution | 81, 12/14 | **93, 30/31** |
| mxbai + document, RRF weighted 3:1 | **87, 13/14** | 77, 24/31 |
| mxbai alone | 80, 12/14 | |
| clause + document + bm25 + splade | 79, 11/14 | |
| clause + document + mxbai + bm25 | 77, 11/14 | |
| mxbai + document + bm25 | 74, 11/14 | |
| clause + document + bm25, DBSF | 72, 10/14 | |
| mxbai + bm25 | 71, 10/14 | |
| any configuration, ColBERT rescore | 63, 9/14 | |

**The configuration that looks six points better on the visible board is sixteen points worse on the questions nobody can see.** `mxbai_large_v1` weighted three to one against the document vector reads 87 and solves thirteen of fourteen, including `harbor-cure-before`, which no other configuration has reached. It was stable across three runs and across neighbouring weights, and on the 31 scored questions it collapses to 77 and 24 of 31.

This is the sharpest result the project has produced, and it nearly went into `lab.py`. It is also the argument for the held-out set, made with numbers: a team tuning against fourteen disclosed cases can find a real, reproducible, stable improvement that is a real, reproducible, stable regression. Worth telling the room.

**ColBERT is a trap at every point on the ladder**, costing eighteen points whether it rescores mxbai, mxbai plus BM25, or the three-way fusion. DBSF costs nine against RRF. SPLADE as a fourth branch costs two and lands inside the solution's own run-to-run band.

**The worked solution reads 93 with 30 of 31 solved on the scored set**, against the 87 and 26 of 31 in the ladder table. The difference is the reference hop, which the ladder predates.

## The vector menu goes in the starter header, 15 September 2026

This reverses "ship ColBERT without telling anyone". That decision made the strongest lever discoverable rather than guessable, and it was written when nobody knew what the extra vectors were worth. The sweep above settles it: ColBERT costs eighteen points at every point on the ladder, mxbai overfits the disclosed board by sixteen points on the scored set, and SPLADE is a wash. There is no hidden good vector to find. The hunt was for four traps.

So the starter now lists all six with the model behind each and recommends nothing. A person or an agent that reaches for ColBERT, measures, and backs it out has learned the thing the workshop claims to teach, in five minutes rather than twenty-five, and the score still decides.

Rejected on the way: commenting the alternatives in as suggestions, to bait an agent into ColBERT. Deliberately false tips teach "the comments were bait" rather than "measure before you switch", and they spend trust in the same hour the room is asked to trust a scoring rubric. The neutral list gets the same outcome without misleading anyone, and it is the position `vectors.py` already argues for in its own docstring.

## Open, for the morning

1. ~~**Scope a read-only key to `legal_lab_v2`.**~~ Done. `preflight` reads `legal_lab_v2` and ends with `ready`, and a package built by `ship.py` runs end to end from a clean directory. `legal_lab_v1` stays in place as the rollback: it holds the same 3,653 chunks under the old vector names.
2. ~~**Attach billing to the cluster.**~~ Done on 15 September. Both vectors are loaded, and the measurement is in the section above.
3. **Keep the read-only key read-only.** `client.py` falls back to the write key when `QDRANT_READONLY_API_KEY` is empty. Thirty laptops must not hold a key that can delete the collection.
4. ~~**"The model is your ceiling" is not yet proven.**~~ Measured on 15 September. It is true for exactly two questions and false for the board as a whole, which is a sharper story than either claim on its own. See the section above.
5. **Rehearse it.** Play the workshop solo and in a pair, and run a coding agent against the shipped tree unattended for thirty minutes and score it. If the agent alone reaches most of what a person reaches, the legal reasoning is decorative and the questions need rebalancing. The tooling for that test is already here: `scripts/ship.py` builds the tree, `workshop/bench.py` scores anything.
6. **The corpus runs slightly denser than the five-second bar.** Clauses average four sentences. The playbook rules hit the bar; chunks such as `harbor-cure` take ten to fifteen seconds. Worth one trimming pass if there is time, and harmless if there is not.
