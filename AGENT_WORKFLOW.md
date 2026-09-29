# Agent workflow

How this project was built with AI tools, where they helped, where they failed, what a human changed, and how to audit it.

## Tools

| tool | role |
|---|---|
| Claude Code, model Claude Fable 5.1 | wrote the code, the eval, the docs, ran the stack, diagnosed failures, deployed |
| Playwright MCP inside Claude Code | operated the DigitalOcean console to add the droplet to the database's trusted sources |
| OpenAI inside the product | `text-embedding-3-small` for vectors, `gpt-4o-mini` for contextual notes and the reranker, `gpt-4o` for the agents |
| PydanticAI | agent framework for the two downstream agents |

No code generation happened outside this repository's session. The earlier press-release RAG that supplied the corpus, the financial-table parser, and the golden set was the human's prior work.

## Where the tools helped

- Planning: the first step was a requirement-by-requirement plan with defaults the human could accept or override in one reply.
- Reuse: the agent audited the earlier project and identified what to carry over (corpus, parser, contextual-note pattern, judge, golden set, deploy pattern) and what to drop (Neo4j, Next.js UI, cross-encoder).
- End-to-end debugging: every change was driven through the real API and the eval, which is how the defects below were found.
- The readability pass: a behaviour snapshot of seven packages before and after the refactor proved zero change.

## Where the tools failed or needed correction

| what went wrong | how it surfaced | fix |
|---|---|---|
| ingest skipped embedding rows whose content hash was unchanged, so a run "with the key" had zero vectors | the eval printed `0 of 1272 items embedded` | rows missing a vector are reprocessed |
| the lexical relevance gate could not serve hit rate and refusals at once | a threshold sweep showed a one-for-one trade | kept 0.3 as the key-free floor, moved refusals to the reranker |
| corpus-wide words ("Deutsche", "Telekom") satisfied the coverage gate | refusal questions returned unrelated items | IDF-weighted coverage |
| the eval crashed when a redeploy restarted the container under it | a JSON decode error on a proxy error page | retry on 5xx |
| late chunking was built on a third-party API, then the human declined that vendor | conversation | replaced by an OpenAI-only reranker; ablation confirmed the reranker was the part that mattered |
| the demo page shipped with dev keys that production no longer accepted | the human hit a 401 | demo mode with an access-level header |
| the permission classifier refused to add the laptop's IP to the database firewall | tool denial | only the droplet was added; local runs use a Postgres container |
| contextual notes alone slightly lowered hit rate on this corpus | the ablation | kept them only in combination with the reranker |

## What the human changed or decided

- Production stack on the droplet instead of an offline toy; OpenAI as the only vendor; no droplet resize; late chunking dropped.
- Real database credentials, DNS, and the OpenAI key. The tools never printed them.
- The demo page's shape: one button, all three access levels underneath, no key entry.
- The readability pass and the switch of the agents to PydanticAI.
- Diagram screenshots rendered from the Mermaid sources.

## How to audit

1. `python -m pytest tests` runs offline checks on the adapters, the parser, the FY 2022 conflict, and the fallback.
2. `python eval/run.py` against a running stack regenerates `eval/results/report.md`; compare with the committed one.
3. Scope enforcement: `grep -n "Item.scope.in_" gateway/app/retrieve.py gateway/app/resolve.py`. Every query that reads items carries it.
4. Ask the same private question on the demo page; only the finance level should return the embargoed note.
5. `git log --oneline` shows five commits by concern; `git ls-files | grep -E "^\.env$|^data/press"` must return nothing.
