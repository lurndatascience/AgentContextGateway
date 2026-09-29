# Source adapters. Each yields RawItem rows in one normalized shape, carrying the
# original reference, timestamp (with its precision), scope, and a confidence that
# reflects how the content was produced (verbatim primary text > deterministic parse
# > LLM extraction > informal note).
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator

from app import financial

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
FULL_DATE = re.compile(rf"\b({MONTHS})\.? (\d{{1,2}}), (20\d\d)\b")
MONTH_DATE = re.compile(rf"\b({MONTHS}) (20\d\d)\b")
YEAR = re.compile(r"\b(20[12]\d)\b")
QUARTER_REPORT_DATE = {"Q1": (5, 15), "Q2": (8, 10), "Q3": (11, 10), "Q4": (2, 25)}

BOILERPLATE = [
    re.compile(r"Sorry,?\s*we are not allowed to show you this content[^.]*\.", re.IGNORECASE),
    re.compile(r"This media information contains forward-looking statements.*?(?=\n\n|\Z)", re.DOTALL),
    re.compile(r"Alternative performance measures are not subject to IFRS.*?(?=\n\n|\Z)", re.DOTALL),
    re.compile(r"These measures should be considered in addition to,? but not as a substitute for[^.]*\.", re.IGNORECASE),
    re.compile(r"Other companies may define these terms in different ways\.", re.IGNORECASE),
    re.compile(r"Visit us\s*-?\s*in Barcelona or on the web[^.]*\.", re.IGNORECASE),
    re.compile(r"From February 26 to February 29, 2024[^.]*\.", re.IGNORECASE),
    re.compile(r"Stage program and events:\s*\S+", re.IGNORECASE),
    re.compile(r"Claudia Nemat will be reporting live from Barcelona[^.]*\.", re.IGNORECASE),
]
CHUNK_CHARS = 1400

# How much to trust each source and why. The reason is shown to the agent with every item.
CONFIDENCE = {
    "press_release": (0.90, "verbatim primary text"),
    "record": (0.75, "record extracted by an LLM from the release"),
    "financial_fact": (0.85, "deterministic parse of a reported table"),
    "internal_note": (0.60, "informal message, not verified"),
}


@dataclass
class RawItem:
    source: str
    source_ref: str
    doc_id: str
    kind: str
    title: str
    content: str
    fields: dict | None = None
    fact_key: str | None = None
    fact_value: str | None = None
    observed_at: datetime | None = None
    timestamp_precision: str = "unknown"
    scope: str = "public"
    doc_text: str | None = None            # whole document, used only to write the situating note
    confidence: float = field(init=False)
    content_hash: str = field(init=False)

    def __post_init__(self):
        self.confidence = CONFIDENCE[self.source][0]
        stamp = f"{self.title}|{self.content}|{self.observed_at}|{self.timestamp_precision}|{self.scope}|{self.confidence}"
        self.content_hash = hashlib.sha256(stamp.encode()).hexdigest()


def find_date(text: str) -> tuple[datetime | None, str]:
    # Best in-text date, with how precise it is. An undated document stays undated.
    if m := FULL_DATE.search(text):
        return datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y"), "day"
    if m := MONTH_DATE.search(text):
        return datetime.strptime(f"{m.group(1)} {m.group(2)}", "%B %Y"), "month"
    years = [y for y in YEAR.findall(text) if 2019 <= int(y) <= 2026]   # skip "by 2030" style targets
    if years:
        return datetime(int(Counter(years).most_common(1)[0][0]), 7, 1), "year"   # mid-year guess
    return None, "unknown"


def report_date(quarter: str) -> datetime:
    # Results releases carry period-end dates in their tables, not a publication date,
    # so we infer a typical publication date from the quarter and label it "inferred".
    q, year = quarter.split()
    month, day = QUARTER_REPORT_DATE[q]
    return datetime(int(year) + (1 if q == "Q4" else 0), month, day)


def strip_boilerplate(text: str) -> str:
    for pat in BOILERPLATE:
        text = pat.sub(" ", text)
    return re.sub(r"[ \t]+", " ", text)


def chunk(text: str) -> list[str]:
    chunks, cur = [], ""
    for para in (p.strip() for p in text.split("\n") if p.strip()):
        if cur and len(cur) + len(para) > CHUNK_CHARS:
            chunks.append(cur)
            cur = ""
        cur = f"{cur}\n{para}".strip()
    return chunks + [cur] if cur else chunks


def _read_docs(data_dir: Path) -> dict[str, str]:
    return {p.stem: p.read_text() for p in sorted((data_dir / "press_releases").glob("*.txt"), key=lambda p: int(p.stem))}


def _read_records(data_dir: Path) -> dict[str, dict]:
    with open(data_dir / "records.jsonl") as f:
        return {r["doc_id"]: r for r in map(json.loads, f)}


def _doc_date(doc_id: str, text: str) -> tuple[datetime | None, str]:
    if financial.has_table(text) and (q := financial.infer_quarter(text)):
        return report_date(q), "inferred"
    return find_date(text)


def press_releases(data_dir: Path) -> Iterator[RawItem]:
    # Unstructured source: one item per chunk of the verbatim press release.
    titles = {k: v["title"] for k, v in _read_records(data_dir).items()}
    for doc_id, raw in _read_docs(data_dir).items():
        text = strip_boilerplate(raw)
        lines = text.split("\n")
        if financial.has_table(raw) and (start := financial.table_start([ln.strip() for ln in lines if ln.strip()])):
            kept = [ln for ln in lines if ln.strip()][:start]     # narrative only; the table becomes facts
            text = "\n".join(kept)
        observed, precision = _doc_date(doc_id, raw)
        for i, piece in enumerate(chunk(text)):
            yield RawItem(source="press_release", source_ref=f"press_release/{doc_id}#{i}", doc_id=doc_id,
                          kind="unstructured", title=titles.get(doc_id, f"Press release {doc_id}"),
                          content=piece, observed_at=observed, timestamp_precision=precision,
                          scope="public", doc_text=text)


def records(data_dir: Path) -> Iterator[RawItem]:
    # Structured source: one record per release, extracted by an LLM in the earlier project.
    docs = _read_docs(data_dir)
    for doc_id, r in _read_records(data_dir).items():
        observed, precision = _doc_date(doc_id, docs.get(doc_id, ""))
        parts = [r["title"] + ".", r["summary"]]
        if r.get("key_metrics"):
            parts.append("Key metrics: " + "; ".join(r["key_metrics"]) + ".")
        for label, key in [("Organizations", "organizations_norm"), ("People", "people"), ("Technologies", "technologies")]:
            if r.get(key):
                parts.append(f"{label}: " + ", ".join(r[key]) + ".")
        yield RawItem(source="record", source_ref=f"record/{doc_id}", doc_id=doc_id, kind="structured",
                      title=r["title"], content=" ".join(parts), fields=r,
                      observed_at=observed, timestamp_precision=precision, scope="public")


def financial_facts(data_dir: Path) -> Iterator[RawItem]:
    # Structured source: one fact per (metric, period) cell in a results table.
    # Comparator columns (e.g. FY 2023 inside the Q1 2024 release) are kept on purpose:
    # they are the duplicates and restatements the gateway has to reconcile.
    for doc_id, raw in _read_docs(data_dir).items():
        if not financial.has_table(raw):
            continue
        quarter = financial.infer_quarter(raw) or "unknown period"
        cols = financial.parse_columns(raw)
        observed = report_date(quarter) if quarter != "unknown period" else None
        seen = set()   # a metric label repeated in a second, unlabelled table section is ambiguous: keep the first
        for row in financial.parse_rows(raw):
            for i, period in enumerate(cols):
                if i >= len(row["values"]) or period.startswith("Change") or (row["metric"], period) in seen:
                    continue
                seen.add((row["metric"], period))
                metric, value = row["metric"], row["values"][i]
                yield RawItem(source="financial_fact", source_ref=f"financial_fact/{doc_id}:{metric}|{period}",
                              doc_id=doc_id, kind="structured", title=f"{metric}, {period}",
                              content=f"Deutsche Telekom {metric} for {period}: {value} (as reported in the {quarter} results release, doc {doc_id}; millions of € unless the metric is a percentage or per-share figure).",
                              fields={"metric": metric, "period": period, "value": value, "reported_in": quarter},
                              fact_key=f"{metric}|{period}", fact_value=value,
                              observed_at=observed, timestamp_precision="inferred" if observed else "unknown",
                              scope="public")


def internal_notes(data_dir: Path) -> Iterator[RawItem]:
    # Unstructured source: team messages. Some are internal, some private. A note may carry
    # tagged facts, which become structured items with the note's scope and a low confidence.
    with open(data_dir / "internal_notes.jsonl") as f:
        for n in map(json.loads, f):
            sent = datetime.fromisoformat(n["sent_at"])
            title = f"#{n['channel']} message from {n['author']}"
            yield RawItem(source="internal_note", source_ref=f"internal_note/{n['id']}", doc_id=n["id"],
                          kind="unstructured", title=title, content=n["text"],
                          fields={"channel": n["channel"], "author": n["author"]},
                          observed_at=sent, timestamp_precision="day", scope=n["scope"])
            for j, fact in enumerate(n.get("facts", [])):
                metric, period = fact["key"].split("|")
                yield RawItem(source="internal_note", source_ref=f"internal_note/{n['id']}:fact{j}", doc_id=n["id"],
                              kind="structured", title=f"{metric}, {period}",
                              content=f"Deutsche Telekom {metric} for {period}: {fact['value']} (stated in a #{n['channel']} message by {n['author']}).",
                              fields={"metric": metric, "period": period, "value": fact["value"], "channel": n["channel"]},
                              fact_key=fact["key"], fact_value=fact["value"],
                              observed_at=sent, timestamp_precision="day", scope=n["scope"])


ADAPTERS = [press_releases, records, financial_facts, internal_notes]


def all_items(data_dir: str) -> list[RawItem]:
    root = Path(data_dir)
    return [item for adapter in ADAPTERS for item in adapter(root)]
