"""Answer composition: extractive answers, cited, with honest abstention.

The answer is built only from retrieved chunks. It never invents content
beyond them: if no chunk scores above the threshold, the answer is
"I don't know from these documents." The LLM explainer below is a
pluggable interface — optional, off by default, and it may only reword
an answer that already exists; it can never add facts or execute actions.
"""
from __future__ import annotations

import re
from typing import Protocol

from orbitronops_rag.models import Answer, RetrievedChunk
from orbitronops_rag.retrieval import tokenize

ABSTAIN_TEXT = "I don't know from these documents."
DEFAULT_THRESHOLD = 0.5
DEFAULT_TOP_K = 3


class LLMExplainer(Protocol):
    """Optional, bring-your-own-key explainer. Never required, never default.

    Implementations must only reword ``answer.text`` using the cited
    chunks. They must not add facts, change citations, or execute anything.
    """

    def reword(self, answer: Answer) -> str: ...


def _best_sentences(chunk_text: str, query_terms: set[str], max_sentences: int = 2) -> list[str]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", chunk_text) if s.strip()]
    if not sentences:
        return []
    scored = []
    for sentence in sentences:
        hits = sum(1 for term in query_terms if term in sentence.lower())
        scored.append((hits, sentence))
    scored.sort(key=lambda item: (-item[0], item[1]))
    picked = [s for hits, s in scored[:max_sentences] if hits > 0]
    if len(picked) < max_sentences:
        # Fill with the chunk's opening sentence(s) so the answer keeps
        # its context instead of returning a single orphaned sentence.
        for sentence in sentences:
            if len(picked) >= max_sentences:
                break
            if sentence not in picked:
                picked.append(sentence)
    return picked or [scored[0][1]]


def compose_answer(
    question: str,
    retrieved: list[RetrievedChunk],
    threshold: float = DEFAULT_THRESHOLD,
    top_k: int = DEFAULT_TOP_K,
    explainer: LLMExplainer | None = None,
) -> Answer:
    """Compose a cited answer from retrieved chunks, or abstain."""
    if not question or not question.strip():
        return Answer(
            question=question, text=ABSTAIN_TEXT, abstained=True, confidence=0.0
        )
    usable = [r for r in retrieved[:top_k] if r.score >= threshold]
    if not usable:
        return Answer(
            question=question, text=ABSTAIN_TEXT, abstained=True, confidence=0.0
        )

    query_terms = set(tokenize(question))
    parts: list[str] = []
    citations: list[str] = []
    for result in usable:
        for sentence in _best_sentences(result.chunk.text, query_terms):
            parts.append(sentence)
        citations.append(f"{result.chunk.source}#{result.chunk.title}")
    text = " ".join(parts)
    # Confidence is the top retrieval score, capped at 1.0 — a retrieval
    # signal, not a claim that the answer is correct. See docs/EVALS.md.
    confidence = min(usable[0].score / 2.0, 1.0)
    answer = Answer(
        question=question,
        text=text,
        citations=sorted(set(citations)),
        retrieved=usable,
        abstained=False,
        confidence=confidence,
    )
    if explainer is not None:
        answer.text = explainer.reword(answer)
    return answer
