# Fix the Search

This assistant gives plausible answers, but sometimes retrieves the wrong evidence. Find out why, fix its search, and show that the fix works on another question. You can use the AI coding assistant for anything.

## Open the Case

Choose either path. Both cover the full workshop:

- **Follow along:** no setup. Watch the facilitator's live agent, inspect the displayed sources, and propose the next evidence check. Compare predictions with the result, alone or with a partner.
- **Hands on:** clone this repository and follow [the short setup path](README.md). Use the organizer's preloaded Qdrant connection, or load the small packet into your own instance. Your local app can use explicitly labeled evidence-only mode without downloading an answer model. An IDE assistant can handle edits.

All sources are fictional. You don't need to research real law or obtain a model-provider account.

Check the selected matter and question date. Read the brief and run the prefilled question. In live mode, the agent gathers evidence and generates a cited answer. If the app labels the run **evidence-only**, it is showing a fallback, not live model generation.

## Investigate, Then Change One Thing

1. Open a citation. Read the source, date, status, and relevant passage. Does it support the claim the answer makes?
2. Inspect the agent's activity and retrieved evidence. What did it search for, follow, or miss? Repeated claims may come from one original source.
3. Say a brief hypothesis: “I think this answer is missing ___ because the search ___.” No form to fill out.
4. In follow-along mode, propose the repair for the facilitator to try. Hands-on participants ask the IDE assistant to inspect `workshop/retrieval.py`, explain a possible repair, and make a small change. Save and rerun the question.
5. Select **Test My Fix**. Compare initial and current evidence, then inspect another question. Explain what improved and what remains uncertain.

Try this prompt:

> Read PARTICIPANT.md and workshop/retrieval.py. Help me explain the evidence gap I see before editing. Make one small retrieval change, keep the answer model and prompt fixed, and help me test another question. Don't change the corpus or evaluation rules.

## Three Investigations

**Missing Authority:** The answer sounds relevant. Find the source that could change it.

**Outdated Sources:** The source exists. Work out whether it applies on the question's date. Newer doesn't always mean applicable.

**False Consensus:** Several passages agree. Find out whether they provide independent support and whether the agent missed a competing account.

The facilitator will announce the next investigation and reveal additional questions near the end. If you're stuck, join the projected investigation, ask for a hint, or use the next checkpoint. You'll still have a full next investigation.

## Read the Result, Not Only the Badge

Tests check the evidence supplied to the answer step: required sources, inapplicable material, and case-specific evidence gaps. They do not certify every sentence of a generated answer. Retrieval scores rank results; they aren't confidence percentages.

Use **Test My Fix** during the workshop. For terminal tests, ask the IDE assistant to run `uv run --frozen --env-file .env python -m workshop.cli evaluate --challenge 1`, replacing `1` with `2` or `3` as needed. Add `--reveal` for the additional questions. Keep the retrieval and context budgets fixed when comparing repairs.
