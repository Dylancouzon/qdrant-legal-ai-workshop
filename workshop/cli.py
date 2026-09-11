"""Organizer preparation and reversible exercise checkpoints."""

import argparse
import os
import json
import shutil
from datetime import datetime, timezone
from .engine import (
    ROOT,
    STATE_DIR,
    BASELINE,
    AUTHORITY,
    FRESHNESS,
    CHECKPOINTS,
    SOLUTION,
    seed,
    client,
    COLLECTION,
    ready,
    search,
    encoder,
)
from .evaluation import save_baselines, evaluate, verify, load_baseline
from .data import CHALLENGES


def read_state():
    path = STATE_DIR / "state.json"
    return json.loads(path.read_text()) if path.exists() else {"revealed": False}


def checkpoint(name):
    cfg = CHECKPOINTS[name]
    target = ROOT / "workshop/retrieval.py"
    backups = STATE_DIR / "backups"
    backups.mkdir(parents=True, exist_ok=True)
    backup = backups / (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + "-retrieval.py"
    )
    shutil.copy2(target, backup)
    target.write_text(
        '"""Investigation settings. Saved changes apply to the next run.\nMatter scoping is always enforced. Inspect engine.py and agent.py.\n"""\n'
        + "".join(f"{key} = {value!r}\n" for key, value in cfg.items())
    )
    return {"checkpoint": name, "backup": str(backup)}


def connect():
    """Attach to a prepared collection without any remote write operations.

    Only the local embedding cache and saved baselines are written. A missing or
    incompatible collection is an error; provisioning belongs to ``prepare``.
    """
    previous_offline = os.environ.get("FASTEMBED_OFFLINE")
    try:
        # Check the remote packet before downloading anything locally.
        ready()
        os.environ["FASTEMBED_OFFLINE"] = "0"
        encoder.cache_clear()
        verification = verify()
        save_baselines()
        q = client()
        try:
            count = q.count(COLLECTION, exact=True).count
        finally:
            q.close()
        return {
            "mode": "connect",
            "collection": COLLECTION,
            "points": count,
            "remote_access": "read-only",
            "verification": verification,
            "state": "Local embedding cache and baselines ready. Existing retrieval edits preserved.",
        }
    finally:
        if previous_offline is None:
            os.environ.pop("FASTEMBED_OFFLINE", None)
        else:
            os.environ["FASTEMBED_OFFLINE"] = previous_offline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser(
        "prepare", help="Load the corpus into your writable Qdrant collection"
    )
    sub.add_parser(
        "connect",
        help="Verify a preloaded collection read-only; cache embeddings and baselines locally",
    )
    sub.add_parser("verify")
    sub.add_parser("ready")
    cp = sub.add_parser("checkpoint")
    cp.add_argument("name", choices=list(CHECKPOINTS))
    ev = sub.add_parser("evaluate")
    ev.add_argument("--challenge", type=int, choices=[1, 2, 3], default=1)
    ev.add_argument("--reveal", action="store_true")
    rv = sub.add_parser("reveal")
    rv.add_argument("value", choices=["on", "off"])
    args = parser.parse_args()
    if args.command == "prepare":
        os.environ["FASTEMBED_OFFLINE"] = "0"
        encoder.cache_clear()
        count = seed()
        save_baselines()
        result = {
            "points": count,
            "verification": verify(),
            "state": "Existing retrieval edits preserved; a fresh checkout starts at baseline.",
        }
    elif args.command == "connect":
        result = connect()
    elif args.command == "verify":
        result = verify()
    elif args.command == "checkpoint":
        result = checkpoint(args.name)
    elif args.command == "evaluate":
        result = evaluate(args.challenge, args.reveal)
    elif args.command == "reveal":
        STATE_DIR.mkdir(exist_ok=True)
        state = read_state()
        state["revealed"] = args.value == "on"
        (STATE_DIR / "state.json").write_text(json.dumps(state))
        result = state
    else:
        ready()
        load_baseline(1)
        probe = CHALLENGES[1]
        rows = search(probe["question"], probe["matter_id"], BASELINE)
        if not rows:
            raise RuntimeError("Readiness search returned no evidence")
        q = client()
        try:
            result = {
                "qdrant": q.info().version,
                "points": q.count(COLLECTION, exact=True).count,
                "baseline_saved": (STATE_DIR / "baselines-v2.json").exists(),
            }
        finally:
            q.close()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
