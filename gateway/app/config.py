import json
from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenAI. Leave the key empty and the gateway runs lexical-only (no embeddings, no agents).
    openai_api_key: str = ""
    openai_embed_model: str = "text-embedding-3-small"   # 1536 dims, fits a pgvector HNSW index
    openai_llm_model: str = "gpt-4o"
    openai_small_model: str = "gpt-4o-mini"   # reranker and contextual-note model
    rerank_enabled: bool = True     # batched 0-10 scoring of candidates; also the relevance judge
    rerank_min_score: float = 4.0   # candidates scoring below this are dropped
    contextual_enabled: bool = True # per-chunk situating notes (Anthropic contextual retrieval)
    embed_dim: int = 1536

    postgres_user: str = "gateway"
    postgres_password: str = "gateway"
    postgres_db: str = "gateway"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_sslmode: str = "prefer"   # "require" for the managed database

    # API key -> principal. The caller never chooses its own scopes; the key does.
    gateway_keys: str = json.dumps({
        "dev-public": {"agent": "public-agent", "scopes": ["public"]},
        "dev-internal": {"agent": "internal-agent", "scopes": ["public", "internal"]},
        "dev-finance": {"agent": "finance-agent", "scopes": ["public", "internal", "private"]},
    })

    demo_mode: bool = False         # lets the demo page pick an access level without a key
    data_dir: str = "/srv/data"
    retrieval_top_k: int = 30
    max_items: int = 8
    per_doc_cap: int = 2            # chunks from one document
    # Relevance gate used only when the reranker is off: a hit must cover this share of the task's
    # IDF-weighted terms, or rank this high on a semantic channel.
    min_coverage: float = 0.3
    semantic_rank_ok: int = 10
    fresh_days: int = 90
    stale_days: int = 365

    @property
    def database_url(self) -> str:
        user, pw = quote_plus(self.postgres_user), quote_plus(self.postgres_password)
        return f"postgresql+psycopg://{user}:{pw}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}?sslmode={self.postgres_sslmode}"

    @property
    def principals(self) -> dict[str, dict]:
        return json.loads(self.gateway_keys)

    @property
    def channels(self) -> list[str]:
        # Retrieval channels this deployment can serve, in the order the defaults prefer them.
        out = ["lexical"]
        if self.openai_api_key:
            out.append("dense")
            if self.contextual_enabled:
                out += ["lexical_ctx", "dense_ctx"]
        return out

    @property
    def default_channels(self) -> list[str]:
        # Contextual indexes replace the plain ones when available.
        have = set(self.channels)
        chosen = ["lexical_ctx" if "lexical_ctx" in have else "lexical"]
        if "dense_ctx" in have:
            chosen.append("dense_ctx")
        elif "dense" in have:
            chosen.append("dense")
        return chosen


@lru_cache
def get_settings() -> Settings:
    return Settings()
