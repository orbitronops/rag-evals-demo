"""Data models for the RAG demo. Plain dataclasses, no dependencies."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Document:
    """One source document in the corpus."""

    source: str  # e.g. "data/runbook-deploy.md"
    title: str
    text: str


@dataclass
class Chunk:
    """One retrievable chunk of a document."""

    id: str  # e.g. "runbook-deploy.md#c2"
    source: str
    title: str
    text: str


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk.id,
            "source": self.chunk.source,
            "title": self.chunk.title,
            "score": round(self.score, 4),
            "text": self.chunk.text,
        }


@dataclass
class Answer:
    """An answer composed only from retrieved chunks — or an abstention."""

    question: str
    text: str
    citations: list[str] = field(default_factory=list)
    retrieved: list[RetrievedChunk] = field(default_factory=list)
    abstained: bool = False
    confidence: float = 0.0  # 0.0–1.0; 0.0 when abstained

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "answer": self.text,
            "citations": self.citations,
            "abstained": self.abstained,
            "confidence": round(self.confidence, 4),
            "retrieved": [r.to_dict() for r in self.retrieved],
        }


@dataclass
class EvalQuestion:
    id: str
    question: str
    expected_source: str = ""  # "" for unanswerable questions
    expected_keywords: list[str] = field(default_factory=list)
    answerable: bool = True


@dataclass
class EvalResult:
    question_id: str
    question: str
    answerable: bool
    abstained: bool
    recall_at_3: float  # 1.0 if expected source in top 3, else 0.0 (n/a: None)
    keyword_accuracy: float | None  # fraction of expected keywords in answer
    retrieved_sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "question_id": self.question_id,
            "question": self.question,
            "answerable": self.answerable,
            "abstained": self.abstained,
            "recall_at_3": self.recall_at_3,
            "keyword_accuracy": self.keyword_accuracy,
            "retrieved_sources": self.retrieved_sources,
        }


@dataclass
class EvalReport:
    total: int
    answerable: int
    unanswerable: int
    retrieval_recall_at_3: float
    mean_keyword_accuracy: float | None
    abstention_rate_unanswerable: float  # share of unanswerable Qs correctly abstained
    false_abstention_rate: float  # share of answerable Qs wrongly abstained
    results: list[EvalResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_questions": self.total,
            "answerable": self.answerable,
            "unanswerable": self.unanswerable,
            "retrieval_recall_at_3": round(self.retrieval_recall_at_3, 4),
            "mean_keyword_accuracy": (
                round(self.mean_keyword_accuracy, 4)
                if self.mean_keyword_accuracy is not None
                else None
            ),
            "abstention_rate_unanswerable": round(
                self.abstention_rate_unanswerable, 4
            ),
            "false_abstention_rate": round(self.false_abstention_rate, 4),
            "results": [r.to_dict() for r in self.results],
        }
