# Two downstream agents built with PydanticAI. Each is an instruction on top of the same
# gateway contract: the context package is the agent's only dependency and only knowledge.
from pydantic_ai import Agent, RunContext
from sqlalchemy.orm import Session

from app.config import get_settings
from app.contract import ContextPackage, ContextRequest, Principal
from app.resolve import resolve

RULES = (
    "Work only from the context package. End every factual sentence with the citation tag(s) of the "
    "item(s) it comes from, like [2]. Never use knowledge outside the package. If the package is empty "
    "or does not cover the task, say so plainly. If a warning affects your answer, say how you handled it. "
)
MODEL = f"openai:{get_settings().openai_llm_model}"

answer_agent = Agent(MODEL, deps_type=ContextPackage, instructions=RULES + "Answer the question in at most four sentences.",
                     model_settings={"temperature": 0})
brief_agent = Agent(MODEL, deps_type=ContextPackage, instructions=RULES + "Write a three-bullet brief for an executive, one cited sentence per bullet.",
                    model_settings={"temperature": 0})


@answer_agent.instructions
@brief_agent.instructions
def package_text(ctx: RunContext[ContextPackage]) -> str:
    pkg = ctx.deps
    lines = [f"{it.ref} {it.title} | freshness={it.freshness} | " +
             ", ".join(f"{e.source_ref} scope={e.scope} confidence={e.confidence} observed={e.observed_at.date() if e.observed_at else 'unknown'}" for e in it.evidence) +
             f"\n{it.content}" for it in pkg.items]
    if pkg.warnings:
        lines.append("WARNINGS:\n" + "\n".join(f"- {w.kind} {w.refs}: {w.message} Resolution: {w.resolution}" for w in pkg.warnings))
    return "CONTEXT PACKAGE:\n" + ("\n\n".join(lines) or "(the package is empty)")


def run(agent: Agent, db: Session, task: str, principal: Principal, as_of=None) -> dict:
    if not get_settings().openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set, agents are disabled")
    pkg = resolve(db, ContextRequest(task=task, as_of=as_of), principal)
    return {"output": agent.run_sync(task, deps=pkg).output, "package": pkg}


def answer(db: Session, question: str, principal: Principal, as_of=None) -> dict:
    return run(answer_agent, db, question, principal, as_of)


def brief(db: Session, topic: str, principal: Principal, as_of=None) -> dict:
    return run(brief_agent, db, f"Write a short brief on: {topic}", principal, as_of)
