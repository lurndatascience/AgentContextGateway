# Agent Context Gateway

A gateway through which an AI agent retrieves task-specific context from structured and unstructured sources. It returns the smallest useful package, with a citation and a reason for every item, and warnings for stale, missing, duplicated, or conflicting facts.

Live: [contextgateway.vaibhavkadam.online](https://contextgateway.vaibhavkadam.online). API docs at `/docs`.

## System design

![System design](docs/diagrams/system_design_flow.png)

| module | responsibility |
|---|---|
| `sources.py` | four adapters, one row shape |
| `ingest.py` | idempotent load, contextual notes, embeddings |
| `retrieve.py` | full-text and vector channels, rank fusion, LLM reranker |
| `resolve.py` | reconcile, pack, link, freshness, explain |
| `agents.py` | two PydanticAI agents on the same contract |
| `main.py` | API, key-to-scope auth, demo page |

## Sources

| source | kind | scope | confidence | timestamp |
|---|---|---|---|---|
| press release chunks | unstructured | public | 0.90 | date in text, else unknown |
| records | structured | public | 0.75 | same as the release |
| financial facts | structured | public | 0.85 | inferred from the quarter |
| internal notes | unstructured and structured | internal or private | 0.60 | message timestamp |

## Ingestion flow

![Ingestion flow](docs/diagrams/ingestion_flow.png)

## Query flow

![Query flow](docs/diagrams/Query_flow.png)

`POST /context` with `X-API-Key` and `{task, budget_tokens, as_of}` returns:

- `items[]`: `ref`, `kind`, `title`, `content`, `fields`, `evidence[]`, `freshness`, `score`, `why[]`
- `warnings[]`: `stale`, `missing`, `duplicate`, or `conflict`, with refs and a resolution
- `scopes_applied`, `candidates_considered`, `tokens_used`, `budget_tokens`

`POST /agents/answer` and `POST /agents/brief` consume the same package and cite its refs.

## Requirement to mechanism

| requirement | mechanism |
|---|---|
| ingest and normalize several source types | four adapters into one `items` table |
| preserve reference, timestamp, freshness, confidence, scope | `source_ref`, `observed_at` with precision, confidence per source, scope column |
| smallest useful package | reranker cutoff, token budget, per-document cap, max items |
| combine structured and unstructured evidence | records attached to cited chunks, shared `fact_key` across sources |
| detect stale, missing, duplicated, conflicting facts | fact groups merged or resolved, age check, uncovered periods |
| filter private material before retrieval | scopes from the key, applied inside the SQL |
| citations with every fact | `evidence[]` on every item |
| explain inclusion | `why[]` on every item |

## Run

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.local.yml up --build   # local Postgres
docker compose up --build                                                     # managed Postgres
python eval/run.py                                                            # writes eval/results/report.md
```

Deploy: `scripts/deploy.sh`.

## Evaluation

Six showcase tasks, a 100-question golden set, and both agents. Full packages in `eval/results/report.md`.

| metric | production | lexical-only |
|---|---|---|
| showcase checks | 6 of 6 | 5 of 6 |
| hit rate | 91% | 80% |
| document recall | 82% | 72% |
| MRR | 0.86 | 0.69 |
| refusals returned empty | 55% | 20% |
| attribution completeness | 100% | 100% |
| out-of-scope evidence | 0 | 0 |
| agent citation coverage | 100% | disabled |
| items per package | 3.4 | 4.0 |
| latency | 5.5 s | 69 ms |

Retrieval ablation:

| configuration | hit rate | recall | MRR | refusals | items |
|---|---|---|---|---|---|
| lexical only | 79% | 72% | 0.69 | 20% | 4.0 |
| lexical + dense | 90% | 79% | 0.76 | 0% | 5.8 |
| lexical + dense + reranker | 90% | 79% | 0.81 | 50% | 3.6 |
| contextual | 86% | 77% | 0.74 | 0% | 5.7 |
| contextual + reranker (default) | 91% | 81% | 0.86 | 55% | 3.4 |

## Limits

- Most releases carry no full date; timestamps are labelled by precision.
- Facts inside prose are not extracted.
- Late chunking was dropped: it needs a hosted long-context model, which the droplet cannot run.
