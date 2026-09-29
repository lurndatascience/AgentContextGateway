# Ingest every source into the items table. Idempotent: unchanged content is skipped,
# changed content is re-embedded and replaced, removed content is deleted. Rows that lack a
# vector for an enabled channel are (re)processed too, so turning on a key back-fills.
# Run with: python -m app.ingest
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict

from openai import OpenAI
from sqlalchemy import delete, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import ContextCache, Item, SessionLocal, init_db
from app.sources import RawItem, all_items

log = logging.getLogger("ingest")
CONTEXT_PROMPT = ("Given the full document and one chunk from it, write 1-2 short sentences naming the speaker or "
                  "source (if quoted), the topic in the document's context, and the time period (if relevant). "
                  "Do not paraphrase the chunk or add facts not in the document. Output only the note.")


def find_changed(db: Session, raw: list[RawItem]) -> tuple[list[RawItem], set[str]]:
    # Changed content, plus rows missing a vector that the current keys can now produce.
    s = get_settings()
    known = dict(db.execute(select(Item.source_ref, Item.content_hash)).all())
    missing: set[str] = set()
    if s.openai_api_key:
        missing |= set(db.scalars(select(Item.source_ref).where(Item.embedding.is_(None))))
        if s.contextual_enabled:
            missing |= set(db.scalars(select(Item.source_ref).where(Item.embedding_ctx.is_(None))))
    changed = [r for r in raw if known.get(r.source_ref) != r.content_hash or r.source_ref in missing]
    removed = set(known) - {r.source_ref for r in raw}
    return changed, removed


def contextualize(db: Session, items: list[RawItem]) -> dict[str, str]:
    # Situating note per press-release chunk (Anthropic contextual retrieval), cached by chunk hash.
    s = get_settings()
    targets = [i for i in items if i.doc_text]
    if not (s.openai_api_key and s.contextual_enabled and targets):
        return {}
    notes = dict(db.execute(select(ContextCache.chunk_hash, ContextCache.note)
                            .where(ContextCache.chunk_hash.in_([i.content_hash for i in targets]))).all())
    client = OpenAI(api_key=s.openai_api_key)

    def write_note(i: RawItem) -> tuple[str, str]:
        resp = client.chat.completions.create(model=s.openai_small_model, temperature=0, max_tokens=120, messages=[
            {"role": "system", "content": CONTEXT_PROMPT},
            {"role": "user", "content": f"<document>\n{i.doc_text[:14000]}\n</document>\n\n<chunk>\n{i.content}\n</chunk>"}])
        return i.content_hash, (resp.choices[0].message.content or "").strip()

    with ThreadPoolExecutor(8) as pool:
        fresh = dict(pool.map(write_note, [i for i in targets if i.content_hash not in notes]))
    for h, n in fresh.items():
        db.execute(insert(ContextCache).values(chunk_hash=h, note=n, model=s.openai_small_model).on_conflict_do_nothing())
    log.info("context notes: %d cached, %d written", len(notes), len(fresh))
    notes.update(fresh)
    return {i.source_ref: notes[i.content_hash] for i in targets}


def embed(texts: list[str]) -> list[list[float] | None]:
    s = get_settings()
    if not s.openai_api_key:
        return [None] * len(texts)
    client, out = OpenAI(api_key=s.openai_api_key), []
    for start in range(0, len(texts), 128):
        out += [d.embedding for d in client.embeddings.create(model=s.openai_embed_model, input=texts[start:start + 128]).data]
    return out


def upsert(db: Session, items: list[RawItem], notes: dict[str, str]) -> None:
    plain = embed([f"{i.title}\n{i.content}" for i in items])
    noted = [i for i in items if i.source_ref in notes]
    ctx = dict(zip([i.source_ref for i in noted], embed([f"{i.title}\n{notes[i.source_ref]}\n{i.content}" for i in noted])))
    for item, vec in zip(items, plain):
        row = {k: v for k, v in asdict(item).items() if k != "doc_text"}
        row.update(context_note=notes.get(item.source_ref), embedding=vec,
                   embedding_ctx=ctx.get(item.source_ref, vec))     # items without a note share the plain vector
        db.execute(insert(Item).values(**row).on_conflict_do_update(index_elements=["source_ref"], set_={**row, "ingested_at": text("now()")}))
    db.execute(text("UPDATE items SET tsv = to_tsvector('english', title || ' ' || content), "
                    "tsv_ctx = to_tsvector('english', title || ' ' || coalesce(context_note, '') || ' ' || content) "
                    "WHERE tsv IS NULL OR tsv_ctx IS NULL OR source_ref = ANY(:refs)"),
               {"refs": [i.source_ref for i in items]})


def run() -> dict:
    init_db()
    raw = all_items(get_settings().data_dir)
    with SessionLocal() as db:
        changed, removed = find_changed(db, raw)
        notes = contextualize(db, changed)
        upsert(db, changed, notes)
        if removed:
            db.execute(delete(Item).where(Item.source_ref.in_(removed)))
        db.commit()
    summary = {"total": len(raw), "changed": len(changed), "removed": len(removed), "notes": len(notes)}
    log.info("ingest done %s", summary)
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    print(run())
