/* Render only server-provided evidence and trace events. No simulated agent activity. */
const $ = (id) => document.getElementById(id);
const state = { session: null, challenge: null, busy: false, trace: [], result: null, activity: null };
const stages = [['plan', 'Plan'], ['retrieve', 'Retrieve'], ['references', 'References'], ['countersearch', 'Countersearch'], ['assess', 'Assess'], ['brief', 'Brief']];
const el = (tag, className = '', text) => { const node = document.createElement(tag); node.className = className; if (text !== undefined) node.textContent = text; return node; };
const text = (value) => typeof value === 'string' ? value : JSON.stringify(value, null, 2);
const normalize = (row) => ({ ...row, id: row.id || row.passage_id, matter: row.matter || row.matter_id });
const matterName = (id) => state.session?.matters.find((matter) => String(matter.id) === String(id))?.name || id || 'Unspecified matter';
const passageTarget = (id) => `passage-${encodeURIComponent(id)}`;
function errorMessage(data, status) { return data.detail ? text(data.detail) : data.message || `The service could not complete this request (${status}). Please try again.`; }
async function api(path, body) {
  let response;
  try { response = await fetch(path, body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}); }
  catch { throw new Error('The investigation service is unreachable. Check that the lab is running, then try again.'); }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(errorMessage(data, response.status));
  return data;
}
function showError(error) { $('service-error').textContent = error.message; $('service-error').hidden = false; }
function clearError() { $('service-error').hidden = true; $('service-error').replaceChildren(); }
function setBusy(busy) {
  state.busy = busy;
  ['ask-button', 'test-button', 'compare-button', 'sources-button', 'matter', 'as-of', 'question', 'evidence-only'].forEach((id) => { $(id).disabled = busy || !state.session; });
  document.querySelectorAll('.mission-tabs button').forEach((button) => { button.disabled = busy; });
}
function requestContext() { return { challenge: state.challenge.id, matter: $('matter').value, question: $('question').value.trim(), as_of: $('as-of').value, evidence_only: $('evidence-only').checked }; }
function resetOutputs() {
  state.result = null; state.trace = []; state.activity = null; $('run-download').hidden = true;
  $('answer-title').textContent = 'The brief'; $('answer-mode').hidden = true;
  $('answer').replaceChildren(el('p', 'empty-copy', 'Run the investigation to build a brief from the retrieved evidence.'));
  $('evidence').replaceChildren(el('p', 'empty-copy', 'The passages supplied to the brief will appear here in context order.'));
  $('evidence-count').textContent = 'In context order';
  $('comparison-results').replaceChildren(); $('compare-status').textContent = '';
  $('test-results').replaceChildren(); $('test-status').textContent = '';
  $('trace-metrics').textContent = 'Waiting for a question'; renderTrace();
}
function chooseChallenge(id) {
  state.challenge = state.session.challenges.find((challenge) => String(challenge.id) === String(id));
  const challenge = state.challenge;
  document.querySelectorAll('.mission-tabs button').forEach((button) => { if (String(button.dataset.id) === String(id)) button.setAttribute('aria-current', 'step'); else button.removeAttribute('aria-current'); });
  $('challenge-label').textContent = `Investigation ${state.session.challenges.indexOf(challenge) + 1} / ${state.session.challenges.length}`;
  $('challenge-title').textContent = challenge.title; $('challenge-brief').textContent = challenge.brief;
  $('question').value = challenge.question;
  $('matter').value = challenge.default_matter || challenge.matter_id || state.session.matters[0].id;
  $('as-of').value = challenge.default_as_of || challenge.as_of || state.session.default_as_of || '2026-09-01';
  resetOutputs(); clearError(); $('request-status').textContent = '';
}
function sourceCard(raw, rank, prefix = '') {
  const source = normalize(raw); const card = el('article', 'evidence-card');
  if (!prefix) { card.id = passageTarget(source.id); card.tabIndex = -1; }
  const header = el('header'); header.append(el('span', 'rank', String(rank).padStart(2, '0')), el('span', 'source-title', source.title || source.document_id || source.id));
  if (source.status) header.append(el('span', `source-status ${source.status}`, source.status));
  card.append(header);
  const metadata = el('div', 'metadata', `${matterName(source.matter)} · ${source.document_id || source.id} · ${source.section_id || 'Source passage'}`);
  if (!prefix && source.matter && source.matter !== $('matter').value) metadata.append(el('span', 'wrong-matter', ' · Different matter'));
  card.append(metadata);
  if (source.effective_from || source.effective_to || source.source_type) card.append(el('div', 'metadata', [source.source_type?.replaceAll('_', ' '), source.effective_from && !source.effective_from.startsWith('9999') ? `Effective ${source.effective_from}` : source.status === 'draft' ? 'Not executed' : null, source.effective_to && source.effective_to !== '9999-12-31' ? `until ${source.effective_to} (exclusive)` : null].filter(Boolean).join(' · ')));
  card.append(el('p', 'passage-text', source.text || 'No source text was returned.'));
  if (source.applicable === false) card.append(el('p', 'metadata wrong-matter', 'Not applicable at the selected as-of date.'));
  const details = el('details'); details.append(el('summary', '', 'Source & retrieval details'));
  details.append(el('p', 'technical-note', `Passage: ${source.id}\n${source.source_family ? `Source family: ${source.source_family}\n` : ''}${source.published_at ? `Published: ${source.published_at}\n` : ''}${source.score == null ? '' : `Ranking score: ${Number(source.score).toFixed(4)}\n`}A ranking score is not confidence or a probability that a claim is true.`));
  card.append(details); return card;
}
function citationLinks(ids, evidence) {
  const links = el('div', 'citation-links');
  (ids || []).forEach((id) => {
    const index = evidence.findIndex((source) => source.id === id); if (index < 0) return;
    const source = evidence[index]; const link = el('a', '', `[${index + 1}] ${source.title || source.section_id || id}`); link.href = `#${passageTarget(id)}`;
    link.addEventListener('click', () => requestAnimationFrame(() => $(passageTarget(id))?.focus({ preventScroll: true })));
    links.append(link);
  }); return links;
}
function renderResult(data) {
  state.result = data; const evidence = (data.evidence || []).map(normalize); const answer = data.answer || {};
  if (data.trace) { state.trace = data.trace; renderTrace(true); }
  $('trace-metrics').textContent = [data.metrics?.search_calls != null ? `${data.metrics.search_calls} search${data.metrics.search_calls === 1 ? '' : 'es'}` : null, data.metrics?.elapsed_ms != null ? `${(data.metrics.elapsed_ms / 1000).toFixed(1)}s` : null].filter(Boolean).join(' · ') || 'Investigation complete';
  const evidenceOnly = ['extractive', 'evidence'].includes(answer.mode);
  $('answer-title').textContent = evidenceOnly ? 'Evidence-only brief' : 'The brief';
  $('answer-mode').textContent = evidenceOnly ? 'Source excerpts' : answer.mode === 'generated' || answer.mode === 'live' ? 'Model generated' : 'Evidence response';
  $('answer-mode').hidden = false;
  $('run-download').hidden = !data.run_id;
  if (data.run_id) $('run-download').href = `/api/runs/${encodeURIComponent(data.run_id)}`;
  $('answer').replaceChildren();
  if (answer.headline) $('answer').append(el('h3', 'brief-headline', answer.headline));
  if (answer.summary) $('answer').append(el('p', 'brief-summary', answer.summary));
  const claims = answer.claims || answer.excerpts?.map((excerpt) => ({ text: excerpt.text, citations: [excerpt.id] })) || [];
  claims.forEach((claim) => { const block = el('div', 'claim'); block.append(el('p', '', claim.text), citationLinks(claim.citations, evidence)); $('answer').append(block); });
  if (!claims.length && answer.text) $('answer').append(el('p', 'brief-summary', answer.text), citationLinks(answer.citations, evidence));
  if (!evidence.length) $('answer').append(el('p', 'empty-copy', 'No supporting passages were returned. This investigation does not establish an answer.'));
  if (answer.uncertainties?.length) { const box = el('aside', 'uncertainties'); const list = el('ul'); answer.uncertainties.forEach((item) => list.append(el('li', '', text(item)))); box.append(el('h3', '', 'Still unresolved'), list); $('answer').append(box); }
  $('answer').append(el('p', 'answer-note', evidenceOnly ? 'Evidence-only mode: source excerpts, not live model generation. Judge what the passages support in this matter and at this date.' : 'Inspect the cited sources. A fluent brief and a successful retrieval check do not guarantee that every claim is correct.'));
  $('evidence-count').textContent = `${evidence.length} sources · context order`;
  $('evidence').replaceChildren(...evidence.map((source, index) => sourceCard(source, index + 1)));
  if (!evidence.length) $('evidence').append(el('p', 'empty-copy', 'No evidence was retrieved. Inspect the search settings and the case file.'));
}
function renderTrace(complete = false) {
  const seen = state.trace.map((step) => step.node);
  $('trace-rail').replaceChildren(...stages.map(([id, label], index) => {
    const last = seen.lastIndexOf(id); const active = state.activity?.node === id && !complete;
    const skipped = last >= 0 && state.trace[last].status === 'skipped';
    const item = el('li', active ? 'active' : skipped ? 'skipped' : last >= 0 ? 'done' : '');
    item.append(el('span', 'node-dot', last >= 0 && !active ? skipped ? '–' : '✓' : String(index + 1)), document.createTextNode(label));
    if (active) item.setAttribute('aria-current', 'step'); return item;
  }));
  $('trace-events').replaceChildren(...state.trace.map((step, index) => {
    const details = el('details', 'trace-event'); const summary = el('summary');
    summary.append(el('span', 'event-index', String(index + 1).padStart(2, '0')), el('span', 'event-title', step.title || step.node), el('span', 'event-summary', step.summary || ''), el('span', 'event-duration', [step.status && step.status !== 'complete' ? step.status : null, step.duration_ms != null ? `${step.duration_ms}ms` : null].filter(Boolean).join(' · ')));
    const content = el('div', 'trace-detail');
    if (step.summary) content.append(el('p', '', step.summary));
    if (step.query) content.append(el('p', '', `Search query: ${text(step.query)}`));
    if (step.evidence_ids?.length) content.append(el('p', '', `Evidence: ${step.evidence_ids.join(' → ')}`));
    if (step.candidates) {
      content.append(el('p', 'signal-label', 'Actual search candidates'));
      if (Array.isArray(step.candidates)) content.append(el('pre', '', text(step.candidates)));
      else Object.entries(step.candidates).forEach(([signal, candidates]) => { content.append(el('p', 'signal-label', signal), el('pre', '', text(candidates))); });
    }
    const technical = Object.fromEntries(Object.entries(step).filter(([key]) => !['id', 'node', 'title', 'summary', 'query', 'evidence_ids', 'candidates', 'duration_ms', 'status'].includes(key)));
    if (Object.keys(technical).length) content.append(el('pre', '', text(technical)));
    if (!step.query && !step.candidates && !Object.keys(technical).length) content.append(el('p', 'muted', 'This step did not report additional search details.'));
    details.append(summary, content); return details;
  }));
  if (!state.trace.length) $('trace-events').append(el('p', 'empty-copy', state.busy ? 'Waiting for the first agent event…' : 'Each step appears as it happens. Open a step to inspect its actual searches and evidence.'));
}
async function investigate(context) {
  let response;
  try { response = await fetch('/api/investigate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(context) }); }
  catch { throw new Error('The investigation service is unreachable. Check that the lab is running, then try again.'); }
  if (!response.ok) { const data = await response.json().catch(() => ({})); throw new Error(errorMessage(data, response.status)); }
  if (!response.body) throw new Error('The service returned no investigation stream.');
  const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = ''; let result = null;
  function consume(line) {
    if (!line.trim()) return; const event = JSON.parse(line);
    if (event.type === 'error') throw new Error(event.detail ? text(event.detail) : event.message || event.error || 'The investigation stopped before completion.');
    if (event.type === 'activity') { state.activity = event; renderTrace(); $('request-status').textContent = event.title || 'Investigating…'; }
    if (event.type === 'step') {
      state.activity = null;
      const step = event.step; const index = step.id ? state.trace.findIndex((item) => item.id === step.id) : -1;
      if (index >= 0) state.trace[index] = step; else state.trace.push(step);
      renderTrace(); $('request-status').textContent = step.summary || step.title || 'Investigating…';
    }
    if (event.type === 'result') { state.activity = null; result = event.result; }
  }
  try {
    while (true) { const { value, done } = await reader.read(); if (done) break; buffer += decoder.decode(value, { stream: true }); let split; while ((split = buffer.indexOf('\n')) >= 0) { consume(buffer.slice(0, split)); buffer = buffer.slice(split + 1); } }
    buffer += decoder.decode(); if (buffer.trim()) consume(buffer);
  } catch (error) { await reader.cancel().catch(() => {}); throw error; }
  finally { reader.releaseLock(); }
  if (!result) throw new Error('The investigation ended without a completed brief. No successful result was recorded.');
  return result;
}
function comparisonColumn(side, title) {
  const column = el('div', 'comparison-column'); column.append(el('h3', '', title));
  const evidence = Array.isArray(side) ? side : side?.evidence || [];
  if (side?.summary) column.append(el('p', 'brief-summary', side.summary));
  if (!evidence.length) column.append(el('p', 'empty-copy', 'No evidence returned.'));
  evidence.forEach((source, index) => column.append(sourceCard(source, index + 1, title))); return column;
}
function sideResult(result, label) {
  const node = el('div', `result-side ${result.passed ? 'pass' : 'fail'}`); node.append(el('strong', '', `${label} · ${result.passed ? 'Evidence check passed' : 'Evidence check failed'}`));
  node.append(el('div', '', result.issues?.length ? result.issues.map(text).join(' ') : result.passed ? 'Required evidence and source constraints pass.' : 'Required evidence or source constraints did not pass.'));
  node.append(el('div', 'muted', `Retrieved: ${(result.evidence_ids || []).join(' → ') || 'No passages'}`));
  if (result.evidence?.length) { const details = el('details'); details.append(el('summary', '', 'Inspect retrieved passages')); result.evidence.forEach((source, index) => details.append(sourceCard(source, index + 1, label))); node.append(details); }
  return node;
}
function renderTests(data) {
  const root = $('test-results'); root.replaceChildren(); const summary = el('div', 'results-summary');
  for (const [key, label] of [['baseline', 'Saved baseline'], ['current', 'Current investigation']]) { const total = data[key]; const box = el('div', 'result-total', label); box.append(el('strong', '', `${total.passed} / ${total.total}`), el('span', '', 'evidence checks passed')); summary.append(box); }
  root.append(summary, el('p', 'answer-note', 'These source-level checks use a fixed-plan deterministic replay, not live model-selected queries. They test the retrieved answer context, not the correctness of generated prose.'));
  (data.cases || []).forEach((test) => {
    const item = el('article', 'evaluation-case'); const header = el('div', 'case-result-header'); const regressed = test.baseline.passed && !test.current.passed;
    header.append(el('h3', '', test.question), el('span', `result-badge ${test.current.passed ? 'pass' : ''}`, regressed ? 'Regression · previously passed' : test.current.passed ? 'Evidence checks pass' : 'Evidence needs attention'));
    item.append(header, el('p', 'metadata', `${matterName(test.matter || test.matter_id)} · ${test.id}${test.as_of ? ` · ${test.as_of}` : ''}`), el('p', '', test.explanation));
    const columns = el('div', 'result-comparison'); columns.append(sideResult(test.baseline, 'Before'), sideResult(test.current, 'Now')); item.append(columns); root.append(item);
  });
  if (data.config) { const details = el('details'); details.append(el('summary', '', 'Under the hood: configuration & evaluation budget'), el('pre', 'technical-note', text({ config: data.config, context_limit: data.context_limit, candidates_per_signal: data.candidates_per_signal, version: data.version }))); root.append(details); }
}
$('question-form').addEventListener('submit', async (event) => {
  event.preventDefault(); if (state.busy) return; const context = requestContext(); if (!context.question) { $('question').focus(); return; }
  clearError(); resetOutputs(); setBusy(true); renderTrace(); $('request-status').textContent = 'Opening the investigation…'; $('trace-metrics').textContent = 'Investigation running'; $('ask-button').textContent = 'Investigating…';
  try { const result = await investigate(context); renderResult(result); $('request-status').textContent = 'Investigation complete. Trace the claims back to their evidence.'; }
  catch (error) { showError(error); $('request-status').textContent = 'Investigation stopped. No completed brief is available.'; $('trace-metrics').textContent = 'Incomplete · inspect error'; renderTrace(true); }
  finally { setBusy(false); $('ask-button').textContent = 'Run Investigation ↗'; }
});
$('test-button').addEventListener('click', async () => {
  if (state.busy) return; clearError(); setBusy(true); $('test-results').replaceChildren(); $('test-status').textContent = 'Running fixed-plan evidence checks against the saved baseline…'; $('test-button').textContent = 'Testing…';
  try { renderTests(await api('/api/evaluate', { challenge: state.challenge.id })); $('test-status').textContent = 'Checks complete. Inspect the evidence behind every change.'; }
  catch (error) { showError(error); $('test-status').textContent = 'Evaluation failed. No current pass/fail result is available.'; }
  finally { setBusy(false); $('test-button').textContent = 'Test My Fix →'; }
});
$('compare-button').addEventListener('click', async () => {
  if (state.busy) return; clearError(); setBusy(true); $('comparison-results').replaceChildren(); $('compare-status').textContent = 'Comparing retrieved evidence for the same question and context…';
  try { const data = await api('/api/compare', requestContext()); const columns = el('div', 'comparison-columns'); columns.append(comparisonColumn(data.before || data.baseline, 'Original investigation'), comparisonColumn(data.after || data.current, 'Current investigation')); $('comparison-results').append(columns); $('compare-status').textContent = 'Fixed-plan deterministic replay of the original and current retrieval settings. This comparison does not use live model-selected queries or generate another brief.'; }
  catch (error) { showError(error); $('compare-status').textContent = 'Comparison unavailable. No current comparison was recorded.'; }
  finally { setBusy(false); }
});
$('sources-button').addEventListener('click', async () => {
  $('sources-title').textContent = `${matterName($('matter').value)} · Case file`; $('sources-content').replaceChildren(); $('sources-status').textContent = 'Opening source packet…'; $('sources-dialog').showModal();
  try { const data = await api(`/api/sources?matter=${encodeURIComponent($('matter').value)}&as_of=${encodeURIComponent($('as-of').value)}`); const sources = data.sources || []; $('sources-status').textContent = `${sources.length} passages · applicability as of ${$('as-of').value}. This is the source collection, not the current answer context.`; $('sources-content').replaceChildren(...sources.map((source, index) => sourceCard(source, index + 1, 'packet'))); }
  catch (error) { $('sources-status').textContent = error.message; }
});
$('close-sources').addEventListener('click', () => $('sources-dialog').close());
['matter', 'as-of'].forEach((id) => $(id).addEventListener('change', () => { resetOutputs(); $('request-status').textContent = 'Context changed. Run a new investigation for this matter and date.'; }));
function updateProviderLabel() {
  const provider = state.session?.provider || {};
  $('provider-label').textContent = $('evidence-only').checked ? 'Evidence-only mode selected' : ['evidence', 'extractive'].includes(provider.mode) ? 'Evidence-only fallback · no live model' : provider.available === false ? 'Live model unavailable · choose run options' : provider.model ? `Live brief · ${provider.model}` : 'Qdrant retrieval agent';
}
$('evidence-only').addEventListener('change', updateProviderLabel);
async function initialize() {
  try {
    state.session = await api('/api/session');
    $('matter').replaceChildren(...state.session.matters.map((matter) => { const option = el('option', '', matter.name); option.value = matter.id; return option; }));
    $('challenge-tabs').replaceChildren(...state.session.challenges.map((challenge, index) => { const button = el('button'); button.type = 'button'; button.dataset.id = challenge.id; button.append(el('span', 'tab-number', `0${index + 1}`), document.createTextNode(challenge.title)); button.addEventListener('click', () => chooseChallenge(challenge.id)); return button; }));
    $('retrieval-file').textContent = state.session.retrieval_file || 'workshop/retrieval.py';
    $('playbook').textContent = state.session.playbook || ''; $('playbook-details').hidden = !state.session.playbook;
    updateProviderLabel();
    const budget = state.session.budgets;
    if (budget) $('run-budget').textContent = `At most ${budget.tool_calls} retrieval tool calls, ${budget.reference_hops} reference hops, and ${budget.context_passages} answer passages. Each search signal considers up to ${budget.candidates_per_signal} candidates; the initial search supplies ${budget.initial_passages} passages.`;
    chooseChallenge(state.session.challenges[0].id); setBusy(false);
  } catch (error) { showError(error); const retry = el('button', '', 'Retry'); retry.addEventListener('click', () => { clearError(); initialize(); }); $('service-error').append(retry); $('challenge-tabs').replaceChildren(el('p', 'muted', 'Case files unavailable.')); }
}
initialize();
