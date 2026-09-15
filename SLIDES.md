# Qdrant Legal Retrieval Lab

Slide content and the notes that go with each slide. The run sheet, the numbers, and the checks are in `FACILITATOR.md`.

Replace `[REPO URL]` before presenting. Do not show anything after "Stop and Commit Your Result" until the competition ends.

Timing: 15 minutes opening, 30 minutes lab, 15 minutes reveal and debrief.

---

# Welcome to the Legal Retrieval Lab

### On Screen

One client. One dated question. Five chunks.

Can you give an answering agent the evidence it needs without exposing another client's documents?

### Notes

This is a hands-on retrieval exercise, not a presentation about hypothetical AI risk.

> Tonight you inherit a retrieval system that works. It returns fluent, relevant-looking results. It is also wrong in ways it will never report by itself.

Ask everyone to start cloning while you keep going.

---

# Workshop Setup

### On Screen

```bash
git clone [REPO URL]
cd qdrant-legal-lab
uv sync
uv run python -m workshop.setup
```

### Notes

Setup asks for the password you announce, decrypts the Qdrant and OpenAI credentials locally, and runs the connection checks. Nobody creates an account, downloads a model, or ingests anything.

Ask people to stop if setup does not end with `ready`, and fix it before the timer starts.

---

# The Situation

### On Screen

- A law firm stores many clients' documents in one Qdrant collection.
- You run retrieval at the firm.
- A client's in-house team asks about their own matter, on a date.
- An answering agent receives only the five chunks your code returns.
- The agent does not search again.

### Notes

Say who is who once and the questions stop being ambiguous. "We" is the client asking. The other company named is their supplier: Harbor Health Systems buys from Meridian Data Services, Cedar Labs from Tessellate Cloud Systems, Atlas Robotics from Fairweather Components. Both names sit above every question in the app.

The three client matters are fictional. The surrounding contract chunks are real public filings.

---

# The Collection

### On Screen

Three client matters:

- **Harbor Health Systems**, services agreement with Meridian Data Services
- **Cedar Labs**, subscription agreement with Tessellate Cloud Systems
- **Atlas Robotics**, supply agreement with Fairweather Components

Agreements, amendments, orders, schedules, definitions, and memos. Thousands of public contract clauses from other companies fill the rest of the store.

> "Matter" = one client's contract engagement

### Notes

Each matter carries a small history. Some clauses were replaced by amendments, some answers need a referenced definition or schedule, and some events only appear in memos.

The public contracts make the collection behave like a busy firm's shared store. Their language can look highly relevant, and it never belongs in an answer about Harbor, Cedar, or Atlas.

Nobody needs to read all of this. Each question asks about one client, one date, and one practical issue.

---

# The Retrieval Task

### On Screen

For each question, return five chunks that are:

1. From the right client
2. Applicable on the question date
3. From the source that proves the rule or the event
4. Complete enough to carry dependencies and exceptions
5. Not repeat copies of the same source

### Notes

The starter retrieves chunks that sound relevant, and that is not enough here. A chunk can be semantically excellent and still unusable: it belongs to another client, it was superseded, it only summarizes the controlling document, or it crowds out a necessary dependency.

---

# This Is Not a Contract Law Test

### On Screen

> You are not being tested on contract law. You are deciding which evidence an answering agent is allowed to rely on.

### Notes

Each case supplies the client, the date, a plain-English question, and five retrieved chunks. The job is to decide whether those five are safe, applicable, and complete.

Legal knowledge helps with source judgment. Qdrant knowledge turns that judgment into retrieval behavior.

---

# Retrieval Decides What the Agent Can Know

### On Screen

Question + Client + Date

↓

Qdrant Retrieval

↓

Five Chunks

↓

Answering Agent

### Notes

The model reasons only over the evidence it receives. If retrieval omits an exception, the model cannot apply it. If retrieval returns another client's clause, the model has no way to know a confidentiality boundary was crossed.

Retrieval behavior is part of agent behavior.

---

# Live Failure

### On Screen

Watch the answer. Then read its evidence.

### Notes

Run it live, without explaining first. The command is in the run sheet.

Pause when the evidence list appears and ask the room: whose contract did the agent receive? Every chunk names the client whose file it came from. Three of the five belong to someone else, and one is another client of the same firm.

Then say it:

> Qdrant returned what the application asked for. The application never expressed the client boundary that Qdrant makes available.

The failure is not that vector search is unsafe. The failure is that the application treated semantic similarity as the whole evidence policy. Do not start explaining filters yet.

---

# Three Principles for Safe Evidence

### On Screen

## Scope the Evidence

Right client. Right date.

## Judge the Source

An agreement proves the rule. A record proves what happened.

## Return the Whole Answer

Keep independent sources. Follow definitions, exceptions, and schedules.

### Notes

These are the three sections of the Evidence Playbook in the browser.

Right date in plain English: a clause marked superseded today may be exactly the clause that applied when an older event happened. Source judgment: five internal notes do not outweigh the agreement they summarize, and a quality memo may be the only record of whether an inspection passed.

Do not name the Qdrant implementation for any principle.

---

# How You Are Scored

### On Screen

**Score out of 100.** Evidence found and graded ranking, over the slots you can use.

1. **Evidence Found:** the controlling chunks you retrieved. This ranks you.
2. **Graded Ranking (NDCG@5):** did the best evidence come first? Tiebreaker. It also falls when a controlling chunk is missing.
3. **Drive these to zero:** Wrong Client, Not in Effect, Duplicate.

### Notes

Each case scores `100 x (0.75 x evidence found + 0.25 x graded ranking)`, times the share of its five slots a lawyer could use. The run's score is the mean.

Every term is a share, so two retrievals that return the same quality of evidence score the same whatever produced them. One other-client chunk costs a fifth of that case, because it is a confidentiality failure rather than a slightly worse average.

"Solved" means every controlling chunk for that case reached the top five.

---

# Your Working Loop

### On Screen

1. Choose a supplied case.
2. Ask the agent and read the answer.
3. Read the five chunks it was built from.
4. Change one retrieval choice in `lab.py`.
5. Run all 12 cases, and keep the change only if the score improves.

```bash
uv run python -m workshop.app       # http://localhost:8000
uv run python -m workshop.run score # or stay in the terminal
```

### Notes

The browser opens on the agent. The answer comes first, and the chunks under it carry the client, the dates, and which ones the agent cited. Reading a fluent answer and then the other client's contract it was built from is the whole point.

`lab.py` sits at the top of the repository on its own. It is the only file they change, and the app re-reads it on every run.

---

# Coding Agents Are Allowed

### On Screen

A generic coding request is not an evidence policy.

Tell your agent:

- What you observed
- What safe evidence means
- What the collection contains
- To inspect current Qdrant capabilities
- To measure every change

### Notes

> The interesting comparison is not human against model. It is a generic coding request against an agent that has been given domain policy, system context, and an evaluation loop.

The Evidence Playbook is in the browser and not in the repository, so an agent only gets it if a person reads it and passes it on. Do not hand out a complete prompt or name the winning features.

---

# The Lab Starts Now

### On Screen

30 minutes

`lab.py`

`http://localhost:8000`

Primary goal: evidence coverage

Visible failures: zero

### Notes

Start the timer and stop presenting. Solo or pairs. Walk the room. The unsticking prompts are in the run sheet.

---

# Stop and Commit Your Result

### On Screen

Be ready to share:

- One improvement you can defend
- One failure that remains
- The evidence for both

### Notes

Stop the timer. Ask everyone to run the calibration set once more. Collect the leading scores, and also find the teams who can explain a real improvement or a real failure. Do not reward score alone.

---

# The Reveal: Same Agent, Different Evidence

### On Screen

Are we cleared to build with the new 8841-C connector?

Same question. Same answering agent.

### Notes

Run the question with the starter. Five results come back with the same title, and the agent says the evidence does not settle it. Let the room read the five identical lines.

Copy `scripts/reference_lab.py` over `lab.py` and run the identical command. Now the agent answers:

> No. Production requires a passing first-article inspection of 30 units and written confirmation from the buyer's quality engineer. The inspection failed, and no confirmation was issued.

The Engineering Change Notice proves the rule. The quality memo proves the inspection result. The repeated approval notes prove neither.

The first answer was not a hallucination. The model behaved well both times. It was handed five copies of one opinion and it said so. The evidence changed, and nothing else did.

---

# What the Experiments Showed

### On Screen

| Lever | Worth | Solves |
| --- | ---: | ---: |
| Filter by matter | 64 points | 15 questions |
| Filter on the effective dates | 17 points | 1, and 26 wrong-date chunks |
| Keep historical versions reachable | 15 points | 6 questions |
| Group repeated sources | 6 points | 2 questions |
| Scope BM25 statistics to the matter | 4 points | 3 questions |
| Fix the date boundary | 2 points | 3 wrong-date chunks |
| Raise the candidate pool | 2 points | 1 question |
| Add the document-context vector | 0.9 points | 1 question |

### Notes

Every row is measured with every other lever switched on, so no lever is credited for a gain that belongs to the one before it. Do not read the rows. Say what changed: the client boundary first, then date logic, then grouping, then the statistics.

The reference retrieval solves 12 more questions than the starter and removes 97 wrong-client results and nine repeat sources. Two changes remove visible failures without solving anything new. In a legal workflow, removing those failures is part of the result.

---

# Legal Judgment Becomes Retrieval Logic

### On Screen

| Legal question | Retrieval control |
| --- | --- |
| Whose documents are eligible? | Payload filters |
| Which version applied on that date? | Date ranges |
| Which wording and meaning matter? | Dense and sparse named vectors, fused |
| Are these independent sources? | Grouping by source family |
| Is this term unusual for this client? | Tenant-scoped inverse document frequency |

### Notes

Qdrant exposes retrieval as controls the application combines at query time. Dense search finds similar meaning, BM25 rewards distinctive terms, named vectors hold the clause body and the clause with its title and heading separately, fusion combines candidate lists, and grouping expresses the rule that repeat copies are one source.

No single control supplies the legal judgment. Together they let the application express the judgment the legal team defined.

---

# Measured, Not Assumed

### On Screen

Is a term rare across the whole firm's collection, or rare inside this client's matter?

Those are different statistical questions.

Also measured: ColBERT reranking lost four solved cases. Maximum Marginal Relevance got worse as diversity rose. A document-type authority boost did nothing after grouping.

### Notes

BM25 gives more weight to uncommon terms, and those statistics normally cover the whole shard. Qdrant 1.19 calculates them over a filtered corpus instead, which here is one client matter. It moved the result from 25/31 to 26/31 solved, and from 83 to 87 points. The feature earned its place because the experiment measured it.

It also changed what another lever was worth: weighting the dense signals above BM25 gained a question before this change and costs three points after it, so the reference fuses unweighted.

ColBERT and MMR are useful Qdrant capabilities that did not suit this workload. Every change started with an observed failure and a hypothesis, and the score decided whether it stayed.

---

# What the Failures Taught Us

### On Screen

- Similarity cannot enforce a client confidentiality boundary.
- The newest clause may not be the clause that applied on the question date.
- The top-ranked chunk may carry only part of the rule.
- Repeat copies are not independent support.

### Notes

Connect each one to a case they saw. A highly similar clause from another client stays ineligible. A default notice received before an amendment stays under the earlier cure clause. A liability cap points at a definition that removes certain claims from it, and either chunk alone is incomplete. Five connector approval notes repeat one internal view and replace neither the Engineering Change Notice nor the failed inspection record.

Good retrieval buys more than a fluent answer. It gives reviewers a traceable set of sources and lets an agent stop when the documents do not settle the issue.

---

# One Workflow to Take Home

### On Screen

Think of one workflow you know:

- What makes a source eligible?
- Which date controls?
- Which documents must travel together?
- What counts as the same source?

### Notes

Give the room a minute, then ask two or three people to share. Connect their answers to retrieval controls rather than designing an architecture on the spot.

Recognize best overall coverage, largest improvement from the starter, and best explanation of a remaining failure.

Close on the opening demo:

> The answering model only got its turn after retrieval. Tonight you changed the evidence it received, and 12 more questions became answerable. What could better retrieval change in your own work?
