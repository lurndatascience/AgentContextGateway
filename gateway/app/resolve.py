# Turn a task into the smallest useful context package:
# retrieve -> reconcile facts (duplicates, conflicts) -> pack to budget -> link related
# structured evidence -> grade freshness -> flag what is stale or missing -> explain.
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.contract import ContextItem, ContextPackage, ContextRequest, Evidence, Principal, Warning
from app.db import Item
from app.retrieve import CHANNELS, Hit, retrieve
from app.sources import CONFIDENCE

PERIOD = re.compile(r"\b((?:Q[1-4]|FY)\s?20\d\d)\b", re.IGNORECASE)
YEAR = re.compile(r"\b20\d\d\b")


@dataclass
class Candidate:
    primary: Item
    score: float
    evidence: list[Item]                       # primary first, then every source that supports it
    why: list[str] = field(default_factory=list)
    warnings: list[Warning] = field(default_factory=list)


def tokens(text: str) -> int:
    return len(text) // 4 + 1


def norm_period(p: str) -> str:
    return re.sub(r"^(Q[1-4]|FY)\s*", r"\1 ", p.upper())


def observed_label(item: Item) -> str:
    return f"{item.observed_at.date()} ({item.timestamp_precision} precision)" if item.observed_at else "no timestamp in source"


def freshness(item: Item, as_of: datetime) -> str:
    s = get_settings()
    if item.observed_at is None:
        return "unknown"
    age = (as_of - item.observed_at).days
    return "fresh" if age <= s.fresh_days else "aging" if age <= s.stale_days else "stale"


# ---- relevance and explanation -------------------------------------------------------------

def relevant(h: Hit) -> bool:
    s = get_settings()
    if h.rerank_score is not None:
        return h.rerank_score >= s.rerank_min_score
    return h.coverage >= s.min_coverage or h.is_semantic_top(s.semantic_rank_ok)


def explain_hit(h: Hit) -> list[str]:
    why = []
    for channel, rank in h.ranks.items():
        kind, _, label = CHANNELS[channel]
        detail = f", covers {h.coverage:.0%} of the task's term weight: {', '.join(h.matched_terms[:6])}" if kind == "text" else ""
        why.append(f"{label} rank {rank}{detail}")
    if h.rerank_score is not None:
        why.append(f"LLM reranker score {h.rerank_score:.0f}/10")
    if h.item.context_note:
        why.append(f"indexed with context note: {h.item.context_note[:120]}")
    if h.item.fact_key:
        why.append(f"structured fact for {h.item.fields['period']}, compact and directly quotable")
    return why


# ---- reconciliation of facts ---------------------------------------------------------------

def fact_groups(db: Session, hits: list[Hit], scopes: list[str]) -> dict[str, list[Item]]:
    # Every in-scope row sharing a fact_key with a hit, newest and most confident first. Loading
    # the whole group means a conflicting row that retrieval missed is still seen.
    keys = {h.item.fact_key for h in hits if h.item.fact_key}
    groups: dict[str, list[Item]] = {k: [] for k in keys}
    if keys:
        for row in db.scalars(select(Item).where(Item.fact_key.in_(keys), Item.scope.in_(scopes))):
            groups[row.fact_key].append(row)
    for group in groups.values():
        group.sort(key=lambda i: (i.observed_at or datetime.min, i.confidence), reverse=True)
    return groups


def merge_fact(h: Hit, group: list[Item]) -> Candidate:
    # Agreeing values merge into one item that cites every source. Disagreeing values become a
    # conflict resolved in favour of the newest, most confident source, with all values cited.
    winner, key = group[0], h.item.fact_key
    values = {i.fact_value.replace(",", "").strip() for i in group}
    c = Candidate(winner, h.score, group, explain_hit(h))
    if len(group) > 1 and len(values) == 1:
        c.why.append(f"same value confirmed by {len(group)} sources, merged into one item")
        c.warnings.append(Warning(kind="duplicate", refs=[i.source_ref for i in group],
                                  message=f"{key} = {winner.fact_value} is reported by {len(group)} sources.",
                                  resolution="Merged into one item; every source is cited."))
    elif len(values) > 1:
        listing = "; ".join(f"{i.fact_value} from {i.source_ref} ({i.observed_at.date() if i.observed_at else 'undated'}, confidence {i.confidence})" for i in group)
        c.why.append(f"chosen over {len(values) - 1} conflicting value(s) as the most recent, most confident source")
        c.warnings.append(Warning(kind="conflict", refs=[i.source_ref for i in group],
                                  message=f"{key} has {len(values)} different values: {listing}.",
                                  resolution=f"Kept {winner.fact_value} from {winner.source_ref}; later reports restate earlier figures. All values are cited so the agent can disclose the discrepancy."))
    return c


def reconcile(db: Session, hits: list[Hit], scopes: list[str]) -> list[Candidate]:
    # One candidate per fact_key and per distinct text, in retrieval order.
    groups = fact_groups(db, hits, scopes)
    cands, seen_keys, seen_hash = [], set(), set()
    for h in filter(relevant, hits):
        item = h.item
        if item.content_hash in seen_hash or (item.fact_key and item.fact_key in seen_keys):
            continue
        seen_hash.add(item.content_hash)
        if item.fact_key:
            seen_keys.add(item.fact_key)
            cands.append(merge_fact(h, groups[item.fact_key]))
        else:
            cands.append(Candidate(item, h.score, [item], explain_hit(h)))
    return cands


# ---- packing -------------------------------------------------------------------------------

def pack(cands: list[Candidate], budget: int) -> tuple[list[Candidate], int]:
    s, used, per_doc, chosen = get_settings(), 0, {}, []
    for c in cands:
        if len(chosen) >= s.max_items:
            break
        doc_key = (c.primary.source, c.primary.doc_id)
        cost = tokens(c.primary.content)
        if (c.primary.kind == "unstructured" and per_doc.get(doc_key, 0) >= s.per_doc_cap) or used + cost > budget:
            continue
        used += cost
        per_doc[doc_key] = per_doc.get(doc_key, 0) + 1
        chosen.append(c)
    return chosen, used


def link_records(db: Session, chosen: list[Candidate], used: int, budget: int, scopes: list[str]) -> int:
    # Prose chunks and table facts get the structured record of their release attached when
    # the budget allows, so the agent sees parsed entities and metrics next to the evidence.
    have = {c.primary.source_ref for c in chosen}
    for idx, c in enumerate(list(chosen), start=1):
        ref = f"record/{c.primary.doc_id}"
        if c.primary.source not in ("press_release", "financial_fact") or ref in have:
            continue
        rec = db.scalar(select(Item).where(Item.source_ref == ref, Item.scope.in_(scopes)))
        if rec and used + tokens(rec.content) <= budget and len(chosen) < get_settings().max_items:
            chosen.append(Candidate(rec, c.score, [rec], [f"structured record for the same release as [{idx}]"]))
            have.add(ref)
            used += tokens(rec.content)
    return used


# ---- package assembly ----------------------------------------------------------------------

def evidence(i: Item) -> Evidence:
    return Evidence(source=i.source, source_ref=i.source_ref, doc_id=i.doc_id, observed_at=i.observed_at,
                    timestamp_precision=i.timestamp_precision, ingested_at=i.ingested_at, scope=i.scope,
                    confidence=i.confidence, quote=i.content[:280])


def to_item(n: int, c: Candidate, as_of: datetime) -> ContextItem:
    p = c.primary
    fresh = freshness(p, as_of)
    why = c.why + [f"confidence {p.confidence}: {CONFIDENCE[p.source][1]}", f"freshness {fresh}: observed {observed_label(p)}"]
    return ContextItem(ref=f"[{n}]", kind=p.kind, title=p.title, content=p.content, fields=p.fields,
                       evidence=[evidence(i) for i in c.evidence], freshness=fresh, score=round(c.score, 4), why=why)


def stale_warning(task: str, chosen: list[Candidate], items: list[ContextItem], as_of: datetime) -> list[Warning]:
    # Stale items are flagged unless the task itself asks about their year.
    years_in_task = set(YEAR.findall(task))
    refs = [c.primary.source_ref for c, it in zip(chosen, items)
            if it.freshness == "stale" and not any(y in c.primary.content for y in years_in_task)]
    if not refs:
        return []
    return [Warning(kind="stale", refs=refs,
                    message=f"{len(refs)} item(s) are older than {get_settings().stale_days} days as of {as_of.date()} and the task does not ask about their period.",
                    resolution="Prefer a newer source if one appears in the package; otherwise say the information may be outdated.")]


def missing_warnings(task: str, items: list[ContextItem]) -> list[Warning]:
    out = []
    if not items:
        out.append(Warning(kind="missing", message="No in-scope evidence found for this task.",
                           resolution="The agent should say it cannot answer from available context."))
    for period in {norm_period(p) for p in PERIOD.findall(task)}:
        if not any(period == (i.fields or {}).get("period") or period in i.content for i in items):
            out.append(Warning(kind="missing", message=f"The task mentions {period} but no in-scope evidence covers that period.",
                               resolution="Do not infer the figure; report it as unavailable."))
    return out


def cite_refs(items: list[ContextItem], warnings: list[Warning]) -> None:
    # Warnings are built with source_refs; translate them to the package's citation tags.
    ref_of = {e.source_ref: it.ref for it in items for e in it.evidence}
    for w in warnings:
        w.refs = sorted({ref_of.get(r, r) for r in w.refs})


def resolve(db: Session, req: ContextRequest, principal: Principal) -> ContextPackage:
    s = get_settings()
    as_of = (req.as_of or datetime.now(timezone.utc)).replace(tzinfo=None)
    hits = retrieve(db, req.task, principal.scopes, s.retrieval_top_k, req.channels, req.rerank)
    chosen, used = pack(reconcile(db, hits, principal.scopes), req.budget_tokens)
    used = link_records(db, chosen, used, req.budget_tokens, principal.scopes)

    items = [to_item(n, c, as_of) for n, c in enumerate(chosen, start=1)]
    warnings = [w for c in chosen for w in c.warnings] + stale_warning(req.task, chosen, items, as_of) + missing_warnings(req.task, items)
    cite_refs(items, warnings)
    return ContextPackage(task=req.task, as_of=as_of, principal=principal, scopes_applied=principal.scopes,
                          items=items, warnings=warnings, candidates_considered=len(hits),
                          tokens_used=used, budget_tokens=req.budget_tokens)
