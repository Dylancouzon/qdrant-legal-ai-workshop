"""HTTP integration tests; every successful search uses the real Qdrant server."""

import json

import pytest
from fastapi.testclient import TestClient

from workshop.app import app
from workshop import engine, provider


@pytest.fixture
def http():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def body():
    from workshop.data import CHALLENGES

    case = CHALLENGES[1]
    return {
        "challenge": 1,
        "matter": case["matter_id"],
        "question": case["question"],
        "as_of": case["as_of"],
        "evidence_only": True,
    }


def test_session_has_three_investigations_and_real_stack(http):
    result = http.get("/api/session")
    assert result.status_code == 200
    data = result.json()
    assert [c["id"] for c in data["challenges"]] == [1, 2, 3]
    assert data["collection"]["passages"] == 66
    assert data["budgets"]["tool_calls"] == 6
    assert data["provider"]["mode"] in ("ollama", "openai", "evidence")


def test_stream_contains_actual_tool_trace_and_complete_result(http, body):
    response = http.post("/api/investigate", json=body)
    assert response.status_code == 200
    events = [json.loads(line) for line in response.text.splitlines()]
    steps = [e["step"] for e in events if e["type"] == "step"]
    assert any(
        s.get("qdrant", {}).get("collection") == engine.COLLECTION for s in steps
    )
    result = next(e["result"] for e in events if e["type"] == "result")
    assert result["framework"] == "LangGraph"
    assert result["planner_mode"] == "deterministic"
    assert result["answer"]["mode"] == "evidence"
    assert result["metrics"]["model_calls"] == 0
    assert result["evidence"]
    assert len(result["evidence"]) <= engine.MAX_CONTEXT
    ids = {r["id"] for r in result["evidence"]}
    assert all(
        c in ids for claim in result["answer"]["claims"] for c in claim["citations"]
    )
    assert result["provenance"]["corpus_hash"] == engine.CORPUS_HASH
    saved = http.get("/api/runs/" + result["run_id"])
    assert saved.status_code == 200
    assert saved.json()["trace"] == result["trace"]


def test_compare_is_explicitly_deterministic_and_has_both_traces(http, body):
    result = http.post("/api/compare", json=body)
    assert result.status_code == 200
    result = result.json()
    assert result["mode"] == "deterministic"
    for side in ("before", "after"):
        assert result[side]["metrics"]["model_calls"] == 0
        assert result[side]["trace"] and result[side]["evidence"]


def test_eval_shows_saved_baseline_and_source_explanations(http):
    response = http.post("/api/evaluate", json={"challenge": 1})
    assert response.status_code == 200
    result = response.json()
    assert result["planner_mode"] == "deterministic"
    for case in result["cases"]:
        assert case["explanation"]
        for side in ("baseline", "current"):
            assert case[side]["evidence_ids"] == [
                p["id"] for p in case[side]["evidence"]
            ]


@pytest.mark.parametrize(
    "patch",
    [
        {"challenge": 4},
        {"matter": "not-a-matter"},
        {"question": "   "},
        {"as_of": "not-a-date"},
    ],
)
def test_invalid_requests_are_not_success(http, body, patch):
    assert http.post("/api/investigate", json={**body, **patch}).status_code == 422


def test_model_failure_in_stream_is_an_error_not_fallback(
    http, body, monkeypatch, caplog
):
    def unavailable(*args, **kwargs):
        raise RuntimeError("private-provider-key-must-not-leak")

    monkeypatch.setattr(provider, "generate", unavailable)
    response = http.post("/api/investigate", json={**body, "evidence_only": False})
    events = [json.loads(line) for line in response.text.splitlines()]
    assert any(e["type"] == "error" for e in events)
    assert not any(e["type"] == "result" for e in events)
    assert "private-provider-key" not in response.text + caplog.text


def test_explicit_fallback_does_not_call_model(http, body, monkeypatch):
    monkeypatch.setattr(
        provider, "generate", lambda *a, **kw: pytest.fail("Model called in fallback")
    )
    response = http.post("/api/ask", json=body)
    assert response.status_code == 200
    assert response.json()["answer"]["mode"] == "evidence"


def test_qdrant_failure_does_not_return_evaluation_success(http, monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "http://127.0.0.1:1")
    response = http.post("/api/evaluate", json={"challenge": 1})
    assert response.status_code == 503
    assert "current" not in response.json()


def test_case_file_is_scoped_and_badges_include_publication_date(http):
    response = http.get(
        "/api/sources", params={"matter": "harbor", "as_of": "2026-03-01"}
    )
    assert response.status_code == 200
    rows = response.json()["sources"]
    assert len(rows) == 22 and all(r["matter"] == "harbor" for r in rows)
    by_id = {r["id"]: r for r in rows}
    assert by_id["harbor-termination-old"]["applicable"] is True
    assert by_id["harbor-termination-current"]["applicable"] is False
    assert by_id["harbor-file-index"]["applicable"] is False


def test_reveal_controls_additional_cases(http, monkeypatch):
    import workshop.app as app_module

    monkeypatch.setattr(app_module, "read_state", lambda: {"revealed": False})
    initial = http.post("/api/evaluate", json={"challenge": 3}).json()
    monkeypatch.setattr(app_module, "read_state", lambda: {"revealed": True})
    reveal = http.post("/api/evaluate", json={"challenge": 3}).json()
    assert reveal["current"]["total"] == initial["current"]["total"] + 1
    assert any(c["id"] == "consensus-other" for c in reveal["cases"])
