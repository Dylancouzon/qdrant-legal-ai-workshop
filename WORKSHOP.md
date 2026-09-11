# Fix the Search

**A 60-minute investigation for legal tech workers.** Work individually or in pairs. Choose a complete follow-along experience with no setup, or clone the repository for optional hands-on work. Coding is optional; an IDE assistant can handle implementation changes.

A legal assistant sounds convincing. Its sources tell a different story. Your job is to find what it missed, repair how it gathers evidence, and test whether the repair holds on another question.

## The Case

Work through a fictional customer dispute packet containing agreements, amendments, supporting records, and competing accounts. The application supplies the matter and relevant date. The company playbook explains the exercise's rules; no external research or specialist legal knowledge is necessary.

The assistant runs a bounded investigation using LangGraph. It searches Qdrant, can follow references and seek counterevidence, and produces a cited answer. Its visible activity trace shows the searches and retrieved sources, not private model reasoning. You change the evidence-gathering behavior while the model and answer instructions stay fixed.

## Three Investigations

| Investigation | What Goes Wrong | Your Question |
| --- | --- | --- |
| Missing Authority | Relevant-looking passages omit the instrument that controls the answer. | “What source does this answer depend on, and did the agent obtain it?” |
| Outdated Sources | An attractive result doesn't apply on the question's date. | “Which version applies then, and how do we know?” |
| False Consensus | Repeated claims look like independent support while conflicting or weak evidence goes unexamined. | “Who is the original source, and what could change this conclusion?” |

Qdrant makes the evidence choices concrete: meaning and lexical signals retrieve candidates, payload conditions constrain applicability, and follow-up queries obtain referenced or competing sources. The application supplies metadata and policy. Neither Qdrant nor a fluent answer establishes legal authority by itself.

## The Hour

Eight minutes of introduction, seven minutes to open and inspect the agent, three ten-minute investigations, ten minutes of additional questions, and five minutes to compare conclusions.

In follow-along mode, the facilitator runs the live agent on screen while participants inspect sources, propose hypotheses and repairs, and predict the next result. Hands-on participants run the same investigation in their checkout.

Each investigation follows the same short loop: inspect, state a hypothesis, make one repair, and test it. A recovery checkpoint lets everyone join the next investigation. No leaderboard or assigned roles.

A good finish is a supported conclusion with its remaining conditions stated clearly. “We need this record before recommending action” can be better than a confident answer.

Start with [the participant guide](PARTICIPANT.md). Organizers should use [the README](README.md) and [facilitator guide](FACILITATOR.md).
