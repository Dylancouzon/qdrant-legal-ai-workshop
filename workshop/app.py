"""The lab in a browser. Reading ranked passages in a bar beats reading a terminal.

    uv run python -m workshop.app

Serves on http://localhost:8000. Standard library only, one process per
participant, no framework. The playbook panel is the reason this exists: the
applicability rules render here and appear nowhere in the repository.
"""

import http.server
import json
import re
import socketserver
import urllib.parse
from pathlib import Path
from . import lab
from .client import connect, collection
from .playbook import RULES
from .questions import CALIBRATION, MATTERS, PROBES
from .score import score_all, K

PORT = 8000
STATE = Path(__file__).resolve().parents[1] / ".workshop" / "baseline.json"

STYLE = """
:root {
  --amaranth: #DC244C; --neon: #6047FF; --ink: #0B0B19; --paper: #FFFFFF;
  --muted: #5A5A6E; --line: #E4E4EC; --wash: #F7F7FA;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--paper); color: var(--ink);
  font-family: "Mona Sans", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  font-weight: 400; line-height: 1.55;
}
header {
  background: var(--ink); color: var(--paper); padding: 18px 24px;
  display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap;
}
header h1 { font-size: 17px; font-weight: 500; margin: 0; letter-spacing: -0.01em; }
header .mark { width: 10px; height: 10px; border-radius: 50%; background: var(--amaranth); }
header span { color: #9B9BB0; font-size: 13px; }
main { display: grid; grid-template-columns: minmax(0, 1fr) 340px; gap: 28px; padding: 24px; max-width: 1240px; }
@media (max-width: 900px) { main { grid-template-columns: 1fr; } }
h2 { font-size: 13px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em;
     color: var(--muted); margin: 0 0 12px; }
form { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }
input[type=text] { flex: 1 1 320px; }
input, select, button {
  font: inherit; padding: 9px 12px; border: 1px solid var(--line); border-radius: 7px;
  background: var(--paper); color: var(--ink);
}
button { background: var(--ink); color: var(--paper); border-color: var(--ink); cursor: pointer; font-weight: 500; }
button.ghost { background: var(--paper); color: var(--ink); }
button:hover { background: var(--neon); border-color: var(--neon); color: var(--paper); }
.passage { border: 1px solid var(--line); border-left: 3px solid var(--line);
           border-radius: 8px; padding: 13px 15px; margin-bottom: 10px; }
.passage.flagged { border-left-color: var(--amaranth); }
.passage .head { display: flex; gap: 10px; align-items: baseline; flex-wrap: wrap; }
.passage .rank { color: var(--muted); font-variant-numeric: tabular-nums; font-size: 13px; }
.passage .title { font-weight: 500; }
.passage .meta { color: var(--muted); font-size: 12.5px; margin: 3px 0 7px; }
.passage p { margin: 0; font-size: 14px; }
.tag { font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase;
       padding: 2px 7px; border-radius: 100px; border: 1px solid var(--line); color: var(--muted); }
.tag.bad { background: var(--amaranth); border-color: var(--amaranth); color: var(--paper); }
.tag.old { background: var(--wash); }
table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
th { text-align: left; font-weight: 500; color: var(--muted); font-size: 12px;
     text-transform: uppercase; letter-spacing: 0.06em; padding: 6px 8px; }
td { padding: 6px 8px; border-top: 1px solid var(--line); font-variant-numeric: tabular-nums; }
td.q { font-variant-numeric: normal; }
.delta.up { color: #1B7F4B; } .delta.down { color: var(--amaranth); }
aside { border-left: 1px solid var(--line); padding-left: 22px; }
@media (max-width: 900px) { aside { border-left: 0; padding-left: 0; border-top: 1px solid var(--line); padding-top: 22px; } }
aside article { margin-bottom: 16px; }
aside h3 { font-size: 14px; font-weight: 500; margin: 0 0 4px; }
aside h3::before { content: ""; display: inline-block; width: 6px; height: 6px; border-radius: 50%;
                   background: var(--neon); margin-right: 8px; vertical-align: middle; }
aside p { margin: 0; font-size: 13px; color: var(--muted); }
.diag { font-size: 12.5px; color: var(--muted); border-top: 1px solid var(--line);
        margin-top: 18px; padding-top: 12px; }
.empty { color: var(--muted); font-size: 14px; }
"""

PAGE = """<title>Legal Retrieval Lab</title>
<style>%(style)s</style>
<header>
  <span class="mark"></span>
  <h1>Legal Retrieval Lab</h1>
  <span>edit workshop/lab.py, then run again</span>
</header>
<main>
  <section>
    <h2>Ask</h2>
    <form id="ask">
      <input type="text" id="q" value="%(example)s" />
      <select id="m">%(matters)s</select>
      <input type="text" id="d" value="2026-01-20" size="10" />
      <button>Retrieve</button>
      <button type="button" class="ghost" id="run">Score calibration</button>
    </form>
    <div id="out" class="empty">Retrieve a question, or score the calibration set.</div>
    <div class="diag" id="diag"></div>
  </section>
  <aside>
    <h2>Applicability playbook</h2>
    %(rules)s
  </aside>
</main>
<script>
const $ = s => document.querySelector(s);
const esc = t => String(t).replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));

function passages(rows, matter) {
  if (!rows.length) return '<div class="empty">Nothing came back.</div>';
  return rows.map((r, i) => {
    const tags = [];
    if (r.matter_id !== matter) tags.push(`<span class="tag bad">another client &middot; ${esc(r.matter_name)}</span>`);
    if (r.superseded) tags.push(`<span class="tag old">superseded ${esc(r.effective_to)}</span>`);
    tags.push(`<span class="tag">${esc(r.instrument_type)}</span>`);
    return `<div class="passage ${r.matter_id !== matter ? 'flagged' : ''}">
      <div class="head"><span class="rank">${i + 1}</span>
      <span class="title">${esc(r.document_title)} s.${esc(r.section_id)}</span>${tags.join(' ')}</div>
      <div class="meta">${esc(r.heading)} &middot; in force from ${esc(r.effective_from)}</div>
      <p>${esc(r.text)}</p></div>`;
  }).join('');
}

function table(d) {
  const delta = (now, was) => {
    if (was === null || was === undefined) return '';
    const diff = now - was;
    if (Math.abs(diff) < 0.005) return '';
    return `<span class="delta ${diff > 0 ? 'up' : 'down'}">${diff > 0 ? '+' : ''}${diff.toFixed(2)}</span>`;
  };
  const rows = d.rows.map(r => `<tr><td class="q">${esc(r.question_id)}</td>
    <td>${r.coverage.toFixed(2)} ${delta(r.coverage, (d.baseline_rows || {})[r.question_id])}</td>
    <td>${r.ranking.toFixed(2)}</td><td>${r.tenant_leaks}</td>
    <td>${r.temporal_violations}</td><td>${r.duplicate_families}</td></tr>`).join('');
  const probes = d.probes.map(r => `<tr><td class="q">${esc(r.question_id)}</td>
    <td>${r.coverage.toFixed(2)}</td><td colspan="4">not scored &middot; missing ${esc(r.missing.join(', '))}</td></tr>`).join('');
  return `<table><tr><th>question</th><th>cover</th><th>rank</th><th>leak</th><th>stale</th><th>dup</th></tr>
    ${rows}
    <tr><td><b>${d.solved}/${d.questions} solved</b></td><td><b>${d.coverage.toFixed(2)}</b>
    ${delta(d.coverage, d.baseline_coverage)}</td><td><b>${d.ranking.toFixed(2)}</b></td>
    <td><b>${d.tenant_leaks}</b></td><td><b>${d.temporal_violations}</b></td><td><b>${d.duplicate_families}</b></td></tr>
    <tr><th colspan="6" style="padding-top:14px">ceiling probes, shown and never scored</th></tr>
    ${probes}</table>`;
}

$('#ask').onsubmit = async e => {
  e.preventDefault();
  $('#out').innerHTML = '<div class="empty">Retrieving...</div>';
  const m = $('#m').value;
  const r = await fetch(`/api/ask?q=${encodeURIComponent($('#q').value)}&m=${m}&d=${$('#d').value}`);
  const d = await r.json();
  $('#out').innerHTML = d.error ? `<div class="empty">${esc(d.error)}</div>` : passages(d.passages, m);
  $('#diag').textContent = d.diagnostics || '';
};
$('#run').onclick = async () => {
  $('#out').innerHTML = '<div class="empty">Scoring twelve questions...</div>';
  const d = await (await fetch('/api/score')).json();
  $('#out').innerHTML = d.error ? `<div class="empty">${esc(d.error)}</div>` : table(d);
  $('#diag').textContent = d.diagnostics || '';
};
</script>
"""


def diagnostics(qc, name):
    """Explain what the code executed, never whether the answers are right."""
    info = qc.get_collection(name)
    present = set(info.config.params.vectors or {}) | set(info.config.params.sparse_vectors or {})
    used = set(re.findall(r'using="([a-z0-9_]+)"', Path(lab.__file__).read_text()))
    return (f"lab.py queries {len(used)} of the {len(present)} representations this collection "
            f"carries ({', '.join(sorted(used))}). Execution only; it says nothing about whether "
            f"the answers are right.")


class Handler(http.server.BaseHTTPRequestHandler):
    qc = None
    name = None

    def log_message(self, *args):
        pass

    def send(self, payload, kind="application/json"):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", f"{kind}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(route.query)
        if route.path == "/":
            rules = "".join(
                f"<article><h3>{title}</h3><p>{body}</p></article>" for title, body in RULES
            )
            matters = "".join(
                f'<option value="{k}">{v}</option>' for k, v in MATTERS.items()
            )
            return self.send(
                (PAGE % {
                    "style": STYLE, "rules": rules, "matters": matters,
                    "example": "how long do we have to put it right before they can walk away?",
                }).encode(),
                "text/html",
            )
        if route.path == "/api/ask":
            return self.send(self.ask(query))
        if route.path == "/api/score":
            return self.send(self.score())
        self.send_error(404)

    def ask(self, query):
        question = (query.get("q") or [""])[0].strip()
        matter = (query.get("m") or ["harbor"])[0]
        as_of = (query.get("d") or ["2026-01-20"])[0]
        if not question:
            return {"error": "Type a question."}
        try:
            points = lab.retrieve(self.qc, self.name, question, matter, as_of)
        except Exception as exc:
            return {"error": f"lab.py raised: {exc}"}
        return {
            "passages": [
                dict(
                    {k: p.payload[k] for k in (
                        "passage_id", "matter_id", "matter_name", "document_title",
                        "section_id", "heading", "text", "instrument_type",
                        "effective_from", "effective_to",
                    )},
                    superseded=p.payload["effective_to"] != "9999-12-31",
                )
                for p in points
            ],
            "diagnostics": diagnostics(self.qc, self.name),
        }

    def score(self):
        run = lambda q, m, d: [
            p.payload for p in lab.retrieve(self.qc, self.name, q, m, d, limit=K)
        ]
        try:
            result = score_all(CALIBRATION, run, k=K)
            probes = score_all(PROBES, run, k=K)
        except Exception as exc:
            return {"error": f"lab.py raised: {exc}"}

        baseline = json.loads(STATE.read_text()) if STATE.exists() else None
        payload = {
            "rows": [
                {k: r[k] for k in ("question_id", "coverage", "ranking", "tenant_leaks",
                                   "temporal_violations", "duplicate_families")}
                for r in result["rows"]
            ],
            "probes": [
                {k: r[k] for k in ("question_id", "coverage", "missing")} for r in probes["rows"]
            ],
            "solved": result["solved"], "questions": result["questions"],
            "coverage": result["coverage"], "ranking": result["ranking"],
            "tenant_leaks": result["tenant_leaks"],
            "temporal_violations": result["temporal_violations"],
            "duplicate_families": result["duplicate_families"],
            "diagnostics": diagnostics(self.qc, self.name),
        }
        if baseline:
            payload["baseline_coverage"] = baseline["coverage"]
            payload["baseline_rows"] = baseline["rows"]
        else:
            # First run of the evening becomes the line everything is measured from.
            STATE.parent.mkdir(exist_ok=True)
            STATE.write_text(json.dumps({
                "coverage": result["coverage"],
                "rows": {r["question_id"]: r["coverage"] for r in result["rows"]},
            }))
        return payload


def main():
    Handler.qc, Handler.name = connect(), collection()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as server:
        print(f"Legal Retrieval Lab on http://localhost:{PORT}")
        print("The applicability playbook is in the right-hand panel. Read it.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


if __name__ == "__main__":
    main()
