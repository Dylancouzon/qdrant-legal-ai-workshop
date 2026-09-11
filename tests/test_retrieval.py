"""Integration checks require the prepared real Qdrant server and cached model."""

import pytest
from workshop import engine
from workshop.data import CASES, PASSAGES
from workshop.evaluation import check, verify, evaluate
from workshop.cli import checkpoint


@pytest.mark.parametrize("mode", ["dense", "sparse", "hybrid"])
@pytest.mark.parametrize("matter", ["harbor", "cedar", "atlas"])
def test_all_search_paths_enforce_matter(mode, matter):
    cfg = dict(engine.SOLUTION, SEARCH_MODE=mode)
    result = engine.retrieve("termination ZX-47", matter, "2026-09-01", cfg)
    assert result["evidence"]
    assert all(p["matter_id"] == matter for p in result["evidence"])
    assert result["trace"][0]["candidates"][mode if mode != "hybrid" else "fused"]


def test_reference_fetch_cannot_cross_matter_or_date():
    malicious = [
        dict(
            passage_id="probe",
            references=[
                "cedar-rider",
                "harbor-termination-old",
                "harbor-termination-current",
            ],
        )
    ]
    result = engine.fetch_references(malicious, "harbor", "2026-09-01", engine.SOLUTION)
    assert [p["passage_id"] for p in result["evidence"]] == [
        "harbor-termination-current"
    ]
    historical = engine.fetch_references(
        malicious, "harbor", "2026-03-01", engine.SOLUTION
    )
    assert [p["passage_id"] for p in historical["evidence"]] == [
        "harbor-termination-old"
    ]


def test_reference_chain_is_explicit_and_scoped():
    rider = next(p for p in PASSAGES if p["passage_id"] == "harbor-rider")
    first = engine.fetch_references([rider], "harbor", "2026-09-01", engine.AUTHORITY)[
        "evidence"
    ]
    assert [p["passage_id"] for p in first] == ["harbor-acceptance"]
    second = engine.fetch_references(
        [rider, *first], "harbor", "2026-09-01", engine.AUTHORITY
    )["evidence"]
    assert {p["passage_id"] for p in second} == {
        "harbor-attempt-log",
        "harbor-correction-log",
    }


def test_seed_idempotent_and_indexes_present():
    assert engine.seed() == len(PASSAGES) == 66
    assert engine.seed() == 66
    q = engine.client()
    try:
        assert {"matter_id", "passage_id", "valid_from_day", "valid_to_day"} <= set(
            q.get_collection(engine.COLLECTION).payload_schema
        )
        assert engine.ready(q)
    finally:
        q.close()


def test_deduplication_keeps_primary_sections():
    rows = [p for p in PASSAGES if p["matter_id"] == "harbor"]
    deduped = engine.deduplicate(rows)
    assert len(deduped) == len(rows) - 4
    assert {"harbor-breach", "harbor-procedure"} <= {p["passage_id"] for p in deduped}


def test_source_checks_reject_missing_scope_and_copies():
    consensus = next(c for c in CASES if c["id"] == "consensus-ready")
    adverse = next(p for p in PASSAGES if p["passage_id"] == "harbor-adverse-report")
    assert check(consensus, [adverse])["passed"]
    copies = [
        p
        for p in PASSAGES
        if p["passage_id"] in ("harbor-support-copy-1", "harbor-support-copy-2")
    ]
    assert not check(consensus, [adverse, *copies])["passed"]
    assert not check(consensus, [])["passed"]
    wrong = next(p for p in PASSAGES if p["passage_id"] == "cedar-adverse-report")
    assert not check(consensus, [adverse, wrong])["passed"]


def test_checkpoints_reload_and_preserve_original():
    path = engine.ROOT / "workshop/retrieval.py"
    original = path.read_text()
    try:
        for name, cfg in engine.CHECKPOINTS.items():
            result = checkpoint(name)
            assert engine.config() == cfg
            assert __import__("pathlib").Path(result["backup"]).exists()
    finally:
        path.write_text(original)


def test_dependency_error_propagates(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "http://127.0.0.1:1")
    with pytest.raises(Exception):
        engine.retrieve("notice", "harbor", "2026-09-01", engine.SOLUTION)


def test_provenance_error_propagates(monkeypatch):
    monkeypatch.setattr(engine, "PROVENANCE", dict(engine.PROVENANCE, model="wrong"))
    with pytest.raises(RuntimeError, match="not prepared"):
        engine.retrieve("notice", "harbor", "2026-09-01", engine.SOLUTION)


def test_all_reference_repairs_use_real_agent_graph():
    reports = verify()
    assert all(reports[f"{n}-solution"]["passed"] == 3 for n in (1, 2, 3))


def test_evaluation_uses_same_agent_and_reveal():
    public = evaluate(1, config=engine.SOLUTION)
    revealed = evaluate(1, include_reveal=True, config=engine.SOLUTION)
    assert public["current"]["total"] == 2
    assert revealed["current"]["total"] == 3
    assert all(c["current"]["trace"] for c in revealed["cases"])


def test_supersession_boundary_is_exclusive():
    refs = [
        dict(
            passage_id="probe",
            references=["harbor-termination-old", "harbor-termination-current"],
        )
    ]
    june = engine.fetch_references(refs, "harbor", "2026-06-30", engine.SOLUTION)[
        "evidence"
    ]
    july = engine.fetch_references(refs, "harbor", "2026-07-01", engine.SOLUTION)[
        "evidence"
    ]
    assert [p["passage_id"] for p in june] == ["harbor-termination-old"]
    assert [p["passage_id"] for p in july] == ["harbor-termination-current"]


def test_one_motivating_source_does_not_satisfy_suite():
    for challenge, passage_id in [
        (1, "harbor-rider"),
        (2, "harbor-termination-current"),
        (3, "harbor-adverse-report"),
    ]:
        rows = [next(p for p in PASSAGES if p["passage_id"] == passage_id)]
        assert not all(
            check(c, rows)["passed"] for c in CASES if c["challenge"] == challenge
        )


def test_as_of_excludes_later_publication_even_if_effective_interval_matches():
    refs = [dict(passage_id="probe", references=["harbor-file-index", "harbor-rider"])]
    rows = engine.fetch_references(refs, "harbor", "2026-03-01", engine.SOLUTION)[
        "evidence"
    ]
    assert [p["passage_id"] for p in rows] == ["harbor-rider"]


def test_changed_case_invalidates_saved_baseline(monkeypatch):
    import hashlib
    import json
    from workshop import evaluation

    altered = [dict(case) for case in CASES]
    altered[0]["required"] = ["harbor-procedure"]
    altered_hash = hashlib.sha256(
        json.dumps(altered, sort_keys=True).encode()
    ).hexdigest()
    assert altered_hash != evaluation.CASES_HASH
    monkeypatch.setattr(evaluation, "CASES_HASH", altered_hash)
    with pytest.raises(ValueError, match="evaluation version changed"):
        evaluation.load_baseline(1)


def test_connect_cli_uses_only_read_operations_on_real_qdrant(
    monkeypatch, tmp_path, capsys
):
    import json
    import sys
    from workshop import cli, evaluation

    real_client = engine.client
    operations = []

    class ReadOnlyClient:
        def __init__(self):
            self.client = real_client()

        def __getattr__(self, name):
            # An allowlist catches all attempted writes, including new mutation
            # methods that a denylist might miss. Reads still hit real Qdrant.
            assert name in {
                "retrieve",
                "count",
                "query_points",
                "scroll",
                "close",
            }, name
            operations.append(name)
            return getattr(self.client, name)

    q = real_client()
    try:
        before = q.count(engine.COLLECTION, exact=True).count
    finally:
        q.close()
    original_config = (engine.ROOT / "workshop/retrieval.py").read_text()
    monkeypatch.setattr(engine, "client", ReadOnlyClient)
    monkeypatch.setattr(cli, "client", ReadOnlyClient)
    monkeypatch.setattr(evaluation, "STATE_DIR", tmp_path)
    monkeypatch.setenv("FASTEMBED_OFFLINE", "1")
    monkeypatch.setattr(sys, "argv", ["workshop", "connect"])
    cli.main()
    output = json.loads(capsys.readouterr().out)
    assert output["remote_access"] == "read-only"
    assert output["points"] == before == 66
    assert all(
        output["verification"][f"{n}-solution"]["passed"] == 3 for n in (1, 2, 3)
    )
    assert (tmp_path / "baselines-v2.json").exists()
    assert (engine.ROOT / "workshop/retrieval.py").read_text() == original_config
    assert __import__("os").environ["FASTEMBED_OFFLINE"] == "1"
    assert {"query_points", "scroll", "retrieve", "count"} <= set(operations)


def test_connect_incompatible_collection_never_falls_back_to_prepare(monkeypatch):
    from workshop import cli

    def unavailable():
        raise RuntimeError("Collection is not prepared")

    def forbidden_seed():
        pytest.fail("connect must never provision or mutate a collection")

    monkeypatch.setattr(cli, "ready", unavailable)
    monkeypatch.setattr(cli, "seed", forbidden_seed)
    with pytest.raises(RuntimeError, match="not prepared"):
        cli.connect()
