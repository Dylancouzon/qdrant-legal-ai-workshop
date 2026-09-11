"""Workshop HTTP boundary: streamed agent runs, real evidence, and saved comparisons."""

import json
import logging
import threading
from datetime import date
from pathlib import Path
from queue import Empty, Queue
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from . import data, engine, provider
from .agent import run_agent
from .cli import read_state

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(
    title="Fix the Search · Qdrant + LangGraph", docs_url=None, redoc_url=None
)
log = logging.getLogger(__name__)
LIVE_RUN = threading.BoundedSemaphore(1)


class AskRequest(BaseModel):
    challenge: int = Field(ge=1, le=3)
    matter: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=1, max_length=2000)
    as_of: str = "2026-09-01"
    evidence_only: bool = False

    @field_validator("as_of")
    @classmethod
    def valid_date(cls, value):
        return date.fromisoformat(value).isoformat()

    @field_validator("question")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Enter a question to investigate.")
        return value.strip()


class EvalRequest(BaseModel):
    challenge: int = Field(ge=1, le=3)


ERROR_DETAIL = "The investigation could not finish. Check Qdrant, retrieval.py, and the configured model. No successful result was recorded. You can explicitly use evidence-only mode if the model is unavailable."


@app.middleware("http")
async def service_error(request, call_next):
    try:
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        log.error("Workshop request failed (%s)", type(exc).__name__)
        return JSONResponse(status_code=503, content={"detail": ERROR_DETAIL})


def evidence(rows, as_of="2026-09-01"):
    return [
        {
            **{k: v for k, v in row.items() if not k.startswith("_")},
            "id": row["passage_id"],
            "matter": row["matter_id"],
            "source_type": row.get("kind", "source"),
            "effective_from": row.get("valid_from"),
            "effective_to": row.get("valid_to"),
            "applicable": row.get("valid_from", "0001-01-01")
            <= as_of
            < row.get("valid_to", "9999-12-31")
            and row.get("published_at", "0001-01-01") <= as_of,
        }
        for row in rows
    ]


def normalize_run(result):
    return {**result, "evidence": evidence(result["evidence"], result["as_of"])}


def baseline_config(challenge):
    return {1: engine.BASELINE, 2: engine.AUTHORITY, 3: engine.FRESHNESS}[challenge]


def validate_context(body):
    if body.matter not in data.MATTERS:
        raise HTTPException(422, "Choose a workshop matter.")


def execute(body, callback=None):
    fallback = body.evidence_only or provider.settings()[0] == "evidence"
    result = normalize_run(
        run_agent(
            body.question,
            body.matter,
            body.as_of,
            planner_mode="deterministic" if fallback else "live",
            answer_mode="evidence" if fallback else "live",
            on_event=callback,
        )
    )
    directory = engine.STATE_DIR / "runs"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{result['run_id']}.json").write_text(json.dumps(result, indent=2))
    return result


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/session")
def session():
    return {
        "challenges": [
            {
                "id": key,
                **value,
                "default_matter": value["matter_id"],
                "default_as_of": value["as_of"],
            }
            for key, value in data.CHALLENGES.items()
        ],
        "matters": [{"id": key, "name": value} for key, value in data.MATTERS.items()],
        "retrieval_file": "workshop/retrieval.py",
        "agent_file": "workshop/agent.py",
        "baseline_ready": (engine.STATE_DIR / "baselines-v2.json").exists(),
        "revealed": read_state().get("revealed", False),
        "config": engine.config(),
        "playbook": data.PLAYBOOK,
        "provider": provider.status(),
        "collection": {
            "name": engine.COLLECTION,
            "passages": len(data.PASSAGES),
            "documents": len({p["document_id"] for p in data.PASSAGES}),
            "matters": len(data.MATTERS),
            "version": data.VERSION,
        },
        "budgets": {
            "candidates_per_signal": engine.CANDIDATE_LIMIT,
            "initial_passages": engine.TOP_K,
            "context_passages": engine.MAX_CONTEXT,
            "tool_calls": 6,
            "reference_hops": 3,
        },
    }


@app.get("/api/health")
def health():
    from .evaluation import load_baseline

    engine.ready()
    load_baseline(1)
    first = data.CHALLENGES[1]
    rows = engine.retrieve(
        first["question"], first["matter_id"], first["as_of"], engine.BASELINE
    )["evidence"]
    if not rows:
        raise HTTPException(503, "The prepared collection returned no evidence.")
    model = provider.status()
    if not model["available"]:
        raise HTTPException(
            503, "Retrieval is ready, but the configured answer model is unavailable."
        )
    return {
        "status": "ready",
        "framework": "LangGraph",
        "retrieval": "real Qdrant",
        "provider": model,
        "passages": len(data.PASSAGES),
    }


@app.post("/api/ask")
def ask(body: AskRequest):
    validate_context(body)
    if not LIVE_RUN.acquire(blocking=False):
        raise HTTPException(
            409,
            "An investigation is already running in this app. Wait for it to finish.",
        )
    try:
        return execute(body)
    finally:
        LIVE_RUN.release()


@app.post("/api/investigate")
def investigate(body: AskRequest):
    validate_context(body)
    if not LIVE_RUN.acquire(blocking=False):
        raise HTTPException(
            409,
            "An investigation is already running in this app. Wait for it to finish.",
        )
    events = Queue()
    stopped = threading.Event()

    def publish(event):
        if stopped.is_set():
            raise RuntimeError("Investigation client disconnected")
        events.put(event)

    def worker():
        try:
            result = execute(body, publish)
            events.put({"type": "result", "result": result})
        except Exception as exc:
            log.error("Investigation failed (%s)", type(exc).__name__)
            events.put({"type": "error", "detail": ERROR_DETAIL})
        finally:
            LIVE_RUN.release()
            events.put(None)

    threading.Thread(target=worker, daemon=True).start()

    def stream():
        try:
            while True:
                try:
                    event = events.get(timeout=1)
                except Empty:
                    event = {"type": "heartbeat"}
                if event is None:
                    return
                yield json.dumps(event) + "\n"
        finally:
            stopped.set()

    return StreamingResponse(
        stream(),
        media_type="application/x-ndjson",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-store"},
    )


@app.post("/api/compare")
def compare(body: AskRequest):
    validate_context(body)
    # Same graph, question, and bounded deterministic plan; no extra model spend.
    before = run_agent(
        body.question, body.matter, body.as_of, config=baseline_config(body.challenge)
    )
    after = run_agent(body.question, body.matter, body.as_of)
    old = {r["passage_id"] for r in before["evidence"]}
    new = {r["passage_id"] for r in after["evidence"]}
    return {
        "before": normalize_run(before),
        "after": normalize_run(after),
        "added": sorted(new - old),
        "removed": sorted(old - new),
        "mode": "deterministic",
        "explanation": "Same graph and question with a fixed evaluation plan. This comparison does not regenerate the live brief.",
    }


@app.post("/api/evaluate")
def evaluate(body: EvalRequest):
    from .evaluation import evaluate as run_evaluation

    report = run_evaluation(
        body.challenge, include_reveal=read_state().get("revealed", False)
    )
    for case in report["cases"]:
        for side in ("baseline", "current"):
            case[side]["evidence"] = evidence(
                case[side]["evidence"], case.get("as_of", "2026-09-01")
            )
    report["planner_mode"] = "deterministic"
    return report


@app.get("/api/sources")
def sources(matter: str, as_of: str = "2026-09-01"):
    if matter not in data.MATTERS:
        raise HTTPException(422, "Choose a workshop matter.")
    try:
        date.fromisoformat(as_of)
    except ValueError:
        raise HTTPException(422, "Use an ISO date: YYYY-MM-DD.") from None
    client = engine.client()
    try:
        engine.ready(client)
        rows, _ = client.scroll(
            engine.COLLECTION,
            scroll_filter=engine.scope_filter(matter, as_of, engine.BASELINE),
            limit=100,
            with_payload=True,
        )
        payloads = [dict(row.payload, score=None) for row in rows]
        return {"sources": evidence(payloads, as_of), "matter": matter, "as_of": as_of}
    finally:
        client.close()


@app.get("/api/runs/{run_id}")
def saved_run(run_id: UUID):
    path = engine.STATE_DIR / "runs" / f"{run_id}.json"
    if not path.exists():
        raise HTTPException(404, "Run not found.")
    return FileResponse(
        path, media_type="application/json", filename=f"investigation-{run_id}.json"
    )


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
