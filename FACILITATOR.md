# Run sheet

What to check, what to say, and what the numbers are. The only organizer document.

## Before anyone arrives

```bash
uv run python -m workshop.run preflight        # must end with "ready"
uv run python scripts/ship.py ../qdrant-legal-lab
```

The collection is `legal_lab_v2`, and a read-only key scoped to `legal_lab_v1` cannot read it. In the Cloud Console, create a read-only key scoped to `legal_lab_v2`, put it in the organizer `.env` as `QDRANT_READONLY_API_KEY`, and run `preflight` before shipping. `ship.py` encrypts whatever that variable holds, so a key with the wrong scope ships a package that fails on every laptop in the room.

Then confirm:

- `ship.py` wrote `.env.enc` and no plaintext `.env`. The password is at least 10 characters and lives outside the repository. Announce it when the lab begins.
- The participant flow works from the generated directory: `uv sync`, then `uv run python -m workshop.setup`.
- The Inference tab in the Cloud Console still lists the models.
- `OPENAI_API_KEY` belongs to a dedicated project with a hard budget cap. Revoke it and the Qdrant key afterwards.
- The repo URL is on a card at each table. Typing a URL from a slide in a dark bar is where the first five minutes go.
- You have a visible 30-minute timer. The root `lab.py` is already the worked solution, so the reveal is a `cd` into this repository rather than a file swap.

## What you need to understand

Three clients, three suppliers, and every question comes from the client side: Harbor Health Systems buys data services from Meridian Data Services, Cedar Labs buys a hosted platform from Tessellate Cloud Systems, and Atlas Robotics buys parts from Fairweather Components. The app names both companies above every question.

You do not need to interpret the contracts or give legal advice. The questions have already been reviewed and labeled. Your job is to help the room see why one piece of evidence belongs in the answer and another does not.

| Pattern | Plain meaning | What can go wrong |
| --- | --- | --- |
| Right client | Use documents from the client named in the question. | A near-perfect clause from another client is still a confidentiality failure. |
| Right date | Use the version that governed when the event happened. | A clause marked superseded may be the correct historical answer. |
| Complete rule | Retrieve the clause and any definition, exception, or schedule it relies on. | One chunk states a rule while another reverses the outcome. |
| Controlling source | An executed agreement usually controls what the parties agreed. | Five internal summaries do not outweigh the agreement they summarize. |
| Record of fact | A memo may be the only evidence of an inspection or other event. | Do not down-rank every memo merely because it is a memo. |

When someone asks which document is legally right: "You do not have to decide from scratch. Read the question, the date, and the top five chunks. The labels reward the source that directly proves the answer."

## The Qdrant ideas in plain English

Use these when someone asks what a piece of code does. You do not need to teach them first.

- **Dense search** finds chunks with similar meaning, even in different words. **BM25** finds distinctive matching words.
- **Named vectors** store several searchable representations of the same chunk. Each is named for the model and the text behind it: `minilm_l6_clause` is the clause body, `minilm_l6_document` is the same model over the title, heading, and body. Nothing in a name says which works better here. That is what the score is for.
- **Prefetch** builds a candidate list from each retrieval method before combining them. **Reciprocal Rank Fusion** combines those lists by position instead of comparing incompatible raw scores. **Weighted RRF** lets a measured, more reliable path count more heavily; it is worth nothing here, and costs three points once BM25 statistics are scoped to the matter.
- **Grouping** allows one result per source family, so forwarded copies of one memo cannot fill the top five.
- **Tenant-scoped inverse document frequency** is a Qdrant 1.19 feature. It calculates how rare a BM25 term is inside one client's matter instead of across every client in the shard.

## Three cases to know cold

Keep these for the debrief. Do not give them to participants during the competition.

**Patient record retention.** The current Exhibit D-2 says clinical records must be kept for seven years. Several internal notes still repeat an earlier three-year period. The exhibit controls because it is the agreed schedule. The repeated notes are one stale source, not five independent opinions.

**Planned maintenance outage.** The service-level clause offers credits for low monthly uptime, but its definition removes announced maintenance from the calculation. A six-hour planned outage earns no credit. Retrieving only the credit clause gives the answer in the wrong direction.

**Connector 8841-C.** Engineering Change Notice 114 allows production only after 30 units pass inspection and the buyer's quality engineer confirms approval in writing. The inspection failed, and no confirmation was issued. Internal line-readiness notes saying "approved" do not remove those conditions. The quality memo matters here because it records the factual inspection result.

## 0 to 15, while they clone

Say the setup in three sentences. A law firm keeps every client's contracts in one store. A client's in-house team asks a dated question about their own matter, so "we" is that client and the other company named is their supplier. The retrieval the room has been given works, and it is wrong in ways it will never tell them.

Then run the demo live. Do not describe it first.

```bash
uv run python -m workshop.run answer \
  "Meridian says we broke the contract and sent us a letter about it on 20 January 2026. How long do we have to put it right before they can walk away?" \
  -m harbor -d 2026-01-20
```

The agent says the chunks do not settle the question. Under the answer is the list of what it was given, with the client that owns each one. Three of the five belong to someone else, and one of those is Cedar Labs, another client of the same firm. That is the whole workshop in one screen: a fluent answer, built on other clients' contracts, from a system that reported no error.

Say the three things they are measured on and stop talking: did you retrieve the evidence that decides the question, did you rank the rest sensibly, and three counts that should be zero. Point at the playbook panel in the app, say it is the legal half and it is not in the repository, and start the clock.

## 15 to 45, the competition

Solo or pairs. They edit `lab.py`, which sits at the top of the repository on its own, and run `score` or use the browser at `localhost:8000`.

The browser opens on the agent. A question goes in, the answer comes out, and the chunks it was built from sit underneath, each stating its client and its dates. A row opens on the client's question and the five chunks that came back for it. The board reports the same five columns as `run score`. It says how many slots a case wasted and never which chunk wasted them, so a case that found everything in perfect order and still scores 60 sends a team to read its five chunks.

Two cases carry a challenge tag and sit in the list with the rest. Nothing we tried reaches their evidence, and they are scored anyway, so the board does not top out at 100. A team reads its number against a real ceiling instead of against a set with the hard cases taken out, and a team that finds a route we did not gets credit for it.

Expect the first run to read 3 or 4 of 14, with 34 to 39 chunks from the wrong client, and a score between 9 and 13. Quote the range rather than a number: the starter searches all 3,653 chunks, and approximate search returns a slightly different set each run, so two laptops running identical code read a few points apart. The matter filter clears every wrong-client chunk and takes the board to 40, steadily, because the filter cuts the candidate set to one matter and Qdrant resolves that exactly. After that the curve steepens. The worked solution in this repository reads 81 with every failure count at zero and 12 of 14 solved. Seven of those points are a second query that follows the `references` payload field, which solves two dependency questions that no ranking change reaches. Both challenge cases stay shut, because the date filter removes the only chunk pointing at the cure answer. If a team calls out a number above 81, ask how they got it. The rules forbid fetching the graded ids out of `workshop/questions.py`, and asking for their `lab.py` is the only enforcement there is.

Walk the room. Prompts that unstick people without giving anything away:

- "Read the top five out loud. Whose contract is that?"
- "That case found every controlling chunk, in the right order, and scores 60. Open it and tell me where the other 40 went."
- "Your board says 74 is the best anyone has reached. Which two cases are holding the ceiling down, and why?"
- "Pick that case at the top of the page and ask the agent. Does the answer say what you would sign your name to?"
- "Your score line says the code uses two of six representations. What are the other four, and which of them helps?"

For teams near the top: "This cluster runs Qdrant 1.19. Should BM25 decide that a word is rare across every client, or inside this client's matter?"

If someone deletes everything marked superseded and their score drops, that is the best conversation in the room. Let them find it.

Encourage coding agents. The useful comparison is a generic coding request against an agent that has been given an evidence policy and an evaluation loop. A participant should tell it what they observed in the browser and ask it to inspect the collection. Do not paste the reference solution or name the winning features. At the end, ask one team what knowledge they had to add before their agent became useful.

## 45 to 55, scoring and the reveal

Run one question twice. First with the starter still in place.

```bash
uv run python -m workshop.run answer "Are we cleared to build with the new 8841-C connector?" \
  -m atlas -d 2026-09-01
```

Five results come back and all five have the same title. The agent answers "not on the documents provided", because the memos point at an Engineering Change Notice and a Supply Agreement section it was never given, and it says so. Stop and let the room read the five identical lines.

Now run the identical command from this repository, whose `lab.py` is the worked solution. Same question, same agent, same model.

> No, Atlas Robotics is not cleared to build with the 8841-C connector. Engineering Change Notice 114 requires a passing first article inspection of thirty units and written confirmation from the quality engineer before production [1], and the quality memorandum records that the inspection failed and no confirmation was issued [2]. The internal line readiness note does not change this.

Nothing about the agent changed. The evidence changed. Say it out loud: the first answer was not a hallucination. The model behaved well both times. It was handed five copies of one opinion and it told you so.

Then three numbers, spoken rather than read off a table. Over the 31 scored questions the starter scores about 21: it solves 12 or 13 and returns roughly 97 chunks belonging to other clients. Filtering by matter takes those 97 to zero and the score to 60. Everything after that, all thirty minutes of it, is worth another nine questions and twenty-seven points.

Hand out the ladder. Do not read it aloud.

One order of discovery, each rung scored over the 31 questions:

| Change | Score | Solved |
| --- | --- | --- |
| starter as shipped | 21 | 13/31 |
| filter by matter | 60 | 17/31 |
| stop filtering on status | 75 | 23/31 |
| treat the end date as exclusive | 76 | 23/31 |
| group by source family | 82 | 24/31 |
| add the document-context vector | 83 | 25/31 |
| scope BM25 statistics to the matter | 87 | 26/31 |
| follow a reference to its definition | 93 | 30/31 |

A cumulative table flatters whatever comes first. What each lever is worth is a different measurement: switch every other lever on, then switch this one off. Reproduce it with `uv run python -m workshop.bench --levers`.

| Lever | Worth | Questions it alone solves |
| --- | --- | --- |
| filter by matter | 64 points | 15 |
| filter on the effective dates | 17 points | 1, and it removes 26 chunks that were not in effect |
| stop filtering on status | 15 points | 6 |
| group by source family | 6 points | 2 |
| scope BM25 statistics to the matter | 4 points | 3 |
| treat the end date as exclusive | 2 points | none, it removes 3 chunks that were not in effect |
| raise the candidate pool to 60 | 2 points | 1 |
| add the document-context vector | 0.9 points | 1 |

Two levers solve no question by themselves and still pay, because they remove defects a reader can see in the result list, and in a legal setting it is the count that gets you sued. The candidate pool is the lever a cumulative table hides: raising it from five to sixty is worth nothing until BM25 statistics are scoped to the matter, and two points after that. Measure levers together or you will teach one of them as useless.

Say what did not work, because that is the more useful half. Every number here is measured.

| Measured and rejected | Costs |
| --- | --- |
| rescore with ColBERT | 13 points, four solved questions |
| diversify with MMR | 17 points, six solved questions |
| weight the fusion 2:2:1 | 3 points |
| weight the fusion 1:1:3 | 2 points, one solved question |
| swap in the larger dense model, mxbai | 16 points on the scored set, six solved questions |

Weighted fusion is the interesting one. Weighting the two dense signals above BM25 was worth a question before BM25 statistics were scoped to the matter, and costs three points after it. One lever changed what another lever was worth, which is why the reference fuses unweighted. An authority prior over document type changes nothing once grouping is on.

Nobody submits anything. People call out the number on their own board, which is the 14-case calibration score, and you take it on trust. The graded chunk ids ship in `workshop/questions.py` because the local scorer needs them, so a team can in principle fetch them by id and read 100. The rules forbid it in one line, and asking the top team for their `lab.py` is the only enforcement there is. The event is honor-based, and saying so out loud costs nothing.

The held-out questions stay in the organizer repository at `workshop/heldout.py`. They are what the ladder below was measured on, and they are the reason the calibration set is small: a team tuning against 14 disclosed cases can overfit, and the ladder tells you what the same change is worth across 31. If you want a check on the top team, ask for their `lab.py` and run it yourself.

## 55 to 60, the debrief

One concrete failure per dimension, each a real chunk anyone can pull up.

**Applicability.** Ask the cure-period question dated 20 January 2026. The correct answer is the original Section 11.1, which is marked superseded. Amendment No. 3 says so in its own words: a notice received before the effective date stays under the old clause. Anyone who filtered on `status == "operative"` threw the answer away, and their score went up on every other question while doing it.

**Controlling evidence.** Ask whether the 8841-C connector is cleared for production. Five internal memos say approved. The Engineering Change Notice says conditionally approved, and a quality memo records that the first article inspection failed. Five documents agreeing is one source repeated, and the two that decide it were below the fold.

**Ranking.** Ask about the liability cap on a data breach. Section 13.1 states the cap and points at Section 1.14 for the carve-out that removes it. Retrieving one without the other produces a confident answer in the wrong direction. Nothing we tried gets both into the top five, which is the honest note to end on: the exercise has a ceiling, and it is where the interesting work starts.

Recognize more than the highest score: largest improvement from the starter, strongest applicability, and best failure explanation. Ask each team for one defensible improvement, one remaining failure, and the evidence for both, and reward the third separately. The team that can explain why ColBERT made things worse has learned more than the team that scored highest.

## After everyone leaves

Revoke the participant Qdrant key and the OpenAI project key. Record which improvements teams found without hints, where they needed help, and whether coding agents found tenant-scoped IDF and what prompting they needed. Re-run `uv run python -m workshop.bench` before changing the corpus, the labels, or the reference solution.
