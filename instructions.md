# Build Brief: Qdrant Legal Retrieval Lab

The original brief, kept as the record of what was asked for. `DECISIONS.md` carries what was built, what it measured, and what changed since.

Instructions for the session that builds this workshop. The repo was stripped to `.git`, `.gitignore`, `.gitattributes`, and `.python-version` on 2026-09-13. The previous version is recoverable at commit `5962901`; its `data.py`, `engine.py`, and `evaluation.py` are worth reading for the corpus metadata design, which was the good part.

## The Event

"Chicago Workshop: Building AI Agents You Can Trust", https://luma.com/p6nyjn29. Hosted by The Superoptimal, The AI Collective, and Code & Coffee. An informal evening event with drinks. Other speakers cover voice agents in legal contexts and evaluation practice (Arize). Qdrant runs the hands-on lab.

Audience: engineers in high-stakes environments, legal engineers building legal products, and search and relevance teams. Mixed technical levels, no ML background assumed. Roughly 30 people with laptops.

Presenter: Dylan Couzon, DevRel at Qdrant. Dylan decides; the build session executes.

## The Format

| Minutes | What Happens |
| --- | --- |
| 0-15 | Slides: vector search, the case, and the rules of the lab. Participants clone and connect while listening. |
| 15-45 | The competition. Solo or in pairs. |
| 45-55 | Scoring, leaderboard, and the reveal of the held-out questions. |
| 55-60 | Debrief on at least one concrete failure per scored dimension. |

## The Concept

A retrieval tuning competition on a legal corpus, and an evidence policy exercise, together. Both, deliberately. A team that only fixes technical defects should not be able to win, and a team that only reasons about legal applicability should not be able to win either.

Participants get a working but deliberately weak Qdrant retrieval setup. They edit exactly one file. They have a local web app where they ask questions, see the ranked chunks, compare against the previous run, and read the playbook. They tune for 30 minutes. At the end a held-out question set produces a score.

## Settled Decisions

**Qdrant Cloud collection, preloaded, for everyone.** No local ingest, no Docker, no re-ingest. This gives a uniform starting line, removes the largest source of night-of failure, allows a bigger corpus, and collapses setup to installing the client and connecting. Dylan will put a read-only, collection-scoped API key in the repo. Confirm it is scoped to read and to that collection only.

**Precompute several representations server-side.** The collection holds six: `minilm_l6_clause` over the clause body, `minilm_l6_document` from the same model over document title plus heading plus text, `mxbai_large_v1`, `bm25`, `splade_pp_v1`, and `colbert_small_v1`. The second dense vector was added after measurement showed that what you embed is a larger lever than which model you use, and it is the difference between 20 and 23 solved questions when combined with fusion weights. Every "upgrade the model" move becomes a one-line query change instead of a re-ingest. This is what makes the Cloud collection strictly better than local.

**Ship ColBERT without telling anyone.** The starter code uses only the weak dense vector and the sparse vector. Late interaction is a large score jump available to anyone who inspects what the collection actually contains. It must be discoverable, not guessable: the app diagnostics panel shows which vectors are in use against the total present, and the editable file's header says the collection may hold more than the starter code uses. That is the only hint.

**One editable file.** Query-time Qdrant code only. Treat it as an interface choice, not a security boundary. Define a stable function signature, validate submissions before the deadline rather than disqualifying at scoring time, and hash the other files as a courtesy check, not as an integrity claim.

**The competition is honor-based and low stakes. Say so.** Do not build organizer-side scoring infrastructure for a 60-minute evening event. Encrypt the held-out questions in the repo from day one so a coding agent cannot read them, announce the password at minute 45, and let people run the scorer locally and call out their number. Do not describe this as strong anti-cheat, because it is not.

**The playbook lives in the web app, not in the repo.** The applicability rules render in the app UI only. A coding agent cannot read them unless the human reads them and pastes them in. This is enforcement rather than etiquette, and it puts the legal reading in the person.

**A small labeled calibration set exists.** This reverses an earlier position. Withholding all feedback does not force legal reasoning, it just removes the ability to tell whether a change helped. The specific failure to avoid: someone deletes the `status == "current"` filter, sees superseded clauses appear, cannot tell whether that is better, and reverts the correct change. Ship enough labeled cases to teach the relevance rubric, and keep the final cases hidden.

**Publish the scored dimensions, keep the questions hidden.** Participants know they will be measured on applicability, controlling evidence coverage, and ranking quality. They do not know the questions.

**The chatbot stays out of the tuning loop.** Fluent text conceals bad evidence, which is the lesson. Use a generated brief in the opening demo, then keep the main loop showing chunks. Reveal generated answers after a team commits its evidence judgment.

**The agent does not retry.** The demo agent makes exactly one retrieval call through the participant's `retrieve()`, with no rephrasing, no query rewriting, and no second attempt. That makes single-shot retrieval quality a faithful measure of the end result, keeps scoring deterministic and free of model cost, and preserves the rule that the chatbot stays out of the tuning loop. Query rewriting is therefore not a participant lever; participants tune Qdrant.

**OpenAI access:** a dedicated project key with a hard budget cap, distributed by QR code, revoked at the end. Retrieval and scoring must work without it.

## Open Items

**The knob menu.** Build the levers, then play the workshop ourselves and balance. The target mix is silent bugs, tuning, and discoverable improvements, where no single category is sufficient to win. Codex argued for cutting the scored track to three interventions because breadth crowds out understanding in 30 minutes; treat that as a hypothesis to test during balancing, not a decision.

**Corpus size.** Start at hundreds of chunks, not thousands. A small set of convincing near-misses is harder and more instructive than a large pile of unrelated text. Grow only if a pilot shows the extra material produces useful failures.

**Where the difficulty floor sits.** The first meaningful win should be reachable in about five minutes, then the curve should steepen. Tune after building.

**Held-out set size.** Start at 30 to 40 questions. Below 20 the gap between second and fifth place is noise.

## The Corpus

Build the evidence relationships first. They are the curriculum; chunk count is a scale choice.

The trap to avoid: assigning invented dates and supersession chains to real contract text does not make the underlying language support those relationships. If the right answer is right only because a metadata field says so, participants learn to obey our database instead of reading evidence.

Build order:

1. Author three to five explicitly fictional matters.
2. Write the amendment, dependency, and applicability histories so the language itself carries the relationship. An amendment must actually read as superseding the clause it supersedes.
3. Bring in authentic excerpts (CUAD is the candidate: 510 real commercial contracts, clause-level spans, CC BY 4.0) only where they stay coherent with the constructed history. Never imply an invented amendment history describes the real agreement.
4. Add unrelated chunks and misleading memo families only after the core cases work.
5. Label everything as fictional workshop material.

Three case constructions carry the domain weight:

**Historical applicability.** A later amendment sits near an earlier governing provision. The question is dated before the amendment applies. A recency boost now has an observable failure case.

**Evidence dependency.** The answer needs both an operative clause and a referenced definition or exception. One attractive chunk is not enough.

**Authority versus repetition.** A duplicated memo family sits alongside the instrument it discusses. Deduplicating by identifier alone should not solve it; recognizing the authority relationship should.

Use matched counterfactual pairs: near-identical wording, different date or matter, different correct evidence.

Before building the competition, validate about a dozen representative questions. For each, write down the required evidence, the tempting wrong evidence, the applicability rationale, and a plausible allowed improvement. If two reviewers cannot agree on those judgments, the corpus is not ready.

## Scoring

Three published dimensions:

1. **Applicability.** Did the returned evidence respect the question's matter and date requirements?
2. **Controlling evidence coverage.** Was the controlling source, or the complete evidence bundle, retrieved?
3. **Ranking quality.** How well were the remaining graded results ordered, accounting for duplicated source families?

Rank on controlling evidence first, ranking quality second. Display both.

Define relevance at the level the exercise cares about, and write it down before annotating: which chunks count as evidence from a controlling document, whether one of two necessary provisions earns partial credit, how duplicate memo copies contribute, and how genuinely alternative evidence is labeled. Annotation choices will otherwise dominate the apparent effect of tuning.

A superseded document is essential to a historical question. "Old material returned" is not inherently a failure, and the scorer must encode that.

Recognize more than one winner: largest improvement, strongest applicability, and best failure explanation. Require a short failure report at submission (one defensible improvement, one remaining failure, the evidence for both) and reward it separately.

## Levers and Planted Bugs

Soft selection. Finalize after the corpus exists and we have measured which ones actually move the score.

**Silent bugs:**

- `avg_len` left at a document-length default on short clause chunks. BM25 and miniCOIL do not compute this server-side, and the default misweights short fields. Little known, no error, real effect. This is the best candidate we have.
- Sparse vector created without the IDF modifier, so boilerplate scores as highly as distinctive terms.
- Dense vectors queried against the wrong distance metric for how they were stored.
- Query embedded without the model's required prefix, where the chosen model needs one.
- `lte` instead of `lt` on the exclusive end of the effective-date interval. Only visible on questions dated exactly at a changeover.
- `status == "current"` in a `must` clause. Looks obviously correct to an engineer and is legally wrong for historical questions. The naive fix makes the score worse on exactly the questions that matter.
- Candidate limit applied before fusion rather than inside the prefetch, so hybrid fuses two tiny pools.

Verify each one empirically on the real corpus before counting it as headroom. Several of these depend on the models finally chosen.

**Tuning and improvements:** payload filters for matter and effective-date interval, fusion choice and RRF `k` and per-prefetch weights, switching to the stronger dense vector, FormulaQuery recency decay, miniCOIL, and the undisclosed ColBERT rescore.

## Verified Qdrant Facts

Checked against the live skills registry and docs on 2026-09-13.

Multiple named dense vectors of different dimensions coexist in one collection, and a query selects one with `using`. Multivectors are configured with `models.MultiVectorConfig(comparator=models.MultiVectorComparator.MAX_SIM)`; MaxSim returns one combined score per point. The late-interaction rescore pattern is a `prefetch` for broad candidates followed by the multivector as the main `query` with `using="colbert"`. Fusion offers RRF, with tunable `k` and per-prefetch weights, and DBSF, which normalizes score distributions using three-sigma endpoints. `FormulaQuery` supports `ExpDecayExpression` over a `DatetimeKeyExpression` on a payload date field; calibrate the decay weight against the scale of the fused score, because decay returns values in zero to one while RRF scores are much smaller.

Cloud Inference embeds both stored documents and queries through the same interface, enabled with `cloud_inference=True` on the client, and handles query and chunk prefixes automatically. Dense and image models are documented; the model list lives in the Inference tab of the Cluster Detail page in the Cloud Console, not in the docs.

Sparse model options are BM25 (cross-domain, long text, needs per-language tokenization, stemming, and stopwords), BM42 (short chunks, English only, no longer maintained), miniCOIL (adds contextual word meaning, English only, needs FastEmbed), and SPLADE++ (term expansion, heavier).

Two constraints worth respecting. Co-locating large multivectors with dense vectors degrades all queries at scale, with reports of 13 seconds dropping to 2 after removing ColBERT at millions of points; put large vectors on disk. Our corpus is hundreds to low thousands of chunks, so this will not bite, but do not let the corpus grow without rechecking. On Qdrant 1.18 and earlier, IDF statistics are computed over the whole shard, which distorts scoring in multi-tenant collections; 1.19 and later support per-tenant IDF. This matters if matters are modeled as tenants.

**To confirm during the build**, because the fetched docs did not show them: the exact syntax for the sparse IDF modifier at collection creation, and whether Cloud Inference covers sparse and late-interaction models or only dense and image. If Cloud Inference does not cover sparse and ColBERT, those vectors must be computed at ingest time with FastEmbed, which is fine because ingest is ours, but query-side sparse and ColBERT embedding would then need a local model and that changes the setup story.

## Build Order

Status as of 14 September 2026. Everything below is built and verified unless marked otherwise.

1. Done. Corpus and evidence relationships, with thirty-seven questions adjudicated rather than the dozen planned. `workshop/corpus.py`, `workshop/validation.py`, `workshop/heldout.py`.
2. Done. Ingest to Qdrant Cloud with six representations. Two of them, `mxbai_large_v1` and `splade_pp_v1`, are declared and wait on cluster billing. `workshop/ingest.py`, `workshop/clausebank.py`.
3. Done. `lab.py` at the top of the repository, one editable file with a stable `retrieve()` signature, and `workshop/bench.py --parity` proves the benchmark runs the same query.
4. Done. `workshop/app.py`, standard library only, Qdrant palette, playbook panel, baseline comparison, and diagnostics that report execution rather than correctness.
5. Done. Twelve calibration questions chosen by measured sensitivity, run by `workshop/run.py score`.
6. Done. Seventeen held-out questions, kept out of the participant tree by `scripts/ship.py` rather than by encryption, and the scorer in `workshop/score.py`.
7. Done. `CLAUDE.md` and `AGENTS.md`.
8. Done. `FACILITATOR.md`, the run sheet with live commands and measured numbers.

Not built, deliberately: organizer-side scoring infrastructure, a leaderboard, a submission flow, and encrypted questions. See `DECISIONS.md`.

## Pre-Workshop Validation

Define what "theoretical maximum" means before quoting a number. Perfect ranking under the labels, the best known implementation, and the best result reachable through the permitted interface are three different quantities. Pick one and name it.

Run Claude Code and Codex unattended for 30 minutes under the one-file constraint and score them. If an agent alone reaches most of the achievable score, the domain knowledge is decorative and the task needs redesign. Note that this test is suggestive rather than conclusive: a low agent score can mean setup friction or unclear instructions rather than a well-designed exercise.

Play the workshop ourselves, solo and in a pair, to balance the knob mix and find the difficulty floor.

## Recorded Disagreement

Codex recommended disclosing on the reveal slide that the held-out questions are weighted toward the intended solution. Dylan declined. The design proceeds without the disclosure. Recorded so the next session does not reopen it.
