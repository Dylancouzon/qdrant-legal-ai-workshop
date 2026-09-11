"""Source checks over the same LangGraph pipeline used by the application."""

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from .data import CASES, VERSION, PASSAGES
from .engine import (
    STATE_DIR,
    BASELINE,
    AUTHORITY,
    FRESHNESS,
    SOLUTION,
    MAX_CONTEXT,
    CANDIDATE_LIMIT,
    PROVENANCE,
    config as active_config,
)

EVALUATION_VERSION = "investigations-v2"
CASES_HASH = hashlib.sha256(json.dumps(CASES, sort_keys=True).encode()).hexdigest()
BASELINES = {1: BASELINE, 2: AUTHORITY, 3: FRESHNESS}
REPAIRS = {1: AUTHORITY, 2: FRESHNESS, 3: SOLUTION}


def check(case, evidence):
    ids = [r["passage_id"] for r in evidence]
    issues = []
    missing = sorted(set(case["required"]) - set(ids))
    wrong = [r["passage_id"] for r in evidence if r["matter_id"] != case["matter_id"]]
    prohibited = sorted(set(case["prohibited"]) & set(ids))
    if missing:
        issues.append("Missing decisive passage: " + ", ".join(missing))
    if wrong:
        issues.append("Wrong matter: " + ", ".join(wrong))
    if prohibited:
        issues.append(
            "Inapplicable source for this question/date: " + ", ".join(prohibited)
        )
    if len(evidence) > MAX_CONTEXT:
        issues.append("Context budget exceeded")
    maximum = case.get("max_family_duplicates")
    if maximum:
        families = Counter(
            r["source_family"]
            for r in evidence
            if r["kind"] in ("account_memo", "derived_memo")
        )
        if any(n > maximum for n in families.values()):
            issues.append(
                "False corroboration: repeated copies of the same source remain in context"
            )
    return dict(passed=not issues, evidence_ids=ids, evidence=evidence, issues=issues)


def run_case(case, cfg):
    from .agent import run_agent

    result = run_agent(
        case["question"],
        case["matter_id"],
        case["as_of"],
        config=cfg,
        planner_mode="deterministic",
        answer_mode="evidence",
    )
    checked = check(case, result["evidence"])
    checked["trace"] = result["trace"]
    return checked


def run_cases(challenge, cfg):
    return {c["id"]: run_case(c, cfg) for c in CASES if c["challenge"] == challenge}


def save_baselines():
    STATE_DIR.mkdir(exist_ok=True)
    data = dict(
        version=VERSION,
        evaluation_version=EVALUATION_VERSION,
        cases_hash=CASES_HASH,
        provenance=PROVENANCE,
        created_at=datetime.now(timezone.utc).isoformat(),
        challenges={str(n): run_cases(n, BASELINES[n]) for n in (1, 2, 3)},
    )
    (STATE_DIR / "baselines-v2.json").write_text(json.dumps(data, indent=2))
    return data


def load_baseline(challenge, include_reveal=False):
    data = json.loads((STATE_DIR / "baselines-v2.json").read_text())
    if (
        data.get("provenance") != PROVENANCE
        or data.get("evaluation_version") != EVALUATION_VERSION
        or data.get("cases_hash") != CASES_HASH
    ):
        raise ValueError(
            "Baseline corpus or evaluation version changed; organizer must run prepare again"
        )
    return data["challenges"][str(challenge)]


def evaluate(challenge, include_reveal=False, config=None):
    if challenge not in (1, 2, 3):
        raise ValueError("Unknown investigation")
    cfg = config if config is not None else active_config()
    before = load_baseline(challenge)
    selected = [
        c
        for c in CASES
        if c["challenge"] == challenge and (include_reveal or not c["reveal"])
    ]
    cases = []
    for c in selected:
        current = run_case(c, cfg)
        if before[c["id"]]["passed"] and not current["passed"]:
            current["issues"].append(
                "Regression: this question passed the saved baseline"
            )
        cases.append(
            dict(
                id=c["id"],
                question=c["question"],
                matter=c["matter_id"],
                matter_id=c["matter_id"],
                as_of=c["as_of"],
                explanation=c["explanation"],
                required=c["required"],
                baseline=before[c["id"]],
                current=current,
                reveal=c["reveal"],
            )
        )
    return dict(
        version=VERSION,
        evaluation_version=EVALUATION_VERSION,
        cases_hash=CASES_HASH,
        challenge=challenge,
        config=cfg,
        context_limit=MAX_CONTEXT,
        candidates_per_signal=CANDIDATE_LIMIT,
        baseline=dict(
            passed=sum(c["baseline"]["passed"] for c in cases), total=len(cases)
        ),
        current=dict(
            passed=sum(c["current"]["passed"] for c in cases), total=len(cases)
        ),
        cases=cases,
    )


def verify():
    reports = {}
    for n in (1, 2, 3):
        for name, cfg in [
            ("baseline", BASELINES[n]),
            ("repair", REPAIRS[n]),
            ("solution", SOLUTION),
        ]:
            reports[f"{n}-{name}"] = run_cases(n, cfg)
        assert not all(
            r["passed"] for r in reports[f"{n}-baseline"].values()
        ), f"Investigation {n} must expose an actual baseline failure"
        for name in ("repair", "solution"):
            failures = {
                id: r["issues"]
                for id, r in reports[f"{n}-{name}"].items()
                if not r["passed"]
            }
            assert not failures, f"Reference fails: {n}-{name}: {failures}"
    return {
        key: {"passed": sum(r["passed"] for r in rows.values()), "total": len(rows)}
        for key, rows in reports.items()
    }
