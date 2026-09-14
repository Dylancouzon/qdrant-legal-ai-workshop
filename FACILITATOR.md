## Before anyone arrives

```bash
uv run python -m workshop.run preflight     # must end with "ready"
uv run python scripts/ship.py ../qdrant-legal-lab   # rebuild the participant repo
```

Check the Inference tab in the Cloud Console still lists the models. Have the repo URL on a slide and on a card at each table, because typing a URL from a slide in a dark bar is where the first five minutes go.

## 0 to 15, while they clone

Say the setup in three sentences. A law firm keeps every client's contracts in one store. Someone asks a dated question about one client. The retrieval they have been given works, and it is wrong in ways it will never tell them.

Then run the demo live. Do not describe it first.

```bash
uv run python -m workshop.run answer \
  "Meridian says we broke the contract and sent us a letter about it on 20 January 2026. How long do we have to put it right before they can walk away?" \
  -m harbor -d 2026-01-20
```

The agent says the passages do not settle the question. Under the answer is the list of what it was given, and one line reads `OTHER CLIENT`. That is the whole workshop in one screen: a fluent answer, built on another client's contract, from a system that reported no error.

Say the three things they are measured on and stop talking:

- Did you retrieve the evidence that decides the question.
- Did you order the rest sensibly.
- Three counts that should be zero: another client's documents, documents outside their date window, and repeat copies of one memo.

Point at the playbook panel in the app and say it is the legal half and it is not in the repository. Then start the clock.

## 15 to 45, the competition

Solo or pairs. They edit `workshop/lab.py` and run `score`, or use the browser at `localhost:8000`.

Expect the first score to read 3 or 4 of 12 with about 36 leaks. The first fix is worth roughly three questions and takes the leaks to zero. After that the curve steepens.

Walk the room. Two prompts that unstick people without giving anything away:

- "Read the top five out loud. Whose contract is that?"
- "Your score line says the code uses two of six representations. What are the other four?"

If someone deletes everything marked superseded and their score drops, that is the best conversation in the room. Let them find it.

## 45 to 55, scoring and the reveal

Run one question twice. First with the starter still in place.

```bash
uv run python -m workshop.run answer "Are we cleared to build with the new 8841-C connector?" \
  -m atlas -d 2026-09-01
```

Five results come back and all five have the same title. The agent says it cannot tell, because the memos point at documents it was never given. Stop and let the room read the five identical lines.

Now drop in a tuned `lab.py` and run the identical command. Same question, same agent, same model.

> No. You are not cleared to build with the 8841-C connector. Production requires a passing first-article inspection of 30 units and written confirmation from the buyer's quality engineer; the inspection failed, and no confirmation has issued.

It cites the Engineering Change Notice and the quality memorandum, and it says in terms that the line-readiness note does not override them. Nothing about the agent changed. The evidence changed.

That is the whole argument of the evening, and it is worth saying out loud: the first answer was not a hallucination. The model behaved well both times. It was handed five copies of one opinion and it told you so.

Then three numbers, spoken rather than read off a table. The starter solves 13 of 29 and returns 90 passages belonging to other clients. Filtering by matter takes those 90 to zero. Everything after that, all thirty minutes of it, is worth another seven questions.

The full ladder is below. Hand it out or put it on the last slide; do not read it aloud.

| Change | Solved | Leaks | Stale | Dupes |
| --- | --- | --- | --- | --- |
| starter as shipped | 13/29 | 90 | 0 | 9 |
| filter by matter | 17/29 | 0 | 0 | 11 |
| stop filtering on status | 21/29 | 0 | 2 | 11 |
| exclusive end date | 21/29 | 0 | 0 | 11 |
| group by source family | 22/29 | 0 | 0 | 0 |
| add the second dense vector | 23/29 | 0 | 0 | 0 |
| tune the fusion weights | 24/29 | 0 | 0 | 0 |

Two of those rows do not move the solved count and still matter. The exclusive end date takes a real temporal violation to zero, and grouping takes nine duplicate slots to zero. A number that only moves a count is still a defect removed, and in a legal setting it is the count that gets you sued.

Say what did not work, because that is the more useful half. ColBERT is in the collection and costs four solved questions here. MMR gets worse the more diversity you ask for. An authority prior over document type changes nothing once grouping is on. Every one of those was measured rather than assumed, and the log is in the repository.

Held-out questions live in the organizer repository only, at `workshop/heldout.py`. Score each team's `lab.py` against them, or let people call out their calibration number and take it on trust. The event is honour-based and saying so out loud costs nothing.

## 55 to 60, the debrief

One concrete failure per dimension, each one a real passage anyone can pull up.

**Applicability.** Ask the cure-period question dated 20 January 2026. The correct answer is the original Section 11.1, which is marked superseded. Amendment No. 3 says so in its own words: a notice received before the effective date stays under the old clause. Anyone who filtered on `status == "operative"` threw the answer away and their score went up on every other question while doing it.

**Controlling evidence.** Ask whether the 8841-C connector is cleared for production. Five internal memos say approved. The Engineering Change Notice says conditionally approved, and a quality memo records that the first article inspection failed. Five documents agreeing is one source repeated, and the two that decide it were below the fold.

**Ranking.** Ask about the liability cap on a data breach. Section 13.1 states the cap and points at Section 1.14 for the carve-out that removes it. Retrieving one without the other produces a confident answer in the wrong direction. Nothing we tried gets both into the top five, which is the honest note to end on: the exercise has a ceiling, and it is where the interesting work starts.

## Recognise more than one winner

Largest improvement from the starter, strongest applicability, and best failure explanation. Ask each team for one defensible improvement, one remaining failure, and the evidence for both, and reward the third separately. The team that can explain why ColBERT made things worse has learned more than the team that scored highest.
