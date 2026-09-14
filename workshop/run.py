"""Your feedback loop. Two commands, both read-only.

    uv run python -m workshop.run ask "how long do we have to fix it?" -m harbor -d 2026-01-20
    uv run python -m workshop.run score

ask    Runs retrieve() from lab.py and prints the ranked passages, so you can
       read the evidence the way a person would.
score  Runs retrieve() over the calibration questions and reports the three
       published dimensions. Edit lab.py, run it again, watch the numbers move.

The held-out questions are not in this repository. The calibration set teaches
the rubric; it does not contain the questions you are scored on.
"""

import argparse
import json
import os
import re
import textwrap
import urllib.error
import urllib.request
from pathlib import Path
from dotenv import load_dotenv
from . import lab
from .client import connect, collection
from .questions import CALIBRATION as QUESTIONS, MATTERS, PROBES
from .score import score_all, K

LAB = Path(__file__).with_name("lab.py")


def diagnostics(qc, name):
    """Report execution, not correctness. What this file asks for, and what exists."""
    info = qc.get_collection(name)
    present = set(info.config.params.vectors or {}) | set(
        info.config.params.sparse_vectors or {}
    )
    used = set(re.findall(r'using="([a-z0-9_]+)"', LAB.read_text()))
    return (
        f"representations: lab.py queries {len(used)} of the {len(present)} this "
        f"collection carries ({', '.join(sorted(used))})"
    )


def ask(args):
    qc, name = connect(), collection()
    points = lab.retrieve(qc, name, args.question, args.matter, args.date)
    print(f"\n{args.question}\nmatter {args.matter}, as of {args.date}\n")
    for i, p in enumerate(points, 1):
        d = p.payload
        flag = "" if d["effective_to"] == "9999-12-31" else f"  [superseded {d['effective_to']}]"
        if d["matter_id"] != args.matter:
            flag += f"  [ANOTHER CLIENT: {d['matter_name'][:44]}]"
        print(f"{i:2}. {p.score:7.3f}  {d['document_title'][:56]} s.{d['section_id']}{flag}")
        print(f"     {d['heading']}  ({d['instrument_type']}, from {d['effective_from']})")
        print(textwrap.fill(d["text"], 92, initial_indent="     ", subsequent_indent="     "))
        print()
    print(diagnostics(qc, name))


def score(args):
    qc, name = connect(), collection()
    run = lambda q, m, d: [p.payload for p in lab.retrieve(qc, name, q, m, d, limit=K)]
    result = score_all(QUESTIONS, run)
    print(f"\ncalibration set, {len(QUESTIONS)} questions, top {K}\n")
    print(f"{'question':30} {'cover':>6} {'rank':>6} {'leak':>5} {'stale':>6} {'dup':>4}  missing")
    print("-" * 92)
    for row in result["rows"]:
        print(
            f"{row['question_id']:30} {row['coverage']:6.2f} {row['ranking']:6.2f} "
            f"{row['tenant_leaks']:5} {row['temporal_violations']:6} "
            f"{row['duplicate_families']:4}  {', '.join(row['missing']) or '-'}"
        )
    print("-" * 92)
    print(
        f"{'TOTAL':30} {result['coverage']:6.2f} {result['ranking']:6.2f} "
        f"{result['tenant_leaks']:5} {result['temporal_violations']:6} "
        f"{result['duplicate_families']:4}   {result['solved']}/{result['questions']} solved"
    )
    probes = score_all(PROBES, run, k=K)
    print("\nceiling probes, shown and never scored. Nothing we have tried reaches these.")
    for row in probes["rows"]:
        print(f"  {row['question_id']:28} {row['coverage']:6.2f}  missing "
              f"{', '.join(row['missing'])}")

    print(
        "\ncover  share of the controlling passages you retrieved, the score that ranks you\n"
        "rank   how well the rest were ordered\n"
        "leak   passages from another client's files\n"
        "stale  this client's passages, outside their effective window on the question date\n"
        "dup    rank slots taken by a repeat copy of a document you already returned"
    )
    print(f"\n{diagnostics(qc, name)}")


def preflight(args):
    """Run this before the room does. It fails loudly instead of at minute 12."""
    ok = True
    try:
        qc, name = connect(), collection()
    except SystemExit as exc:
        print(f"FAIL  .env: {exc}")
        return
    try:
        info = qc.get_collection(name)
    except Exception as exc:
        print(f"FAIL  cannot read collection {name}: {str(exc)[:120]}")
        print("      Check QDRANT_URL and that the key is scoped to this collection.")
        return
    dense = set(info.config.params.vectors or {})
    sparse = set(info.config.params.sparse_vectors or {})
    count = qc.count(name, exact=True).count
    print(f"OK    collection {name}: {count} passages")
    print(f"OK    representations present: {', '.join(sorted(dense | sparse))}")

    for matter in sorted(MATTERS):
        n = qc.count(name, count_filter=_matter_filter(matter), exact=True).count
        if n < 20:
            ok = False
            print(f"FAIL  matter {matter} has only {n} passages")
        else:
            print(f"OK    matter {matter}: {n} passages")

    # Check the models lab.py actually names. The collection declares more
    # representations than the starter uses, and finding out what they are is
    # part of the exercise, so preflight reports their names and stops there.
    for signal, model in ((lab.DENSE_MODEL and "dense_weak", lab.DENSE_MODEL),
                          ("bm25", lab.SPARSE_MODEL)):
        try:
            qc.query_points(
                name,
                query=models_document(model, "termination for cause"),
                using=signal,
                limit=1,
            )
            print(f"OK    inference {signal:13} {model}")
        except Exception as exc:
            ok = False
            reason = ("needs billing on the cluster" if "Authentication failed" in str(exc)
                      else str(exc)[:70])
            print(f"FAIL  inference {signal:13} {model} :: {reason}")

    load_dotenv(".env")
    points = lab.retrieve(qc, name, "how long do we have to fix the problem", "harbor", "2026-01-20")
    print(f"{'OK   ' if points else 'FAIL '} lab.retrieve returned {len(points)} passages")
    if not points:
        ok = False

    print(f"{'OK   ' if os.getenv('OPENAI_API_KEY') else 'note '} OPENAI_API_KEY "
          f"{'set' if os.getenv('OPENAI_API_KEY') else 'missing (the answer command needs it; nothing else does)'}")
    print("\nready" if ok and points else "\nnot ready, fix the FAIL lines above")


def models_document(model, text):
    from qdrant_client import models as qm

    return qm.Document(text=text, model=model)


def _matter_filter(matter):
    from qdrant_client import models as qm

    return qm.Filter(
        must=[qm.FieldCondition(key="matter_id", match=qm.MatchValue(value=matter))]
    )


PROMPT = """You are a legal research assistant. Answer the question using ONLY the \
numbered passages below. Cite the passages you rely on as [1], [2]. If the passages do \
not settle the question, say so and say what is missing. Be brief.

Question, asked on {as_of} about matter {matter}:
{question}

Passages:
{passages}"""


def answer(args):
    """One retrieval call, one completion, no retries. Deliberately.

    The agent never rephrases and never searches again, so the answer is only
    ever as good as the evidence retrieve() returned. That is the lesson.
    """
    load_dotenv(".env")
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return print("Set OPENAI_API_KEY in .env. Retrieval and scoring work without it.")
    qc, name = connect(), collection()
    points = lab.retrieve(qc, name, args.question, args.matter, args.date)
    if not points:
        return print("retrieve() returned nothing, so the agent has nothing to answer from.")

    passages = "\n\n".join(
        f"[{i}] {p.payload['document_title']} s.{p.payload['section_id']} "
        f"({p.payload['heading']}, in force from {p.payload['effective_from']})\n"
        f"{p.payload['text']}"
        for i, p in enumerate(points, 1)
    )
    body = json.dumps(
        {
            "model": os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
            "messages": [
                {
                    "role": "user",
                    "content": PROMPT.format(
                        as_of=args.date, matter=args.matter,
                        question=args.question, passages=passages,
                    ),
                }
            ],
        }
    ).encode()
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            reply = json.load(response)["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        return print(f"OpenAI returned {exc.code}: {exc.read().decode()[:200]}")

    print(f"\n{reply}\n")
    print("-" * 72)
    print("The agent saw only these passages, in this order, and did not search again:")
    for i, p in enumerate(points, 1):
        d = p.payload
        stale = "" if d["effective_to"] == "9999-12-31" else f"  SUPERSEDED {d['effective_to']}"
        foreign = "" if d["matter_id"] == args.matter else f"  OTHER CLIENT: {d['matter_name'][:40]}"
        print(f"  [{i}] {d['document_title'][:52]} s.{d['section_id']}{stale}{foreign}")


def main():
    parser = argparse.ArgumentParser(prog="workshop.run", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    a = sub.add_parser("ask", help="run one question and read the passages")
    a.add_argument("question")
    a.add_argument("-m", "--matter", required=True, choices=sorted(MATTERS))
    a.add_argument("-d", "--date", required=True, help="question date, YYYY-MM-DD")
    a.set_defaults(func=ask)

    s = sub.add_parser("score", help="score the calibration set")
    s.set_defaults(func=score)

    n = sub.add_parser("answer", help="what the agent says, given your evidence")
    n.add_argument("question")
    n.add_argument("-m", "--matter", required=True, choices=sorted(MATTERS))
    n.add_argument("-d", "--date", required=True, help="question date, YYYY-MM-DD")
    n.set_defaults(func=answer)

    p = sub.add_parser("preflight", help="check the setup before the room does")
    p.set_defaults(func=preflight)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
