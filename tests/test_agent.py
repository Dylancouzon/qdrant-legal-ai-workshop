"""Agent-policy tests over real Qdrant. Only generation is stubbed where needed."""

import pytest
from workshop import agent, engine, provider
from workshop.data import CHALLENGES


def question(n=1):
    c = CHALLENGES[n]
    return c["question"], c["matter_id"], c["as_of"]


def test_graph_is_langgraph_and_reference_chain_is_bounded():
    assert type(agent.GRAPH).__name__ == "CompiledStateGraph"
    result = agent.run_agent(*question(), config=engine.SOLUTION)
    ids = {r["passage_id"] for r in result["evidence"]}
    assert {
        "harbor-rider",
        "harbor-acceptance",
        "harbor-attempt-log",
        "harbor-correction-log",
    } <= ids
    assert result["metrics"]["search_calls"] <= agent.MAX_TOOL_CALLS
    assert result["metrics"]["reference_calls"] <= agent.MAX_REFERENCE_HOPS
    assert result["metrics"]["model_calls"] == 0
    assert result["provenance"] == engine.PROVENANCE


def test_invalid_model_citation_fails_closed(monkeypatch):
    def generate(schema, system, payload):
        if schema is provider.InvestigationPlan:
            return schema(
                objectives=["Find the evidence"],
                counter_query="independent operational exceptions",
                followup_query="",
                missing_information=[],
            )
        return schema(
            headline="Unsupported",
            summary="Unsupported",
            claims=[{"text": "Invented authority", "citations": ["invented-id"]}],
            uncertainties=[],
        )

    monkeypatch.setattr(provider, "generate", generate)
    with pytest.raises(provider.ProviderError, match="outside"):
        agent.run_agent(
            *question(), config=engine.SOLUTION, planner_mode="live", answer_mode="live"
        )


def test_model_selected_query_reaches_qdrant_and_weak_countersearch_retries(
    monkeypatch,
):
    selected_query = "Harbor migration readiness assessment rehearsal succeeded no basis portability exit"

    def generate(schema, system, payload):
        if schema is provider.InvestigationPlan:
            return schema(
                objectives=["Check independent evidence"],
                counter_query=selected_query,
                followup_query="",
                missing_information=[],
            )
        row = payload["evidence"][0]
        return schema(
            headline="Inspect the sources",
            summary="Source-based test brief",
            claims=[{"text": row["text"], "citations": [row["passage_id"]]}],
            uncertainties=[],
        )

    monkeypatch.setattr(provider, "generate", generate)
    result = agent.run_agent(
        *question(3), config=engine.SOLUTION, planner_mode="live", answer_mode="live"
    )
    queries = [
        step.get("query") for step in result["trace"] if step["node"] == "countersearch"
    ]
    assert selected_query in queries
    assert engine.counter_query(question(3)[0], "harbor") in queries
    assert "harbor-adverse-report" in {r["passage_id"] for r in result["evidence"]}
    assert result["metrics"]["model_calls"] == 2
    assert result["metrics"]["search_calls"] <= agent.MAX_TOOL_CALLS


def test_provider_failure_never_silently_becomes_evidence_mode(monkeypatch):
    def fail(*args, **kwargs):
        raise provider.ProviderError("Unavailable")

    monkeypatch.setattr(provider, "generate", fail)
    with pytest.raises(provider.ProviderError):
        agent.run_agent(*question(), planner_mode="live", answer_mode="live")
    assert (
        agent.run_agent(
            *question(), planner_mode="deterministic", answer_mode="evidence"
        )["answer"]["mode"]
        == "evidence"
    )
