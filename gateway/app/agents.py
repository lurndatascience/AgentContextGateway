# Two downstream agents built with PydanticAI. Each is one instruction on top of the same
# gateway contract: the context package is the agent's only knowledge. Without an API key the
# agents fall back to a deterministic extract of the package, so the core path always runs.
from functools import lru_cache

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from sqlalchemy.orm import Session

from app.config import get_settings
from app.contract import ContextPackage, ContextRequest, Principal
from app.resolve import resolve

RULES = (
    "Work only from the context package. End every factual sentence with the citation tag(s) of the "
    "item(s) it comes from, like [2]. Never use knowledge outside the package. If the package is empty "
    "or does not cover the task, say so plainly. If a warning affects your answer, say how you handled it. "
)
ANSWER = "Answer the question in at most four sentences."
BRIEF = "Write a three-bullet brief for an executive, one cited sentence per bullet."


@lru_cache
def agent(instruction: str) -> Agent:
    s = get_settings()
    model = OpenAIChatModel(s.openai_llm_model, provider=OpenAIProvider(api_key=s.openai_api_key))
    return Agent(model, instructions=RULES + instruction, model_settings={"temperature": 0})


def package_text(pkg: ContextPackage) -> str:
    lines = [f"{it.ref} {it.title} | freshness={it.freshness} | " +
             ", ".join(f"{e.source_ref} scope={e.scope} confidence={e.confidence} observed={e.observed_at.date() if e.observed_at else 'unknown'}" for e in it.evidence) +
             f"\n{it.content}" for it in pkg.items]
    if pkg.warnings:
        lines.append("WARNINGS:\n" + "\n".join(f"- {w.kind} {w.refs}: {w.message} Resolution: {w.resolution}" for w in pkg.warnings))
    return "CONTEXT PACKAGE:\n" + ("\n\n".join(lines) or "(the package is empty)")


def extractive(pkg: ContextPackage) -> str:
    # Deterministic fallback without an API key: the first sentence of each item, cited.
    if not pkg.items:
        return "The context package is empty, so this task cannot be answered from available sources."
    lines = [f"- {it.content.split('. ')[0].strip().rstrip('.')}. {it.ref}" for it in pkg.items[:3]]
    lines += [f"- Warning ({w.kind}): {w.message}" for w in pkg.warnings]
    return "\n".join(lines)


def run(instruction: str, db: Session, task: str, principal: Principal, as_of=None) -> dict:
    pkg = resolve(db, ContextRequest(task=task, as_of=as_of), principal)
    if not get_settings().openai_api_key:
        return {"output": extractive(pkg), "package": pkg, "mode": "extractive fallback, no API key"}
    output = agent(instruction).run_sync(f"TASK: {task}\n\n{package_text(pkg)}").output
    return {"output": output, "package": pkg, "mode": "llm"}


def answer(db: Session, question: str, principal: Principal, as_of=None) -> dict:
    return run(ANSWER, db, question, principal, as_of)


def brief(db: Session, topic: str, principal: Principal, as_of=None) -> dict:
    return run(BRIEF, db, f"Write a short brief on: {topic}", principal, as_of)
