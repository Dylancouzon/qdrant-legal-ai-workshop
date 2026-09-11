# Fix the Search

Chicago, September 2026. A 60-minute Qdrant and LangGraph workshop for legal tech workers.

A legal assistant gives a plausible answer. Participants investigate what its evidence supports, repair how it gathers sources, and test another question. Three progressive investigations address **Missing Authority**, **Outdated Sources**, and **False Consensus**. Coding is optional; the IDE assistant can handle edits.

Start with [the workshop concept](WORKSHOP.md), [participant guide](PARTICIPANT.md), or [facilitator run of show](FACILITATOR.md). [outline.md](outline.md) contains the eight-minute introduction outline only, and [SOLUTIONS.md](SOLUTIONS.md) contains reference repairs. All documents and legal rules in the application are fictional training material.

## Choose Your Path

**Follow along, no setup:** the facilitator runs the live agent on screen. Inspect the sources, suggest an evidence check, predict the effect of a repair, and compare the revealed questions. This covers the complete workshop; a laptop or account isn't required.

**Optional hands-on:** clone this repository, open it in your IDE, and run the local application. Connect to the organizer's preloaded Qdrant collection using an appropriately scoped read-only credential, or ingest the 66-passage fictional packet into your own Qdrant instance. An answer model isn't required: the attendee launcher uses explicitly labeled evidence-only mode by default. You can supply your own local or hosted model to try live generation.

The organizer supplies the repository clone URL and, if available, the Qdrant endpoint, collection name, and collection-scoped read-only credential. No shared Cloud deployment or credentials come with this repository. Keep Qdrant admin and model-provider credentials private.

## Hands-On Setup

Install `uv` if it isn't already available, then clone the organizer-supplied repository URL and open its directory. Copy `.env.cloud.example` to `.env` and enter the supplied connection values; don't commit them. Use the preloaded connection path for a shared collection. `connect` reads the collection and saves local baselines; it never seeds or creates payload indexes.

```sh
cp .env.cloud.example .env
# Edit .env with the organizer's endpoint, collection, and read-only key.
./scripts/start-lab.sh
```

On platforms that don't run shell scripts, use these equivalent commands after editing `.env`:

```sh
uv run --frozen --env-file .env python -m workshop.cli connect
uv run --frozen --env-file .env python -m workshop.serve
```

The launcher uses the pinned `uv.lock`, prepares query embeddings and local baselines through read-only `connect`, and starts the app. It reads `.env` explicitly. The provided Cloud example selects evidence-only mode.

If no shared collection is available, start your own local Qdrant with `docker compose up -d` or configure your own Qdrant Cloud collection. Use `prepare` only for an instance you own or have permission to populate. Ingesting the small packet requires write/index permissions and downloads the embedding model. Connecting to a preloaded collection still requires the local query-embedding model; it does not download an answer model.

For a local collection you own:

```sh
cp .env.example .env
# Set ANSWER_PROVIDER=evidence in .env unless using your own live model.
docker compose up -d
uv run --frozen --env-file .env python -m workshop.cli prepare
./scripts/start-lab.sh
```

For your own Cloud collection, use the same `prepare` command with your own writable connection configured in `.env`; omit Docker. Preparation ingests the corpus without requiring an answer model.

The attendee app opens at `http://localhost:8000`. The [participant guide](PARTICIPANT.md) explains the investigation loop. If setup takes longer than expected, join the projected investigation and continue the full workshop immediately.

## Organizer Preparation

Run the live projected experience from your own machine or private host. Use Python 3.12, Docker with Compose for local Qdrant, and Ollama for the default local answer model. A practical local starting point is eight CPU cores and 16 GB RAM, with space for dependencies, the Qdrant volume, and model caches. Rehearse actual model latency before the session.

```sh
cp .env.example .env
./scripts/prepare.sh
uv run --frozen --env-file .env python -m workshop.cli checkpoint baseline
uv run --frozen --env-file .env python -m workshop.cli reveal off
./scripts/start.sh
```

`prepare.sh` prepares the local dependencies and collection and invokes `scripts/prepare-model.sh` to pull/check the configured model. Install Ollama and start its service first when using the default live mode. Open the app, check `/api/health`, and run a live question: retrieval readiness alone doesn't prove the answer provider works.

The application defaults to port **8000**, Qdrant to **6333**, and Ollama to **11434**. Compose binds Qdrant to loopback. Keep internal services private; this training app doesn't provide production authentication. No public app deployment, Qdrant Cloud creation, or specific provider routing is assumed.

For a preloaded shared Cloud collection, seed and verify it using organizer-only write credentials, then distribute a collection-scoped read-only credential for attendee `connect` operations. Configure both the read-only permission and collection restriction using [Qdrant Cloud granular database access](https://qdrant.tech/documentation/cloud/authentication/). Each checkout stores its own configuration, baselines, and run records. Attendee changes should affect their local retrieval policy, not the shared corpus.

Preparation idempotently seeds 66 passages across three matters and preserves local retrieval settings. Keep `.workshop` for cached query embeddings and saved baselines, and retain the local Qdrant volume if used. Dependencies are pinned in `pyproject.toml` and `uv.lock`; Compose pins the local Qdrant image. Re-run preparation and verification after changing the corpus or retrieval implementation. Use `connect`, not `prepare`, for a shared read-only collection.

## What Runs

- FastAPI serves the browser interface and application endpoints.
- `workshop/agent.py` uses a [LangGraph state graph](https://docs.langchain.com/oss/python/langgraph/graph-api) to organize a bounded investigation: planning, retrieval, evidence follow-up, sufficiency assessment, and answering. The visible trace records tool activity and sources, not private model reasoning.
- Qdrant stores 384-dimensional dense embeddings from `BAAI/bge-small-en-v1.5`, normalized corpus TF-IDF sparse vectors, and source metadata. The sparse tokenizer preserves compound identifiers. Retrieval uses actual server queries, with fusion and payload filtering where configured. The application supplies source relationships and applicability policy.
- `workshop/retrieval.py` is the small participant edit surface. Saved changes apply to subsequent runs. Keep the model and answer prompt fixed when comparing repairs.
- The default local model plans searches and generates a cited brief. A clearly labeled evidence-only mode provides deterministic planning and source extracts for outages and regression checks. It is not live generation.
- Source-level tests check the evidence supplied to the answer step. They don't certify every generated sentence or establish legal authority.

## Investigation Budget and Records

Every search considers up to eight candidates per signal and returns up to four passages. Hybrid can consider up to 16 candidates across its two signals. The final answer context holds at most 10 passages. The graph permits at most six logical retrieval tool calls, including no more than three reference batches in total. A countersearch that finds no operational record can retry once with a broader query within that budget. Hybrid diagnostics issue three Qdrant search requests for one logical search, so the tool count is not the raw server-request count or an equal-compute benchmark.

The downloadable run JSON records the activity trace, configuration, evidence, and graph/corpus/prompt provenance. Use it to compare investigations and explain which sources entered the final context.

## Model and Server Configuration

The attendee launcher loads `.env` using `uv --env-file`. For direct commands, use `uv run --frozen --env-file .env` or export the variables in the shell. The organizer scripts also load `.env` when present. Bare Python does not load it automatically. `.env.cloud.example` provides the shared-collection path; `.env.example` provides local organizer defaults. Keep provider credentials server-side and out of browser code and participant guides.

| Variable | Purpose |
| --- | --- |
| `ANSWER_PROVIDER` | `ollama` for the default live local model; `openai` for an organizer-configured compatible endpoint; `evidence` for explicit fallback |
| `ANSWER_MODEL` | Default local model `qwen3:8b`; explicitly choose a model when using a remote provider |
| `OLLAMA_BASE_URL` | Default `http://127.0.0.1:11434` |
| `MODEL_THINK` | Default `1` enables Ollama brief-generation thinking; set `0` for models that do not support it. Planning remains nonthinking, and private reasoning never appears in the trace. |
| `MODEL_TIMEOUT` | Model request timeout in seconds; default `120` |
| `OPENAI_API_KEY` | Server-side credential for an optional compatible remote provider |
| `OPENAI_BASE_URL` | Optional compatible endpoint URL |
| `QDRANT_URL` | Default `http://127.0.0.1:6333` |
| `QDRANT_API_KEY` | Optional server-side Qdrant credential |
| `QDRANT_COLLECTION` | Workshop collection name; default `fix_the_search_v2` |
| `FASTEMBED_CACHE_PATH` | Embedding cache; default `.workshop/models` |
| `FASTEMBED_OFFLINE` | Runtime defaults to `1`, using cached embeddings; preparation enables downloads |
| `APP_HOST`, `APP_PORT` | Start-script bind address and port; defaults `127.0.0.1`, `8000` |

The app can open when the configured model is unavailable so the user can explicitly choose evidence-only mode. `/api/health` reports a model-unavailable status as HTTP 503 rather than claiming full readiness. A live provider failure must remain an error until the user explicitly chooses evidence-only fallback. Never present extracted text or a deterministic plan as a successful live model run. Retrieval and source-level evaluation remain useful without a model provider. The workshop doesn't require hosted credentials.

## Checkpoints and Reveal

```sh
# Deliberately flawed start.
uv run --frozen --env-file .env python -m workshop.cli checkpoint baseline
# Start investigation two with the authority repair.
uv run --frozen --env-file .env python -m workshop.cli checkpoint authority
# Start investigation three with authority and freshness repaired.
uv run --frozen --env-file .env python -m workshop.cli checkpoint freshness
# Complete reference repair.
uv run --frozen --env-file .env python -m workshop.cli checkpoint solution
# Additional questions for minutes 45–55.
uv run --frozen --env-file .env python -m workshop.cli reveal on
```

Checkpoints back up `workshop/retrieval.py` under `.workshop/backups/` before replacing it. They don't reset Git or delete unrelated files or Docker data. Copy a desired backup to that configuration path to recover an edit. Restarting the web process preserves saved settings. To prepare for another group, restore `baseline` and run `reveal off`.

## Verify and Recover

```sh
uv run --frozen --env-file .env python -m workshop.cli ready
uv run --frozen --env-file .env python -m workshop.cli verify
uv run --frozen --env-file .env python -m workshop.cli evaluate --challenge 1 --reveal
uv run --frozen --env-file .env python -m workshop.cli evaluate --challenge 2 --reveal
uv run --frozen --env-file .env python -m workshop.cli evaluate --challenge 3 --reveal
uv run --frozen --env-file .env pytest -q
curl --fail http://localhost:8000/api/health
```

The reference verification uses real Qdrant and deterministic evidence checks. The measured full-suite results, including reveal cases, are:

| Investigation | Starting Checkpoint | Starting Checks | Repaired Checkpoint | Repaired Checks |
| --- | --- | --- | --- | --- |
| Missing Authority | `baseline` | 0/3 | `authority` | 3/3 |
| Outdated Sources | `authority` | 1/3 | `freshness` | 3/3 |
| False Consensus | `freshness` | 0/3 | `solution` | 3/3 |

The complete solution passes all nine cases. These are context checks under deterministic planning, not generated-answer accuracy scores. Separately run a live question in the browser, inspect citations and agent activity, and compare the retrieved context with the generated brief. A deterministic regression pass doesn't test every live planner choice.

If readiness fails, check `docker compose ps`, `docker compose logs qdrant`, the cached embedding files, and `uv run --frozen --env-file .env python -m workshop.cli ready`. For live-model errors, confirm Ollama is running and `ollama list` includes the configured model. A missing or failed dependency is an error, not an empty successful evaluation.

Changed corpus provenance requires preparation again. An unexpected collection point count calls for a fresh workshop collection name rather than deleting unknown data. Use a checkpoint to recover invalid participant configuration.

## Boundaries

The application receives explicit matter and as-of date context. These teaching controls aren't production authorization. Real applications must derive permitted scope from authenticated policy and maintain authoritative source metadata. Eligible sources must have been published by the question date and satisfy `valid_from <= as_of < valid_to`. Applicability follows these supplied rules; neither “newest wins” nor the machine's current date replaces the question date.

The packet and evaluation suite are compact learning materials, not a legal benchmark. Hybrid retrieval isn't guaranteed to outperform every baseline. Countersearch can locate competing evidence, but doesn't prove a contradiction; deduplication can reduce repeated accounts, but doesn't establish credibility. Passing retrieval checks doesn't guarantee a correct generated conclusion.

Rehearse on the actual presentation host and optional attendee setup. No public deployment, Qdrant Cloud provisioning, or Hackersquad integration is included. Optional hosted-provider behavior requires organizer configuration and separate verification. Local verification has covered 42 automated tests and browser checks of live runs, mobile layout, the case file, and comparisons. Recheck these after changing the model or deployment host.

Generated briefs are drafts that require source review. The facilitator default is `qwen3:8b`; attendees need no answer model. Small local models can misread a condition even when the decisive source is present. Conversely, a model may compensate for mixed outdated/current evidence and answer correctly in the flawed freshness baseline. Neither outcome changes the retrieval test: inspect the context and the cited claim separately.
