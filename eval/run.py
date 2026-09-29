# End-to-end evaluation against a running gateway. Stdlib only, so it runs anywhere:
#   python eval/run.py            (GATEWAY_URL defaults to http://127.0.0.1:8002)
# Writes eval/results/report.md and eval/results/results.json.
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
import urllib.error
import urllib.request
from pathlib import Path

API = os.environ.get("GATEWAY_URL", "http://127.0.0.1:8002")
# The eval picks its access level the way the demo page does (DEMO_MODE must be on).
AS_OF = "2024-07-01T00:00:00"          # the corpus's present; press releases run to mid 2024
HERE = Path(__file__).resolve().parent

SHOWCASE = [
    {"name": "Factual lookup combining prose and a structured record", "key": "public", "as_of": AS_OF,
     "task": "Which company became a premium supplier of RISE with SAP?",
     "expect": {"doc_ids": ["43"], "kinds": {"structured", "unstructured"}}},
    {"name": "Conflicting fact: FY 2022 service revenue was restated", "key": "internal", "as_of": AS_OF,
     "task": "What was Deutsche Telekom's service revenue in FY 2022?",
     "expect": {"warning": "conflict", "value": "91,988"}},
    {"name": "Duplicate fact confirmed by two internal notes", "key": "internal", "as_of": AS_OF,
     "task": "What FY 2023 dividend per share did the AGM approve?",
     "expect": {"warning": "duplicate"}},
    {"name": "Tempting private item must stay out (internal scope)", "key": "internal", "as_of": "2026-05-01T00:00:00",
     "task": "What are the preliminary Q1 2026 results, net revenue and adjusted EBITDA?",
     "expect": {"warning": "missing", "exclude_prefix": "internal_note/n03"}, "compare": "finance"},
    {"name": "Stale guidance when the task asks for the current figure", "key": "internal", "as_of": AS_OF,
     "task": "What is the current full-year guidance for adjusted EBITDA AL?",
     "expect": {"warning": "stale"}},
    {"name": "Out-of-corpus question should come back empty", "key": "public", "as_of": AS_OF,
     "task": "Who won the Champions League in 2023?",
     "expect": {"max_items": 0}},
]
# Retrieval ablation: each configuration is run over the whole golden set on the same deployment.
ABLATION = [
    ("lexical only", {"channels": ["lexical"], "rerank": False}),
    ("lexical + dense (baseline)", {"channels": ["lexical", "dense"], "rerank": False}),
    ("baseline + LLM reranker", {"channels": ["lexical", "dense"], "rerank": True}),
    ("contextual retrieval", {"channels": ["lexical_ctx", "dense_ctx"], "rerank": False}),
    ("contextual retrieval + LLM reranker", {"channels": ["lexical_ctx", "dense_ctx"], "rerank": True}),
]
AGENT_TASKS = [
    ("answer", "internal", "What was Deutsche Telekom's service revenue in FY 2022?"),
    ("brief", "public", "T-Systems and SAP partnership"),
]


def post(path: str, key: str, body: dict) -> tuple[int, dict, float]:
    req = urllib.request.Request(f"{API}{path}", data=json.dumps(body).encode(), method="POST",
                                 headers={"content-type": "application/json", "x-demo-level": key})
    t0 = time.perf_counter()
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, json.load(r), time.perf_counter() - t0
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code < 500:
                return e.code, json.loads(body), time.perf_counter() - t0
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(10 * (attempt + 1))          # gateway restarting or proxy hiccup: wait and retry
    raise RuntimeError(f"{path} failed after 3 attempts")


def context(key: str, task: str, as_of: str = AS_OF, budget: int = 1500, **opts) -> tuple[dict, float]:
    status, pkg, dt = post("/context", key, {"task": task, "as_of": as_of, "budget_tokens": budget, **opts})
    assert status == 200, pkg
    return pkg, dt


def doc_ids(pkg: dict) -> list[set[str]]:
    return [{e["doc_id"] for e in it["evidence"]} for it in pkg["items"]]


def render(pkg: dict) -> str:
    out = [f"scopes `{'+'.join(pkg['scopes_applied'])}`, as of {pkg['as_of'][:10]}, {len(pkg['items'])} items, "
           f"{pkg['tokens_used']}/{pkg['budget_tokens']} tokens, {pkg['candidates_considered']} candidates considered", ""]
    for w in pkg["warnings"]:
        out.append(f"- **{w['kind']}** {' '.join(w['refs'])}: {w['message']} *Resolution: {w['resolution']}*")
    for it in pkg["items"]:
        ev = "; ".join(f"`{e['source_ref']}` scope={e['scope']} conf={e['confidence']} observed={(e['observed_at'] or 'unknown')[:10]} ({e['timestamp_precision']})" for e in it["evidence"])
        out += ["", f"**{it['ref']} {it['title']}** ({it['kind']}, {it['freshness']}, score {it['score']})",
                f"> {it['content'][:400].replace(chr(10), ' ')}", f"- evidence: {ev}", "- why: " + " / ".join(it["why"])]
    return "\n".join(out)


def check(sc: dict, pkg: dict) -> list[str]:
    e, fails = sc["expect"], []
    kinds = {it["kind"] for it in pkg["items"]}
    all_refs = {ev["source_ref"] for it in pkg["items"] for ev in it["evidence"]}
    if "doc_ids" in e and not any(set(e["doc_ids"]) & d for d in doc_ids(pkg)):
        fails.append(f"expected docs {e['doc_ids']} not in package")
    if "kinds" in e and not e["kinds"] <= kinds:
        fails.append(f"expected kinds {e['kinds']}, got {kinds}")
    if "warning" in e and e["warning"] not in {w["kind"] for w in pkg["warnings"]}:
        fails.append(f"expected a {e['warning']} warning")
    if "value" in e and not any(it["fields"] and it["fields"].get("value") == e["value"] for it in pkg["items"]):
        fails.append(f"expected resolved value {e['value']}")
    if "exclude_prefix" in e and any(r.startswith(e["exclude_prefix"]) for r in all_refs):
        fails.append(f"private item {e['exclude_prefix']} leaked")
    if "max_items" in e and len(pkg["items"]) > e["max_items"]:
        fails.append(f"expected at most {e['max_items']} items, got {len(pkg['items'])}")
    return fails


def attribution(items: list[dict]) -> float:
    ok = sum(1 for it in items if it["why"] and it["evidence"] and all(
        e["source_ref"] and e["scope"] and e["quote"] and e["timestamp_precision"] and e["confidence"] is not None for e in it["evidence"]))
    return ok / len(items) if items else 1.0


def citation_coverage(text: str, refs: set[str]) -> float:
    sentences = [s for s in re.split(r"(?<=[.!?])\s+|\n+", text) if len(s.strip()) > 20]
    cited = sum(1 for s in sentences if set(re.findall(r"\[\d+\]", s)) & refs)
    return cited / len(sentences) if sentences else 0.0


def golden_metrics(gold: list[dict], **opts) -> dict:
    def one(g):
        pkg, dt = context("public", g["query"], **opts)
        return g, pkg, dt

    with ThreadPoolExecutor(4) as pool:
        runs = list(pool.map(one, gold))
    hit, recall, rr, refusals_ok, refusals, items_all, leaks = 0, 0.0, 0.0, 0, 0, [], 0
    for g, pkg, _ in runs:
        items_all += pkg["items"]
        leaks += sum(1 for it in pkg["items"] for e in it["evidence"] if e["scope"] not in pkg["scopes_applied"])
        if g["expected_action"] == "refuse":
            refusals += 1
            refusals_ok += int(not pkg["items"] or any(w["kind"] == "missing" for w in pkg["warnings"]))
            continue
        expected, ranks = set(g["expected_doc_ids"]), doc_ids(pkg)
        found = {d for r in ranks for d in r & expected}
        hit += int(bool(found))
        recall += len(found) / len(expected) if expected else 1
        rr += next((1 / (i + 1) for i, r in enumerate(ranks) if r & expected), 0)
    answerable = len(gold) - refusals
    return {"answerable": answerable, "hit_rate": hit / answerable, "doc_recall": recall / answerable, "mrr": rr / answerable,
            "refusals": refusals, "refusal_correct": refusals_ok / refusals if refusals else None,
            "attribution_completeness": attribution(items_all), "items_returned": len(items_all),
            "avg_items": len(items_all) / len(gold), "scope_leaks": leaks,
            "avg_latency_ms": 1000 * sum(dt for _, _, dt in runs) / len(runs)}


def run_showcase(report: list[str], results: dict) -> None:
    report += ["## Showcase queries", ""]
    for sc in SHOWCASE:
        pkg, dt = context(sc["key"], sc["task"], sc["as_of"])
        fails = check(sc, pkg)
        results["showcase"].append({"name": sc["name"], "pass": not fails, "fails": fails})
        report += [f"### {sc['name']}", "", f"Task: *{sc['task']}*  ", f"Result: **{'PASS' if not fails else 'FAIL: ' + '; '.join(fails)}** ({dt * 1000:.0f} ms)", "", render(pkg)]
        if sc.get("compare"):
            other, _ = context(sc["compare"], sc["task"], sc["as_of"])
            report += ["", f"Same task with the `{sc['compare']}` key (private scope allowed):", "", render(other)]
        report.append("")


def run_golden(report: list[str], results: dict, health: dict, gold: list[dict]) -> None:
    report += ["## Golden set: retrieval relevance and attribution", "",
               f"Default configuration: channels {health['default_channels']}, reranker {'on' if health['rerank'] else 'off'}.", ""]
    r = results["golden"] = golden_metrics(gold)
    report += ["| metric | value |", "|---|---|",
               f"| answerable questions | {r['answerable']} |", f"| hit rate (an expected doc is in the package) | {r['hit_rate']:.0%} |",
               f"| expected-doc recall | {r['doc_recall']:.0%} |", f"| MRR | {r['mrr']:.2f} |",
               f"| refusal questions returned empty or a missing warning | {r['refusal_correct']:.0%} of {r['refusals']} |",
               f"| attribution completeness (item has evidence with ref, scope, confidence, timestamp precision, quote, and reasons) | {r['attribution_completeness']:.0%} of {r['items_returned']} items |",
               f"| average items per package | {r['avg_items']:.1f} |", f"| out-of-scope evidence returned | {r['scope_leaks']} |",
               f"| average latency | {r['avg_latency_ms']:.0f} ms |", ""]


def run_ablation(report: list[str], results: dict, health: dict, gold: list[dict]) -> None:
    report += ["## Retrieval ablation", "", "Same golden set, same deployment; the reranker column also acts as the relevance judge. Rows whose channels this deployment cannot serve are skipped.", "",
               "| configuration | hit rate | doc recall | MRR | refusals empty | avg items | latency |", "|---|---|---|---|---|---|---|"]
    available = set(health["channels"])
    for name, opts in ABLATION:
        if not set(opts["channels"]) <= available or (opts["rerank"] and not health["rerank"]):
            report.append(f"| {name} | skipped | | | | | |")
            continue
        m = results["ablation"][name] = golden_metrics(gold, **opts)
        report.append(f"| {name} | {m['hit_rate']:.0%} | {m['doc_recall']:.0%} | {m['mrr']:.2f} | {m['refusal_correct']:.0%} | {m['avg_items']:.1f} | {m['avg_latency_ms']:.0f} ms |")
        print(f"ablation {name}: hit={m['hit_rate']:.0%} recall={m['doc_recall']:.0%} mrr={m['mrr']:.2f} refusal={m['refusal_correct']:.0%}")
    report.append("")


def run_agents(report: list[str], results: dict) -> None:
    report += ["## Downstream agents on the same contract", ""]
    for kind, key, text in AGENT_TASKS:
        status, res, dt = post(f"/agents/{kind}", key, {"text": text, "as_of": AS_OF})
        if status != 200:
            report += [f"### {kind}: *{text}*", "", f"Skipped: {res.get('detail')}", ""]
            results["agents"].append({"agent": kind, "skipped": res.get("detail")})
            continue
        cov = citation_coverage(res["output"], {it["ref"] for it in res["package"]["items"]})
        results["agents"].append({"agent": kind, "citation_coverage": cov, "mode": res.get("mode")})
        report += [f"### {kind}: *{text}*", "", f"Mode: {res.get('mode')}. Sentence citation coverage: **{cov:.0%}** ({dt * 1000:.0f} ms)", "", "```", res["output"], "```", "",
                   "Package handed to the agent:", "", render(res["package"]), ""]


def main():
    health = json.load(urllib.request.urlopen(f"{API}/health"))
    gold = [json.loads(l) for l in open(HERE / "golden.jsonl")]
    report = ["# Gateway evaluation", "", f"Gateway: {API}", "", f"Items in store: {health['items']}. LLM configured: {health['llm']}."]
    results = {"showcase": [], "golden": {}, "ablation": {}, "agents": []}

    run_showcase(report, results)
    run_golden(report, results, health, gold)
    run_ablation(report, results, health, gold)
    run_agents(report, results)

    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "report.md").write_text("\n".join(report))
    (HERE / "results" / "results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results["golden"], indent=2))
    print("showcase:", [(s["name"], "PASS" if s["pass"] else s["fails"]) for s in results["showcase"]])
    print("agents:", results["agents"])


if __name__ == "__main__":
    main()
