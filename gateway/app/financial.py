# Parse the broken financial tables in Deutsche Telekom results releases.
# DT serialises tables one cell per line. We read the header region for column labels
# and pair each metric label with the numbers that follow it. Carried over from the
# press-release RAG's ingestion service, trimmed to the four functions the gateway uses.
import re

NUMERIC = re.compile(r"^-?[\d,]+\.?\d*\s*[%€$]?$|^-?\d+\.\d+p?$|^n\.a\.$")
PERIOD = re.compile(r"^(Q[1-4][\s-]Q[1-4]\s*\d{4}|Q[1-4]\s*\d{4}|FY\s*\d{4})$", re.IGNORECASE)
DATE_HEADER = re.compile(r"^[A-Z][a-z]+\.?\s+\d{1,2},\s+\d{4}$")
QUARTER_IN_TEXT = re.compile(r"\b(Q[1-4])\s+(\d{4})\b")
QUARTER_IN_PROSE = re.compile(r"\b(first|second|third|fourth)\s+quarter\s+of\s+(\d{4})\b", re.IGNORECASE)
PROSE_TO_Q = {"first": "Q1", "second": "Q2", "third": "Q3", "fourth": "Q4"}
HEADER_PERIOD_START = re.compile(r"^(Q[1-4][- ]Q[1-4]|Q[1-4]|FY)$", re.IGNORECASE)
HEADER_YEAR = re.compile(r"^20\d{2}$")
UNIT_LINE = re.compile(r"^(millions of\s*[€$]?|in\s+EUR|in\s+USD|thousands)\s*$", re.IGNORECASE)
NOISE_HEADER = {"Change", "%", "millions of €", "in EUR", "in USD", "EUR", "USD", "thousands",
                "Q1-Q3", "Q1-Q2", "Q1", "Q2", "Q3", "Q4"}
UNIT_MARKERS = ("millions of", "thousands", "in eur", "in usd")


def _lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.split("\n") if ln.strip()]


def has_table(text: str) -> bool:
    lines = _lines(text)
    if len(lines) < 20:
        return False
    numeric_ratio = sum(1 for ln in lines if NUMERIC.match(ln)) / len(lines)
    return numeric_ratio >= 0.20 and any(m in text.lower() for m in UNIT_MARKERS)


def table_start(lines: list[str]) -> int | None:
    return next((i for i, ln in enumerate(lines)
                 if PERIOD.match(ln) or DATE_HEADER.match(ln) or ln == "millions of €"), None)


def parse_rows(text: str) -> list[dict]:
    lines = _lines(text)
    start = table_start(lines)
    if start is None:
        return []
    rows, label, vals = [], None, []
    for ln in lines[start:]:
        low = ln.lower()
        if "forward-looking statements" in low or "comments on the table" in low:
            break
        if (PERIOD.match(ln) or DATE_HEADER.match(ln) or ln in NOISE_HEADER
                or re.match(r"^20\d{2}$", ln) or re.match(r"^Q\d-Q\d$", ln)):
            continue
        if NUMERIC.match(ln):
            vals.append(ln)
        elif 2 <= len(ln) <= 90 and not ln.endswith("."):
            if label and vals:
                rows.append({"metric": label, "values": vals})
            label, vals = ln, []
    if label and vals:
        rows.append({"metric": label, "values": vals})
    return rows


def parse_columns(text: str) -> list[str]:
    # Header region -> ordered labels, e.g. ['Q1 2024', 'Q1 2023', 'Change %', 'FY 2023'].
    lines = _lines(text)
    start = next((i for i, ln in enumerate(lines) if PERIOD.match(ln) or DATE_HEADER.match(ln)
                  or HEADER_PERIOD_START.match(ln) or UNIT_LINE.match(ln)), None)
    if start is None:
        return []
    cols, cur = [], None
    for ln in lines[start:]:
        if NUMERIC.match(ln):
            break
        if HEADER_YEAR.match(ln) and cur and HEADER_PERIOD_START.match(cur):
            cur = f"{cur} {ln}"
        elif PERIOD.match(ln):
            if cur:
                cols.append(cur)
            cols.append(ln.upper())
            cur = None
        elif HEADER_PERIOD_START.match(ln):
            if cur:
                cols.append(cur)
            cur = ln.upper().replace(" ", "-")
        elif ln == "Change":
            if cur:
                cols.append(cur)
            cur = "Change"
        elif ln == "%" and cur == "Change":
            cur = "Change %"
        elif UNIT_LINE.match(ln):
            if cur:
                cols.append(cur)
                cur = None
        elif DATE_HEADER.match(ln):
            if cur:
                cols.append(cur)
            cols.append(ln)
            cur = None
        else:
            break
    if cur:
        cols.append(cur)
    return cols


def infer_quarter(text: str) -> str | None:
    m = QUARTER_IN_TEXT.search(text)
    if m:
        return f"{m.group(1)} {m.group(2)}"
    m = QUARTER_IN_PROSE.search(text)
    return f"{PROSE_TO_Q[m.group(1).lower()]} {m.group(2)}" if m else None
