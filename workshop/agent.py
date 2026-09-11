"""A bounded LangGraph investigation, with observable Qdrant tools.

The participant's retrieval policy is read once per run. The model can propose a
targeted follow-up query; it cannot change matter/date scope or execution limits.
"""

from datetime import date
from time import monotonic
from typing import Any, Callable, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from . import engine, provider
from .data import PLAYBOOK

MAX_REFERENCE_HOPS = 3
MAX_TOOL_CALLS = 6


class InvestigationState(TypedDict, total=False):
    question: str
    matter_id: str
    as_of: str
    config: dict
    planner_mode: str
    answer_mode: str
    plan: dict
    evidence: list[dict]
    trace: list[dict]
    answer: dict
    warnings: list[str]
    tool_calls: int
    model_calls: int
    reference_calls: int
    on_event: Any


def _publish(state, node, title, summary, *, status="complete", **details):
    event = {
        "id": f"step-{len(state['trace']) + 1}",
        "node": node,
        "title": title,
        "summary": summary,
        "status": status,
        **details,
    }
    state["trace"] = [*state["trace"], event]
    if state.get("on_event"):
        state["on_event"]({"type": "step", "step": event})
    return event


def _starting(state, node, title):
    if state.get("on_event"):
        state["on_event"]({"type": "activity", "node": node, "title": title})


def _merge(state, rows):
    existing = {r["passage_id"] for r in state["evidence"]}
    state["evidence"] = [
        *state["evidence"],
        *[r for r in rows if r["passage_id"] not in existing],
    ]


def _tool(state, function, *args, **kwargs):
    if state["tool_calls"] >= MAX_TOOL_CALLS:
        _publish(
            state,
            "assess",
            "Search limit reached",
            "The agent stopped at its declared tool-call budget.",
            status="limited",
        )
        return {"evidence": [], "trace": []}
    started = monotonic()
    result = function(*args, **kwargs)
    state["tool_calls"] += 1
    if function is engine.fetch_references:
        state["reference_calls"] += 1
    for raw in result["trace"]:
        event = dict(raw)
        node = event.pop("node")
        title = event.pop("title")
        summary = event.pop("summary")
        _publish(
            state,
            node,
            title,
            summary,
            duration_ms=round((monotonic() - started) * 1000),
            **event,
        )
    _merge(state, result["evidence"])
    return result


def plan_node(state):
    _publish(
        state,
        "plan",
        "Set the investigation boundary",
        "Use the original question, the selected matter, and the requested as-of date. Hold the answer prompt fixed.",
        query=state["question"],
        matter=state["matter_id"],
        as_of=state["as_of"],
        policy={
            "reference_hops": MAX_REFERENCE_HOPS,
            "tool_calls": MAX_TOOL_CALLS,
            "context_passages": engine.MAX_CONTEXT,
        },
    )
    return state


def retrieve_node(state):
    _starting(state, "retrieve", "Querying Qdrant")
    _tool(
        state,
        engine.retrieve,
        state["question"],
        state["matter_id"],
        state["as_of"],
        state["config"],
    )
    return state


def decide_node(state):
    if state["planner_mode"] == "live":
        _starting(state, "plan", "The model is choosing the next evidence checks")
        proposal = provider.generate(
            provider.InvestigationPlan,
            provider.PLAN_PROMPT,
            {
                "question": state["question"],
                "matter": state["matter_id"],
                "as_of": state["as_of"],
                "playbook": PLAYBOOK,
                "evidence": _model_evidence(state["evidence"]),
            },
        ).model_dump()
        state["model_calls"] += 1
    else:
        proposal = {
            "objectives": [
                "Find the governing source and its conditions",
                "Check applicability and independent contrary evidence",
            ],
            "counter_query": engine.counter_query(
                state["question"], state["matter_id"]
            ),
            "followup_query": "",
            "missing_information": [],
        }
    state["plan"] = proposal
    _publish(
        state,
        "plan",
        "Choose the next evidence checks",
        (
            "Live model-selected search plan."
            if state["planner_mode"] == "live"
            else "Deterministic evaluation plan; no model was called."
        ),
        plan=proposal,
        planner_mode=state["planner_mode"],
    )
    return state


def references_node(state):
    if not state["config"]["FOLLOW_REFERENCES"]:
        _publish(
            state,
            "references",
            "Reference following is off",
            "The current policy stops at the initial passages even when they point to another source.",
            status="skipped",
        )
        return state
    _starting(state, "references", "Following explicit source references")
    attempted = set()
    for hop in range(MAX_REFERENCE_HOPS):
        seen = {r["passage_id"] for r in state["evidence"]}
        pending = []
        for row in state["evidence"]:
            refs = [
                ref
                for ref in row.get("references", [])
                if ref not in seen and ref not in attempted
            ]
            if refs:
                pending.append({**row, "references": refs})
        if (
            not pending
            or state["tool_calls"] >= MAX_TOOL_CALLS - 1
            or state["reference_calls"] >= MAX_REFERENCE_HOPS
        ):
            break
        attempted.update(ref for r in pending for ref in r["references"])
        _tool(
            state,
            engine.fetch_references,
            pending,
            state["matter_id"],
            state["as_of"],
            state["config"],
        )
    # A model may suggest one extra search when the initial result has no links.
    followup = state["plan"].get("followup_query", "").strip()
    if not attempted and followup and state["tool_calls"] < MAX_TOOL_CALLS - 1:
        _tool(
            state,
            engine.retrieve,
            followup,
            state["matter_id"],
            state["as_of"],
            state["config"],
            purpose="followup",
        )
    if not attempted and not followup:
        _publish(
            state,
            "references",
            "No additional references to follow",
            "No unseen explicit source links were present in the current evidence.",
        )
    return state


def counter_node(state):
    if not state["config"]["SEEK_COUNTEREVIDENCE"]:
        _publish(
            state,
            "countersearch",
            "Counter-evidence search is off",
            "This run has not deliberately searched for evidence challenging the first results.",
            status="skipped",
        )
        return state
    _starting(
        state,
        "countersearch",
        "Searching for evidence that could change the conclusion",
    )
    result = _tool(
        state,
        engine.retrieve,
        state["plan"]["counter_query"],
        state["matter_id"],
        state["as_of"],
        state["config"],
        purpose="counterevidence",
    )
    independent = any(
        row.get("kind") == "operational_record" for row in result["evidence"]
    )
    if not independent and state["tool_calls"] < MAX_TOOL_CALLS:
        _publish(
            state,
            "countersearch",
            "Broaden the counter-search",
            "The first counter-search returned no independent operational record. Try one broader evidence query within the same budget.",
        )
        _tool(
            state,
            engine.retrieve,
            engine.counter_query(state["question"], state["matter_id"]),
            state["matter_id"],
            state["as_of"],
            state["config"],
            purpose="counterevidence",
        )
    if (
        state["config"]["FOLLOW_REFERENCES"]
        and state["tool_calls"] < MAX_TOOL_CALLS
        and state["reference_calls"] < MAX_REFERENCE_HOPS
    ):
        seen = {r["passage_id"] for r in state["evidence"]}
        pending = [
            {
                **r,
                "references": [
                    ref for ref in r.get("references", []) if ref not in seen
                ],
            }
            for r in state["evidence"]
            if any(ref not in seen for ref in r.get("references", []))
        ]
        if pending:
            _tool(
                state,
                engine.fetch_references,
                pending,
                state["matter_id"],
                state["as_of"],
                state["config"],
            )
    return state


def assess_node(state):
    before = state["evidence"]
    rows = engine.deduplicate(before) if state["config"]["DEDUPLICATE"] else before
    # Keep new evidence from follow-up tools in the limited context, not only the first hits.
    if len(rows) > engine.MAX_CONTEXT:
        rows = [*rows[:2], *rows[-(engine.MAX_CONTEXT - 2) :]]
    state["evidence"] = rows
    warnings = []
    if not rows:
        warnings.append("No evidence was retrieved.")
    if not state["config"]["CHECK_VERSIONS"]:
        warnings.append("Source applicability was not constrained to the as-of date.")
    if not state["config"]["SEEK_COUNTEREVIDENCE"]:
        warnings.append("The agent did not search deliberately for counter-evidence.")
    families = [
        r["source_family"]
        for r in rows
        if r.get("kind") in {"account_memo", "derived_memo"}
    ]
    if len(families) != len(set(families)):
        warnings.append(
            "The context includes multiple copies of the same account assessment."
        )
    state["warnings"] = warnings
    kept = {r["passage_id"] for r in rows}
    _publish(
        state,
        "assess",
        "Assemble the answer context",
        f"{len(rows)} passages enter the answer step. These are coverage checks, not a legal correctness verdict.",
        evidence_ids=list(r["passage_id"] for r in rows),
        warnings=warnings,
        removed_ids=[r["passage_id"] for r in before if r["passage_id"] not in kept],
        deduplication=state["config"]["DEDUPLICATE"],
        context_limit=engine.MAX_CONTEXT,
    )
    return state


def _model_evidence(rows):
    keys = (
        "passage_id",
        "title",
        "document_id",
        "section_id",
        "text",
        "published_at",
        "valid_from",
        "valid_to",
        "status",
        "source_family",
        "kind",
        "references",
    )
    return [{key: row[key] for key in keys if key in row} for row in rows]


def brief_node(state):
    rows = state["evidence"]
    if state["answer_mode"] == "live":
        _starting(state, "brief", "Writing a brief from the retrieved evidence")
        answer = provider.generate(
            provider.Brief,
            provider.BRIEF_PROMPT,
            {
                "question": state["question"],
                "as_of": state["as_of"],
                "matter": state["matter_id"],
                "playbook": PLAYBOOK,
                "evidence": _model_evidence(rows),
            },
        ).model_dump()
        state["model_calls"] += 1
        known = {r["passage_id"] for r in rows}
        if any(
            cid not in known for claim in answer["claims"] for cid in claim["citations"]
        ):
            raise provider.ProviderError(
                "The model cited a passage outside its retrieved context."
            )
        answer.update(
            mode="generated",
            model=provider.settings()[1],
            citation_check="IDs exist in supplied context; support must still be reviewed",
        )
    else:
        answer = {
            "mode": "evidence",
            "headline": "Inspect the evidence before drawing a conclusion",
            "summary": "Evidence-only fallback: these are source extracts from the same LangGraph retrieval workflow. No model generated this brief.",
            "claims": [
                {"text": r["text"], "citations": [r["passage_id"]]} for r in rows
            ],
            "uncertainties": state["warnings"],
        }
    state["answer"] = answer
    _publish(
        state,
        "brief",
        "Brief ready" if state["answer_mode"] == "live" else "Evidence packet ready",
        "Every displayed citation resolves to a passage supplied to this answer. Check whether the passage supports the claim.",
        evidence_ids=[r["passage_id"] for r in rows],
        mode=answer["mode"],
    )
    return state


def build_graph():
    graph = StateGraph(InvestigationState)
    nodes = [
        ("plan", plan_node),
        ("retrieve", retrieve_node),
        ("decide", decide_node),
        ("references", references_node),
        ("countersearch", counter_node),
        ("assess", assess_node),
        ("brief", brief_node),
    ]
    prior = START
    for name, fn in nodes:
        graph.add_node(name, fn)
        graph.add_edge(prior, name)
        prior = name
    graph.add_edge(prior, END)
    return graph.compile()


GRAPH = build_graph()


def run_agent(
    question: str,
    matter_id: str,
    as_of: str,
    config=None,
    planner_mode="deterministic",
    answer_mode="evidence",
    on_event: Callable[[dict], None] | None = None,
):
    if planner_mode not in {"live", "deterministic"} or answer_mode not in {
        "live",
        "evidence",
    }:
        raise ValueError("Unknown agent execution mode")
    date.fromisoformat(as_of)
    started = monotonic()
    result = GRAPH.invoke(
        {
            "question": question,
            "matter_id": matter_id,
            "as_of": as_of,
            "config": dict(config if config is not None else engine.config()),
            "planner_mode": planner_mode,
            "answer_mode": answer_mode,
            "evidence": [],
            "trace": [],
            "warnings": [],
            "tool_calls": 0,
            "model_calls": 0,
            "reference_calls": 0,
            "on_event": on_event,
        },
        config={"recursion_limit": 20},
    )
    return {
        "run_id": str(uuid4()),
        "question": question,
        "matter": matter_id,
        "as_of": as_of,
        "answer": result["answer"],
        "evidence": result["evidence"],
        "trace": result["trace"],
        "warnings": result["warnings"],
        "config": result["config"],
        "planner_mode": planner_mode,
        "metrics": {
            "search_calls": result["tool_calls"],
            "model_calls": result["model_calls"],
            "reference_calls": result["reference_calls"],
            "elapsed_ms": round((monotonic() - started) * 1000),
        },
        "framework": "LangGraph",
        "retrieval": "Qdrant",
        "agent_version": "investigation-v2",
        "provenance": dict(engine.PROVENANCE),
        "prompt_version": "legal-brief-v2",
    }
