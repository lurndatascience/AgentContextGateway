# Retrieval: every enabled channel produces a ranked list, the lists are fused with Reciprocal
# Rank Fusion, and an optional LLM reranker reorders the result. The principal's scopes are
# applied inside every SQL query, so out-of-scope rows never become candidates.
import math
import re
from collections import Counter
from dataclasses import dataclass, field

from openai import OpenAI
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import Item
from app.rerank import rerank as llm_rerank

STOPWORDS = {"the", "and", "for", "what", "which", "who", "how", "did", "does", "was", "were", "are", "with",
             "from", "that", "this", "into", "about", "when", "where", "why", "has", "have", "had", "its", "any",
             "his", "her", "been", "will", "many", "much", "last", "year", "today", "yesterday", "currently",
             "out", "off", "some", "also", "over", "there", "their", "they", "them", "than", "then"}
KEEP_SHORT = {"fy", "q1", "q2", "q3", "q4", "ai", "5g"}
ALIASES = {"full-year": "fy", "fiscal": "fy"}

# channel name -> (kind, indexed column, label shown in explanations). Adding a channel is one line.
CHANNELS = {
    "lexical": ("text", Item.tsv, "lexical match"),
    "lexical_ctx": ("text", Item.tsv_ctx, "lexical match (contextual index)"),
    "dense": ("vector", Item.embedding, "semantic match"),
    "dense_ctx": ("vector", Item.embedding_ctx, "semantic match (contextual index)"),
}
RRF_K = 60
_idf: dict = {"n": -1, "weights": {}}


@dataclass
class Hit:
    item: Item
    score: float = 0.0                                       # RRF score across channels
    ranks: dict[str, int] = field(default_factory=dict)     # channel -> best rank
    rerank_score: float | None = None                        # 0-10 from the LLM reranker
    matched_terms: list[str] = field(default_factory=list)
    coverage: float = 0.0                                    # share of the task's IDF-weighted terms present

    def is_semantic_top(self, limit: int) -> bool:
        return any(rank <= limit for ch, rank in self.ranks.items() if CHANNELS[ch][0] == "vector")


def terms(text: str) -> list[str]:
    return [ALIASES.get(t, t) for t in re.findall(r"\w[\w.\-]*", text.lower())
            if (len(t) > 2 or t in KEEP_SHORT) and t not in STOPWORDS]


def idf(db: Session) -> dict[str, float]:
    # Inverse document frequency over the items table, rebuilt when the row count changes.
    # Words that appear in most of the corpus ("Deutsche", "Telekom") then barely count.
    n = db.scalar(select(func.count(Item.id)))
    if n != _idf["n"]:
        df = Counter()
        for title, content in db.execute(select(Item.title, Item.content)):
            df.update(set(terms(f"{title} {content}")))
        _idf.update(n=n, weights={t: math.log(n / c) for t, c in df.items()})
    return _idf["weights"]


def coverage(task_terms: set[str], item: Item, weights: dict[str, float]) -> tuple[list[str], float]:
    # Share of the task's term weight that the item covers. Unknown words get the maximum weight,
    # so a task about "layoffs" is not satisfied by items that only match the company name.
    top = max(weights.values(), default=1.0)
    matched = sorted(task_terms & set(terms(f"{item.title} {item.content}")))
    total = sum(weights.get(t, top) for t in task_terms)
    return matched, (sum(weights.get(t, top) for t in matched) / total if total else 0.0)


def text_search(db: Session, task: str, scopes: list[str], k: int, column, task_terms: set[str], weights: dict) -> list[list[Item]]:
    # Two lists: a strict all-terms query, and a loose any-term query pulled wide and re-ranked by
    # term coverage so a short fact matching most of the task beats a long chunk repeating two words.
    strict = func.websearch_to_tsquery("english", task)
    loose = func.to_tsquery("english", " | ".join(task_terms) or "''")
    strict_hits = list(db.scalars(select(Item).where(Item.scope.in_(scopes), column.op("@@")(strict))
                                  .order_by(func.ts_rank_cd(column, strict).desc()).limit(k)))
    rank = func.ts_rank_cd(column, loose, 1)
    rows = db.execute(select(Item, rank).where(Item.scope.in_(scopes), column.op("@@")(loose))
                      .order_by(rank.desc()).limit(k * 5)).all()
    loose_hits = [item for item, _ in sorted(rows, key=lambda r: (-coverage(task_terms, r[0], weights)[1], -r[1]))][:k]
    return [loose_hits, strict_hits]


def vector_search(db: Session, qvec: list[float], scopes: list[str], k: int, column) -> list[Item]:
    return list(db.scalars(select(Item).where(Item.scope.in_(scopes), column.isnot(None))
                           .order_by(column.cosine_distance(qvec)).limit(k)))


def embed_query(task: str) -> list[float]:
    s = get_settings()
    return OpenAI(api_key=s.openai_api_key).embeddings.create(model=s.openai_embed_model, input=[task]).data[0].embedding


def fuse(rankings: list[tuple[str, list[Item]]]) -> list[Hit]:
    # Reciprocal Rank Fusion: an item found by several channels is boosted.
    hits: dict[str, Hit] = {}
    for channel, ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            h = hits.setdefault(item.source_ref, Hit(item=item))
            h.score += 1.0 / (RRF_K + rank)
            h.ranks[channel] = min(h.ranks.get(channel, rank), rank)
    return sorted(hits.values(), key=lambda h: -h.score)


def apply_rerank(task: str, hits: list[Hit]) -> list[Hit]:
    scores = llm_rerank(task, [(h.item.title, h.item.content) for h in hits])
    for idx, score in scores.items():
        if idx < len(hits):
            hits[idx].rerank_score = score
    return sorted(hits, key=lambda h: (-(h.rerank_score if h.rerank_score is not None else -1), -h.score))


def retrieve(db: Session, task: str, scopes: list[str], k: int,
             channels: list[str] | None = None, rerank: bool | None = None) -> list[Hit]:
    s = get_settings()
    channels = [c for c in (channels or s.default_channels) if c in s.channels]
    task_terms, weights = set(terms(task)), idf(db)
    qvec = embed_query(task) if any(CHANNELS[c][0] == "vector" for c in channels) else None

    rankings = []
    for name in channels:
        kind, column, _ = CHANNELS[name]
        if kind == "text":
            rankings += [(name, r) for r in text_search(db, task, scopes, k, column, task_terms, weights)]
        else:
            rankings.append((name, vector_search(db, qvec, scopes, k, column)))

    hits = fuse(rankings)[:k]
    for h in hits:
        h.matched_terms, h.coverage = coverage(task_terms, h.item, weights)
    if (rerank if rerank is not None else s.rerank_enabled) and s.openai_api_key and hits:
        hits = apply_rerank(task, hits)
    return hits
