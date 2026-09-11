# Fix the Search: Opening Outline

**Eight minutes. Presenter outline only; no slides.** Open the prepared application and a fictional source packet.

| Time | Say and Show | Invite the Room In |
| --- | --- | --- |
| 0–2 | Bridge from the preceding talk: trustworthy participation in a workflow depends partly on obtaining the right evidence. Ask, “Can this customer terminate early?” Show the matter, question date, and initial cited answer. | “Would you send this to the account team: yes, no, or need more evidence?” Take a quick show of hands. |
| 2–4 | Open a source and follow its reference. Contrast a relevant-looking passage with an applicable controlling instrument. Show why customer, status, and effective dates matter. | “What source could change this answer?” |
| 4–6 | Trace **question + matter + date → agent searches Qdrant → agent follows evidence gaps → cited answer**. Meaning search helps with paraphrases; lexical signals help with precise references; metadata constraints restrict eligible sources. Show one actual search result and its source metadata. | “A source ranks first. What does that tell us, and what doesn't it tell us?” |
| 6–8 | Introduce Missing Authority, Outdated Sources, and False Consensus. Participants repair the evidence-gathering behavior and test another question. Keep the model and answer prompt fixed. | “Your job is to improve the investigation. A well-supported condition or unanswered question is a useful result.” |

## Demonstration Notes

Use actual retrieved passages from the prepared baseline, not staged replacements. Keep the selected matter and question date visible. Show the agent's tool activity as a record of searches and sources, not a window into private reasoning. In fallback mode, explicitly call the output evidence-only and explain that the live model is unavailable.

Qdrant executes retrieval. The application supplies metadata, applicability rules, and source relationships. Qdrant doesn't determine legal authority or guarantee answer correctness. Multiple copies of one claim aren't independent corroboration, and a retrieval score isn't the probability that an answer is true.

## Technical Sources

- [Qdrant vectors](https://qdrant.tech/documentation/manage-data/vectors/): dense and sparse representations.
- [Qdrant payload filtering](https://qdrant.tech/documentation/search/filtering/): exact-match and range constraints on metadata.
- [Qdrant hybrid queries](https://qdrant.tech/documentation/search/hybrid-queries/): combine retrieval branches using supported query and fusion facilities.

Keep the introduction grounded in the case. The workshop measures how these choices affect evidence coverage; it isn't a feature tour or a performance benchmark.
