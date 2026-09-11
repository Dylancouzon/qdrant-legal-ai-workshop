# Facilitate Fix the Search

Offer two complete paths: follow along with your projected live agent, or work in a local repository checkout. The room includes legal tech workers with different technical backgrounds. Everyone can inspect evidence and explain a hypothesis. Let the IDE assistant handle code; keep the conversation about what the investigation needs.

## Ready Before People Arrive

- Complete [organizer preparation](README.md), including a live answer model. Rehearse the projected application and the optional clone-and-connect path.
- Run `uv run --frozen --env-file .env python -m workshop.cli verify` against real Qdrant. Then run a live question and inspect its cited answer and activity trace. Deterministic retrieval tests alone don't verify live generation.
- Restore `uv run --frozen --env-file .env python -m workshop.cli checkpoint baseline` and run `uv run --frozen --env-file .env python -m workshop.cli reveal off`. Confirm initial evidence, **Test My Fix**, citations, and comparisons.
- Confirm your prepared collection and live model. If offering shared Qdrant Cloud access, provide only an appropriately collection-scoped read-only credential. Keep admin and model-provider keys private. Have the recovery commands ready.
- Know how to select the explicitly labeled evidence-only fallback. A failed model request isn't a successful investigation.

## The 60-Minute Run of Show

| Minutes | Lead the Room | Watch For |
| --- | --- | --- |
| 0–8 | Follow [the opening outline](outline.md). Take the initial trust vote before opening sources. | Fluent language earns trust before anyone checks applicability. |
| 8–15 | Orient both paths. Open the projected app; hands-on participants open their local app. Demonstrate one citation, source metadata, the agent's activity, and a baseline comparison. State a short hypothesis aloud. | Everyone can inspect a passage; hands-on participants can locate the small retrieval configuration. |
| 15–25 | **Missing Authority.** Ask what document would change the answer. Offer one hint at a time. | A relevant summary substitutes for the controlling instrument. |
| 25–35 | **Outdated Sources.** Preserve the first repair or use the `authority` checkpoint. Ask which source applies on the question's date. | Participants choose “newest” without checking effective intervals. |
| 35–45 | **False Consensus.** Preserve prior repairs or use `freshness`. Compare independent records and repeated accounts. | More passages get mistaken for stronger corroboration. |
| 45–55 | Reveal additional questions and test all three investigations. Discuss a changed conclusion or a remaining gap. | A fix for one example breaks another matter or historical question. |
| 55–60 | Repeat the trust vote. Invite two short examples and close on the evidence needed for action. | A conditional conclusion can be better supported than a confident yes. |

## Missing Authority

> The assistant has relevant sources, but may have missed the instrument that controls the answer. Find the missing authority and repair how it obtains evidence.

Expected diagnosis: the first retrieval is incomplete. Precise references and ordinary-language descriptions require different signals; following a retrieved document's reference can obtain decisive material outside the first result set.

Graduated hints:

1. “Which instrument would you need before relying on this answer? Does a retrieved passage name it?”
2. “Compare a precise reference with a paraphrase. Inspect both search results and follow-up activity.”
3. “Inspect the search mode and reference-following behavior in `workshop/retrieval.py`. Keep matter scoping intact and test another question.”

Accept repairs based on measured results. Hybrid isn't automatically superior; participants should explain what it retrieved and why reference following mattered.

## Outdated Sources

> The assistant found the source. Does that source apply on the date in the question?

In the projected app, and in each hands-on checkout, confirm the authority repair works or run `uv run --frozen --env-file .env python -m workshop.cli checkpoint authority`. Refresh and select investigation two.

Expected diagnosis: publication availability and effective intervals determine eligibility. A source published after the question date cannot supply contemporaneous evidence. A later document can be inapplicable to a historical question; an earlier document can remain correct for that date. “Newest wins” isn't the rule.

1. “Compare the question date, effective dates, and document status.”
2. “Trace the date through initial search and referenced-document retrieval. Do both paths apply the same rule?”
3. “Inspect applicability filtering. Use the supplied metadata and playbook, then test a historical question as well as a current one.”

The model may correctly resolve mixed old/current evidence in the flawed baseline. Don't claim every generated answer must be wrong: the failure is unreliable context. Conversely, a repaired context doesn't prevent a small model from misreading a condition. Inspect the evidence and its interpretation separately.

The exercise uses explicit fictional rules. In practice, people must establish authoritative source relationships and applicable policy before encoding them. Qdrant executes those constraints; it doesn't decide their legal meaning.

## False Consensus

> Several passages support the answer. Are they independent evidence, and what might change the conclusion?

Confirm the first two repairs work or run `uv run --frozen --env-file .env python -m workshop.cli checkpoint freshness`. Refresh and select investigation three.

Expected diagnosis: repeated accounts crowd out distinct sources, and a search aimed only at support misses competing evidence. Source sufficiency requires examining provenance and unresolved conditions, not counting passages.

1. “Who originated each claim? Which passages repeat the same account?”
2. “What search would test the preliminary conclusion? What source could challenge it?”
3. “Inspect targeted countersearch, source deduplication, and the sufficiency check. Keep prior applicability constraints on every path.”

Countersearch retrieves candidate evidence for inspection; it doesn't prove a contradiction. Deduplication makes room for distinct sources; it doesn't establish credibility. The answer should retain unresolved conditions when the packet doesn't establish them.

## Reveal and Compare

At minute 45, run `uv run --frozen --env-file .env python -m workshop.cli reveal on` in the projected app checkout. Hands-on participants run the same command in their checkout, optionally using the IDE assistant. Refresh, select each investigation in turn, and run **Test My Fix**. CLI users need `--challenge 1`, `2`, or `3` and `--reveal`.

The deterministic reference results are Missing Authority 0/3 → 3/3, Outdated Sources 1/3 → 3/3, and False Consensus 0/3 → 3/3, including reveal cases. A live brief is a separate artifact to inspect.

Ask: “Which required source entered the context? Which inapplicable source left? Did an independent record change the conclusion? What remains unproven?” Read the case explanation rather than only the pass count. These are learning questions, not a secure examination.

## Recover Without Losing the Room

- **Behind:** join the projected investigation immediately, or use `checkpoint authority` for investigation two or `checkpoint freshness` for investigation three. Checkpoints back up the retrieval configuration before replacing it.
- **Broken edit:** restore a checkpoint or copy the desired file from `.workshop/backups/` to `workshop/retrieval.py`. Don't reset the repository.
- **Live model unavailable:** report the error and explicitly choose evidence-only mode. Discuss the real retrieved sources; do not describe deterministic planning or extracts as a live model run.
- **Qdrant or embedding cache unavailable:** use the README readiness steps. Retrieval failures are errors, never passing evaluations. Discuss the local fictional packet while services recover.
- **Reference demonstration:** use `checkpoint solution`. Before another group arrives, restore `checkpoint baseline` and `reveal off`.

## Close with the Decision

Choose two questions:

- “Which source changed what you could responsibly recommend?”
- “What did the agent need to look for after its first search?”
- “When did more evidence fail to mean better evidence?”
- “What does this passing suite establish, and what still needs human judgment?”

The practical Qdrant connection: participants changed eligible sources and retrieval signals, obtained missing or competing records, and measured the resulting context. The graph organized the investigation; the evidence determined what the answer could support.
