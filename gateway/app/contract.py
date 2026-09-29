# The gateway contract. Every downstream agent talks to the gateway through these types only.
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Scope = Literal["public", "internal", "private"]
Source = Literal["press_release", "record", "financial_fact", "internal_note"]


class Principal(BaseModel):
    agent: str
    scopes: list[Scope]


class ContextRequest(BaseModel):
    task: str = Field(description="What the agent is trying to do, in plain language.")
    budget_tokens: int = Field(1500, ge=100, le=8000)
    as_of: datetime | None = Field(None, description="Freshness reference point. Defaults to now.")
    channels: list[Literal["lexical", "lexical_ctx", "dense", "dense_ctx"]] | None = Field(
        None, description="Retrieval channels to fuse. Defaults to the server's best available set. Mainly for ablation.")
    rerank: bool | None = Field(None, description="Apply the LLM reranker (also the relevance judge). Defaults to on.")


class Evidence(BaseModel):
    source: Source
    source_ref: str = Field(description="Stable pointer into the source, e.g. press_release/62#3")
    doc_id: str
    observed_at: datetime | None
    timestamp_precision: Literal["day", "month", "year", "inferred", "unknown"]
    ingested_at: datetime
    scope: Scope
    confidence: float
    quote: str


class ContextItem(BaseModel):
    ref: str = Field(description="Citation tag the agent must use, e.g. [2]")
    kind: Literal["structured", "unstructured"]
    title: str
    content: str
    fields: dict | None = None
    evidence: list[Evidence]
    freshness: Literal["fresh", "aging", "stale", "unknown"]
    score: float
    why: list[str]


class Warning(BaseModel):
    kind: Literal["stale", "missing", "duplicate", "conflict"]
    message: str
    refs: list[str] = []
    resolution: str | None = None


class ContextPackage(BaseModel):
    task: str
    as_of: datetime
    principal: Principal
    scopes_applied: list[Scope]
    items: list[ContextItem]
    warnings: list[Warning]
    candidates_considered: int
    tokens_used: int
    budget_tokens: int
