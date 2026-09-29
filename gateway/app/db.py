# One normalized table. Every source adapter produces rows of this shape.
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import create_engine, func, text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(index=True)
    source_ref: Mapped[str] = mapped_column(unique=True)
    doc_id: Mapped[str] = mapped_column(index=True)
    kind: Mapped[str]                      # structured | unstructured
    title: Mapped[str]
    content: Mapped[str]                   # what retrieval sees and what the agent gets
    context_note: Mapped[str | None]       # LLM situating note (contextual retrieval), retrieval-side only
    fields: Mapped[dict | None] = mapped_column(JSONB)
    fact_key: Mapped[str | None] = mapped_column(index=True)   # "Service revenue|FY 2022"
    fact_value: Mapped[str | None]
    observed_at: Mapped[datetime | None]
    timestamp_precision: Mapped[str]
    ingested_at: Mapped[datetime] = mapped_column(server_default=func.now())
    scope: Mapped[str] = mapped_column(index=True)
    confidence: Mapped[float]
    content_hash: Mapped[str]
    embedding: Mapped[list[float] | None] = mapped_column(Vector(get_settings().embed_dim))          # title + content
    embedding_ctx: Mapped[list[float] | None] = mapped_column(Vector(get_settings().embed_dim))      # title + note + content
    tsv: Mapped[str | None] = mapped_column(TSVECTOR)
    tsv_ctx: Mapped[str | None] = mapped_column(TSVECTOR)


class ContextCache(Base):
    # Situating notes keyed by chunk hash, so re-ingest of unchanged chunks never pays the LLM again.
    __tablename__ = "context_cache"
    chunk_hash: Mapped[str] = mapped_column(primary_key=True)
    note: Mapped[str]
    model: Mapped[str]


INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_items_tsv ON items USING gin (tsv)",
    "CREATE INDEX IF NOT EXISTS ix_items_tsv_ctx ON items USING gin (tsv_ctx)",
    "CREATE INDEX IF NOT EXISTS ix_items_embedding ON items USING hnsw (embedding vector_cosine_ops)",
    "CREATE INDEX IF NOT EXISTS ix_items_embedding_ctx ON items USING hnsw (embedding_ctx vector_cosine_ops)",
]


engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        for stmt in INDEXES:
            conn.execute(text(stmt))


def get_db():
    with SessionLocal() as db:
        yield db
