"""Retrieval: deterministic TF-IDF-style keyword scoring.

No embeddings, no API, no model. Each chunk is scored by the IDF-weighted
overlap between query terms and chunk terms, normalised by chunk length so
long chunks do not win by default. Same corpus + same query = same ranking.
"""
from __future__ import annotations

import math
import re

from orbitronops_rag.models import Chunk, RetrievedChunk

STOPWORDS = frozenset(
    """
    a an the and or but of to in on for with at by from as is are was were be been
    being do does did have has had will would can could should may might i you he
    she it we they this that these those what which who whom whose when where why
    how if then than so such not no yes please tell me about give show list
    """.split()
)

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-]*")


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens, with stopwords removed."""
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]


class Retriever:
    """TF-IDF index over a fixed list of chunks."""

    def __init__(self, chunks: list[Chunk]):
        self.chunks = list(chunks)
        self._doc_freq: dict[str, int] = {}
        self._chunk_terms: list[dict[str, int]] = []
        for chunk in self.chunks:
            terms: dict[str, int] = {}
            for token in set(tokenize(chunk.text)):
                terms[token] = chunk.text.lower().count(token)
                self._doc_freq[token] = self._doc_freq.get(token, 0) + 1
            self._chunk_terms.append(terms)
        self._n = max(len(self.chunks), 1)

    def _idf(self, term: str) -> float:
        # Smoothed IDF: a term in every chunk scores ~0, a rare term scores high.
        return math.log((self._n + 1) / (self._doc_freq.get(term, 0) + 0.5)) + 1.0

    def score(self, query: str, chunk_index: int) -> float:
        """Score one chunk against a query. 0.0 when there is no term overlap."""
        query_terms = tokenize(query)
        if not query_terms:
            return 0.0
        terms = self._chunk_terms[chunk_index]
        chunk_len = sum(terms.values()) or 1
        raw = 0.0
        for term in set(query_terms):
            if term in terms:
                raw += self._idf(term) * terms[term]
        # Length normalisation: sqrt keeps short, focused chunks competitive.
        return raw / math.sqrt(chunk_len)

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
        """Top-k chunks by score, highest first. Empty query -> no results."""
        if not query or not query.strip():
            return []
        scored = [
            RetrievedChunk(chunk=chunk, score=self.score(query, i))
            for i, chunk in enumerate(self.chunks)
        ]
        scored = [r for r in scored if r.score > 0.0]
        scored.sort(key=lambda r: (-r.score, r.chunk.id))
        return scored[: max(top_k, 0)]
