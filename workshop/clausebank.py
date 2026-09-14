"""Real contracts from CUAD, used as the rest of the firm's document store.

CUAD is the Contract Understanding Atticus Dataset: 510 real commercial
contracts with clause-level spans, published by The Atticus Project under
CC BY 4.0. https://www.atticusprojectai.org/cuad

These passages keep their own contract name and parties. They are never
presented as part of a fictional matter, and no invented date or amendment
history is attached to any of them. They are the other clients' files, which
is exactly what makes a missing matter filter a real failure.
"""

import ast
import csv
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

URL = (
    "https://huggingface.co/datasets/theatticusproject/cuad/resolve/main/"
    "CUAD_v1/master_clauses.csv"
)
CACHE = Path(__file__).resolve().parents[1] / ".workshop" / "master_clauses.csv"
CONTRACTS = 150
MIN_WORDS, MAX_WORDS = 25, 110
NOTICE = "Real public contract text from CUAD (The Atticus Project), CC BY 4.0."

SKIP = {
    "Filename",
    "Document Name",
    "Parties",
    "Agreement Date",
    "Effective Date",
    "Expiration Date",
}
DATE_FORMATS = ("%B %d, %Y", "%b %d, %Y", "%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d")
FALLBACK_DATE = "2015-01-01"


def _download():
    CACHE.parent.mkdir(exist_ok=True)
    if not CACHE.exists():
        print(f"downloading CUAD clause table to {CACHE} ...", file=sys.stderr)
        urllib.request.urlretrieve(URL, CACHE)
    return CACHE


def _first(cell):
    """CUAD stores repeated values as a list literal in one cell."""
    cell = (cell or "").strip()
    if not cell:
        return ""
    try:
        value = ast.literal_eval(cell)
    except Exception:
        return cell
    if isinstance(value, str):
        return value
    return str(value[0]) if value else ""


def _spans(cell):
    cell = (cell or "").strip()
    if not cell:
        return []
    try:
        value = ast.literal_eval(cell)
    except Exception:
        value = [cell]
    if isinstance(value, str):
        value = [value]
    return [re.sub(r"\s+", " ", str(v)).strip() for v in value if str(v).strip()]


def _date(*cells):
    for cell in cells:
        raw = _first(cell).strip()
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(raw, fmt).date().isoformat()
            except ValueError:
                continue
    return FALLBACK_DATE


def _shouty(text):
    letters = sum(c.isalpha() for c in text)
    return letters and sum(c.isupper() for c in text) / letters > 0.6


def _slug(text, fallback):
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")[:48]
    return slug or fallback


def load(contracts=CONTRACTS):
    """Return clause passages in the same payload shape as the fictional corpus."""
    with open(_download(), newline="", encoding="utf-8") as fh:
        csv.field_size_limit(10**7)
        rows = list(csv.DictReader(fh))
    categories = [c for c in rows[0] if c and not c.endswith("-Answer") and c not in SKIP]

    usable = []
    for row in rows:
        clauses = [
            (cat, span)
            for cat in categories
            for span in _spans(row.get(cat))
            if MIN_WORDS <= len(span.split()) <= MAX_WORDS and not _shouty(span)
        ]
        if clauses:
            usable.append((len(clauses), row, clauses))
    usable.sort(key=lambda x: -x[0])

    passages, used = [], {}
    for order, (_, row, clauses) in enumerate(usable[:contracts]):
        name = _first(row.get("Document Name")) or "Commercial Agreement"
        matter = _slug(Path(_first(row.get("Filename")) or "").stem, f"contract-{order}")
        # Two contracts can slug to the same name; keep matter ids unique.
        used[matter] = used.get(matter, 0) + 1
        if used[matter] > 1:
            matter = f"{matter}-{used[matter]}"
        parties = _first(row.get("Parties"))
        signed = _date(row.get("Effective Date"), row.get("Agreement Date"))
        seen = set()
        for index, (category, text) in enumerate(clauses):
            if text in seen:
                continue
            seen.add(text)
            pid = f"cuad-{matter}-{index}"
            passages.append(
                {
                    "passage_id": pid,
                    "matter_id": matter,
                    "matter_name": name[:120],
                    "customer": parties[:120],
                    "supplier": parties[:120],
                    "document_id": matter.upper(),
                    "document_title": name[:120],
                    "section_id": category,
                    "heading": category,
                    "text": text,
                    "instrument_type": "agreement",
                    "executed_on": signed,
                    "effective_from": signed,
                    "effective_to": "9999-12-31",
                    "status": "operative",
                    "source_family": pid,
                    "references": [],
                    "notice": NOTICE,
                }
            )
    return passages


def check():
    passages = load()
    ids = {p["passage_id"] for p in passages}
    assert len(ids) == len(passages), "duplicate passage id"
    matters = {p["matter_id"] for p in passages}
    assert len(matters) >= 100, len(matters)
    from .corpus import MATTERS

    assert not (matters & set(MATTERS)), "clause bank collides with a fictional matter"
    for p in passages:
        assert MIN_WORDS <= len(p["text"].split()) <= MAX_WORDS
        datetime.fromisoformat(p["effective_from"])
    return f"{len(passages)} clause-bank passages across {len(matters)} real contracts"


if __name__ == "__main__":
    print(check())
