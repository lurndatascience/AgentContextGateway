# Offline checks that need no database and no API key: the adapters, the parser, and the
# deterministic agent fallback. Run with: python -m pytest tests
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gateway"))

from app.agents import extractive                                   # noqa: E402
from app.contract import ContextItem, ContextPackage, Evidence, Principal, Warning   # noqa: E402
from app.sources import all_items, find_date                        # noqa: E402

DATA = str(Path(__file__).resolve().parents[1] / "data")
ITEMS = all_items(DATA)


def test_every_source_is_present_with_one_row_shape():
    by_source = Counter(i.source for i in ITEMS)
    assert set(by_source) == {"press_release", "record", "financial_fact", "internal_note"}
    assert all(i.source_ref and i.doc_id and i.content and i.scope and i.content_hash for i in ITEMS)


def test_private_material_is_labelled_private():
    private = [i for i in ITEMS if i.scope == "private"]
    assert private and all(i.source == "internal_note" for i in private)
    assert any("Q1 2026" in i.content for i in private)


def test_financial_facts_contain_the_restated_fy2022_service_revenue():
    values = defaultdict(set)
    for i in ITEMS:
        if i.fact_key:
            values[i.fact_key].add(i.fact_value.replace(",", ""))
    assert values["Service revenue|FY 2022"] == {"91947", "91988"}


def test_dates_carry_their_precision():
    assert find_date("Bonn, March 5, 2024. Deutsche Telekom ...") == (datetime(2024, 3, 5), "day")
    assert find_date("In March 2024 the company ...") == (datetime(2024, 3, 1), "month")
    assert find_date("No date here at all")[1] == "unknown"


def test_extractive_fallback_cites_and_reports_warnings():
    ev = Evidence(source="record", source_ref="record/1", doc_id="1", observed_at=None, timestamp_precision="unknown",
                  ingested_at=datetime(2026, 1, 1), scope="public", confidence=0.75, quote="q")
    item = ContextItem(ref="[1]", kind="structured", title="t", content="First sentence. Second sentence.",
                       evidence=[ev], freshness="unknown", score=0.1, why=["because"])
    pkg = ContextPackage(task="x", as_of=datetime(2026, 1, 1), principal=Principal(agent="a", scopes=["public"]),
                         scopes_applied=["public"], items=[item], warnings=[Warning(kind="missing", message="gap")],
                         candidates_considered=1, tokens_used=10, budget_tokens=100)
    out = extractive(pkg)
    assert "First sentence. [1]" in out and "Warning (missing): gap" in out
    assert "cannot be answered" in extractive(pkg.model_copy(update={"items": []}))
