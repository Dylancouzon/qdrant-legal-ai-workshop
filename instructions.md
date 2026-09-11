> **Approved Redesign (September 2026):** The user has authorized an agent-based workshop for mixed legal tech workers. The current build uses Qdrant and LangGraph with three progressive investigations: Missing Authority, Outdated Sources, and False Consensus. This supersedes the original two-challenge limit and evidence-only main experience. The main experience uses a live model when configured; an explicitly labeled evidence-only fallback remains available. The user also replaced student VMs with two complete participation paths: facilitator-led follow-along without setup, and optional repository clone with shared read-only Qdrant Cloud access or participant-owned ingestion. The revised schedule and participant experience appear in WORKSHOP.md. Preserve the original brief below as project history; apply its other requirements where compatible.

# Build Instructions: Fix the Search

## Your Task

Build a complete, working workshop application in this repository. Implement and verify the experience; do not stop at a proposal or mockup. First inspect the repository and its instructions, reuse an appropriate existing stack, and preserve unrelated work. Make reasonable implementation decisions without repeatedly asking for confirmation. Document assumptions and any genuine blockers.

Create `outline.md` for the opening Qdrant introduction. **Only create an outline for this introduction. Do not create slides or a slide application.** The presenter will create the slides separately.

## Workshop Context

- Audience: primarily legal tech engineers.
- Duration: 60 minutes maximum, including the introduction and debrief.
- Environment: Hackersquad provides each attendee with a VM through a link. Qdrant can be preinstalled, collections preloaded, and the IDE includes an AI coding assistant.
- Attendees should not need to install dependencies, obtain credentials, load data, or manually write code during the workshop.
- They may use the IDE assistant to inspect and modify the implementation. The exercise is about diagnosis and evidence, not syntax.
- The preceding talk asks how organizations can turn human judgment into executable work, and what must be true before trusting AI inside that work.
- This workshop narrows that question to retrieval: does the assistant receive the right evidence?

## Concept and Scope

Title: **Fix the Search**.

The participant-facing explanation should fit in this paragraph:

> This assistant gives plausible answers, but sometimes retrieves the wrong evidence. Find out why, fix its search, and show that the fix works on another question. You can use the AI coding assistant for anything.

Build one legal question-answering application and two challenges. Keep the experience lightweight and understandable within a few minutes. Participants may work individually or in pairs.

Do not add assigned roles, leaderboards, tokens, submission budgets, approval ceremonies, elaborate scoring, or a third challenge. Do not build a notebook exercise. Do not require a chat-based agent to navigate the workshop itself.

## Schedule

| Minutes | Activity |
| --- | --- |
| 0–10 | Qdrant introduction using a concrete contract question |
| 10–15 | Open the environment and demonstrate evidence inspection |
| 15–30 | Challenge one: find the right contract |
| 30–45 | Challenge two: find the missing clause |
| 45–53 | Reveal additional questions and test fixes |
| 53–60 | Compare results and debrief |

## Participant Application

Provide a browser application, ready to open in the VM, with these core elements:

1. A short challenge brief and a prefilled question.
2. The assistant's answer with inspectable citations.
3. The retrieved passages in retrieval order, showing source text and useful metadata, including matter/customer, document identifier, and section identifier.
4. A **Test My Fix** button that runs a small evaluation set against the current retrieval implementation.
5. An understandable before-and-after comparison of retrieved evidence and test results.

Explain failures in terms of evidence: wrong matter, missing decisive passage, or a previously passing question that now fails. A green badge alone is insufficient. Distinguish retrieval scores from confidence or correctness; never present similarity as a probability that an answer is true.

Keep the interface simple. Put technical detail behind optional expansion. Provide loading, empty-result, and service-error states. Make long passages and citations readable without crowding the page.

Participants should modify a small, clearly documented retrieval module or configuration using the IDE assistant. They should not have to navigate a large codebase. Include plain-language guidance on where the search behavior lives, but do not expose the solution in the initial challenge brief.

Keep the answer model and prompt constant during the exercises so that retrieval changes can be observed. Challenge two should retain the correct matter scoping learned in challenge one. Provide independent checkpoints so anyone who falls behind can start challenge two with matter scoping already fixed.

## Challenge One: Find the Right Contract

Initial symptom: a convincing answer cites a different customer's agreement.

Example mission card:

> The assistant says termination requires 60 days' notice. The account team thinks that's wrong. Find the evidence, repair the search, and check that another customer's question still works.

Required design:

- Use several synthetic customer agreements with similar language but meaningfully different notice periods or termination conditions.
- The selected matter must be explicit application context, not something guessed from the question by a model.
- The initial retrieval implementation fails to constrain results to that matter.
- Author and test the corpus so the wrong-matter result occurs reliably with the actual retrieval stack. Do not fabricate search results in the UI.
- The intended repair applies the appropriate Qdrant payload filter to every relevant retrieval path.
- Tests must include another customer so hardcoding the first customer's identifier does not pass.
- Clearly explain in facilitator materials that this is an intentionally flawed training search configuration. It is not a production authorization design.

Learning outcome: semantic relevance does not establish whether evidence is applicable to the current matter.

## Challenge Two: Find the Missing Clause

Initial symptom: search retrieves general termination language but misses a decisive clause referenced by a precise identifier.

Required design:

- Start with matter filtering working.
- Include a specific section, clause, or exhibit identifier whose passage changes the answer under the supplied fictional rules.
- Include both identifier-heavy questions and questions phrased in natural-language paraphrases.
- Allow participants to implement or compare dense semantic retrieval, lexical/sparse retrieval, and hybrid retrieval in Qdrant.
- Use real dense and sparse representations and Qdrant's supported query/fusion facilities. Verify current APIs against official documentation before implementation.
- Make the dataset demonstrate a real, reproducible retrieval failure and improvement. Do not assume hybrid retrieval will automatically outperform every baseline; measure and adjust the exercise honestly.
- Test both identifier-heavy and paraphrased questions so fixing one example is insufficient.
- Keep candidate counts and evaluation criteria explicit and consistent when comparing approaches.

Learning outcome: different query types need different retrieval signals, and a change must be tested beyond the motivating example.

## Data and Evaluation

Use entirely synthetic documents, fictional customers, and a short supplied company playbook. No external legal research or specialist legal knowledge should be necessary. Clearly identify the material as fictional training data.

Choose a small corpus large enough to create credible competing results but small enough for attendees to inspect. Include stable document and passage IDs and explicit metadata. Ensure source text unambiguously supports the expected conclusions.

Create a compact, versioned evaluation set. For each case record the question, matter context, required evidence IDs, prohibited evidence where relevant, and an explanation of why the evidence matters.

Use deterministic source-level checks as the main pass criteria, including required evidence within the context supplied to the answer model and exclusion of wrong-matter evidence. Do not rely solely on an LLM judge or exact matching of generated prose. Label retrieval success honestly; it does not certify every generated answer.

Save the initial baseline and display comparisons against the current implementation. Include at least one additional case per challenge for the final reveal. These may be facilitator-controlled rather than initially visible in the participant interface. They are learning exercises, not secure examinations; no anti-cheating infrastructure is needed.

Verify that:

- Each intended baseline failure occurs reproducibly.
- The intended solution improves the relevant cases.
- Hardcoding a customer or returning only the motivating passage does not satisfy the suite.
- Challenge two's retrieval changes preserve matter filtering.
- Failed dependencies and missing credentials are reported as errors, never successful evaluations.

## Qdrant and VM Preparation

Use a real Qdrant instance and actual queries. Do not substitute an in-memory imitation or canned retrieval results.

Provide organizer-facing setup that installs or checks dependencies, prepares embeddings, loads and indexes the collection, and starts the application. Make preparation repeatable and seeding idempotent. Pin compatible dependencies. Follow existing repository conventions where suitable.

Keep preparation outside attendee time. Support preloaded collections or a reproducible snapshot/restore workflow appropriate to the selected Qdrant version. Do not assume a specific Hackersquad API, domain, port-routing scheme, or deployment interface that has not been provided. Document VM requirements, ports, environment variables, start commands, and readiness checks for the organizer.

Prefer practical CPU-compatible defaults. If embedding models need downloads, cache them during VM preparation. Keep any provider credentials on the server and out of source control, browser bundles, logs, and participant documentation.

If live answer generation requires organizer-supplied credentials, provide a clearly labeled extractive evidence-only fallback for development and outages. Never present canned or extracted text as live model generation. Retrieval and evaluation must remain functional without the answer provider.

Provide easy reset and checkpoint commands for the workshop exercise state. Scope resets to workshop files and data, preserve participant changes where feasible, and avoid broad destructive repository commands.

## Required Files and Documentation

Adapt implementation filenames to the repository, but deliver these Markdown files:

### `outline.md`

A concise outline for the presenter's 10-minute Qdrant introduction, including suggested timing, key points, and a proposed demonstration. No slides.

Cover:

- Bridge from the prior talk: trustworthy participation depends in part on receiving the right evidence.
- Opening question: “Can this customer terminate early?” Show two relevant-looking passages from different agreements.
- The path: question → Qdrant retrieves evidence → AI answers.
- What Qdrant solves: search by meaning, lexical signals, and metadata constraints combined to select relevant evidence.
- Why these choices matter for legal applications, with examples rather than sales claims.
- Boundary: Qdrant executes retrieval; the application supplies metadata and policy. Qdrant does not determine legal authority or guarantee answer correctness.
- Transition to the two challenges without revealing their exact repairs.

Include official Qdrant documentation links supporting technical statements. Avoid unsourced performance claims, competitive comparisons, and a broad product feature tour.

### `PARTICIPANT.md`

A short guide containing the one-paragraph premise, how to open the application, how to inspect evidence, where retrieval behavior lives, how to use the IDE assistant, and how to run tests. Ask participants to state a brief hypothesis before changing anything and inspect the result afterward. Keep this conversational, not a form or additional approval step. Do not include full solutions.

### `FACILITATOR.md`

The 60-minute run of show, opening trust vote, both mission briefs, graduated hints, expected diagnoses, final-reveal procedure, debrief points, and recovery steps for participants who fall behind. Include a short readiness checklist and a fallback if the answer provider is unavailable.

### `SOLUTIONS.md`

Working reference repairs, explanations of why they help, expected evaluation outcomes, and common inadequate fixes. Keep this separate from the main participant path; it need not be access-controlled. Provide usable reference checkpoints or patches as appropriate.

### `README.md`

Organizer setup and operation, architecture at a useful level, VM preparation, environment variables, test commands, reset/checkpoint instructions, and known limitations. Update rather than overwrite unrelated existing documentation.

## Verification and Completion

Run meaningful automated checks for seeding, retrieval scoping, evaluation criteria, and both reference solutions. Exercise the full application against real Qdrant. If browser tools are available, verify the participant flow visually, including citations, comparisons, and error states.

Check that a fresh prepared environment opens in the deliberately flawed challenge-one baseline, rather than accidentally starting with the reference solutions applied. Confirm that restarting preserves the intended exercise state and that checkpoints work.

Do not deploy publicly or invent Hackersquad integration details. Deliver a runnable repository and clear VM handoff instructions. In your final response, report what you built, how to start it, what you verified, and any remaining organizer configuration. Be explicit about anything you could not test.
