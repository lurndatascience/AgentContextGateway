# LLM reranker: one batched gpt-4o-mini call scores every candidate 0-10 for the task. The score
# orders the package and, with a cutoff, also acts as the relevance judge that drops lexical
# confusers ("Champions League" vs "digitalization champions"). Skipped without an API key.
import logging

from openai import OpenAI
from pydantic import BaseModel, Field

from app.config import get_settings

log = logging.getLogger("rerank")
PROMPT = ("Score each numbered context item from 0 to 10 for how useful it is for the task. "
          "10: directly answers or is the exact subject. 5: clearly related, partial help. "
          "0: unrelated, or only shares words with the task. Score every item.")


class Score(BaseModel):
    index: int
    score: float = Field(ge=0, le=10)


class Scores(BaseModel):
    scores: list[Score]


def rerank(task: str, items: list[tuple[str, str]]) -> dict[int, float]:
    # items: (title, content) in candidate order. Returns index -> score.
    s = get_settings()
    if not items:
        return {}
    body = "\n\n".join(f"[{i}] {title}\n{content[:600]}" for i, (title, content) in enumerate(items))
    resp = OpenAI(api_key=s.openai_api_key).beta.chat.completions.parse(
        model=s.openai_small_model, temperature=0, response_format=Scores,
        messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": f"TASK: {task}\n\n{body}"}])
    parsed = resp.choices[0].message.parsed
    scores = {sc.index: sc.score for sc in parsed.scores} if parsed else {}
    log.info("rerank scored %d of %d", len(scores), len(items))
    return scores
